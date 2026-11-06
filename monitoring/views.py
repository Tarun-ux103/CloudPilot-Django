import json
from pathlib import Path
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .forms import MetricForm, ServerForm
from .ml import make_prediction
from .models import Alert, MetricSnapshot, Recommendation, Server


def dashboard(request):
    servers = list(Server.objects.all())
    latest_metrics = {server.id: server.metrics.first() for server in servers}
    total_cpu = [item.cpu_utilization for item in latest_metrics.values() if item]
    total_memory = [item.memory_utilization for item in latest_metrics.values() if item]
    open_alerts = Alert.objects.filter(resolved=False).select_related('server')[:6]
    recent_recommendations = Recommendation.objects.select_related('server')[:5]
    chart_labels, chart_cpu, chart_memory = [], [], []
    if servers:
        first_server = servers[0]
        points = list(first_server.metrics.order_by('-recorded_at')[:12])[::-1]
        chart_labels = [point.recorded_at.strftime('%H:%M') for point in points]
        chart_cpu = [round(point.cpu_utilization, 1) for point in points]
        chart_memory = [round(point.memory_utilization, 1) for point in points]
    context = {
        'servers': servers,
        'latest_metrics': latest_metrics,
        'server_count': len(servers),
        'running_count': sum(1 for server in servers if server.status == 'running'),
        'avg_cpu': round(sum(total_cpu) / len(total_cpu), 1) if total_cpu else 0,
        'avg_memory': round(sum(total_memory) / len(total_memory), 1) if total_memory else 0,
        'open_alerts': open_alerts,
        'open_alert_count': Alert.objects.filter(resolved=False).count(),
        'recent_recommendations': recent_recommendations,
        'chart_labels': json.dumps(chart_labels),
        'chart_cpu': json.dumps(chart_cpu),
        'chart_memory': json.dumps(chart_memory),
        'metric_form': MetricForm(),
    }
    return render(request, 'monitoring/dashboard.html', context)


def add_server(request):
    if request.method == 'POST':
        form = ServerForm(request.POST)
        if form.is_valid():
            server = form.save()
            messages.success(request, f'{server.name} was added to the simulator.')
            return redirect('dashboard')
    else:
        form = ServerForm()
    return render(request, 'monitoring/server_form.html', {'form': form})


def add_metric(request, server_id):
    server = get_object_or_404(Server, pk=server_id)
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    form = MetricForm(request.POST)
    if form.is_valid():
        metric = form.save(commit=False)
        metric.server = server
        metric.save()
        messages.success(request, f'New workload reading saved for {server.name}.')
        if metric.cpu_utilization >= 90 or metric.memory_utilization >= 90 or metric.disk_utilization >= 95:
            Alert.objects.create(server=server, level='critical', message='A resource utilization metric crossed the critical threshold. Review the latest workload reading.')
        elif metric.cpu_utilization >= 80 or metric.memory_utilization >= 85:
            Alert.objects.create(server=server, level='warning', message='High resource utilization was recorded. Run an optimization check.')
    else:
        messages.error(request, 'Please check the workload values. CPU, memory and disk must be between 0 and 100.')
    return redirect('dashboard')


@require_POST
def optimize_server_view(request, server_id):
    server = get_object_or_404(Server, pk=server_id)
    metric = server.metrics.first()
    if not metric:
        messages.error(request, 'Add a workload reading before running optimization.')
        return redirect('dashboard')
    result = make_prediction(metric, settings.CLOUDPILOT_MODEL_DIR)
    recommendation = Recommendation.objects.create(server=server, **{key: result[key] for key in [
        'predicted_cpu', 'predicted_memory', 'action', 'recommended_vm', 'current_monthly_cost',
        'recommended_monthly_cost', 'estimated_monthly_savings', 'anomaly_detected', 'note'
    ]})
    if result['anomaly_detected'] or result['predicted_cpu'] >= 85 or result['predicted_memory'] >= 85:
        level = 'critical' if result['predicted_cpu'] >= 95 or result['predicted_memory'] >= 95 else 'warning'
        Alert.objects.create(server=server, level=level, message=f"Optimization check: forecast CPU {result['predicted_cpu']}%, memory {result['predicted_memory']}%. {result['note']}")
    messages.success(request, f'Optimization completed for {server.name}. Recommended action: {recommendation.get_action_display()}.')
    return redirect('server_detail', server_id=server.id)


def server_detail(request, server_id):
    server = get_object_or_404(Server, pk=server_id)
    metrics = list(server.metrics.all()[:30])[::-1]
    context = {
        'server': server,
        'monthly_cost': round(float(server.hourly_rate) * 730, 2),
        'metrics': metrics,
        'recommendations': server.recommendations.all()[:10],
        'alerts': server.alerts.all()[:10],
        'metric_form': MetricForm(),
        'chart_labels': json.dumps([m.recorded_at.strftime('%d %b %H:%M') for m in metrics]),
        'chart_cpu': json.dumps([round(m.cpu_utilization, 1) for m in metrics]),
        'chart_memory': json.dumps([round(m.memory_utilization, 1) for m in metrics]),
    }
    return render(request, 'monitoring/server_detail.html', context)


@require_POST
def resolve_alert(request, alert_id):
    alert = get_object_or_404(Alert, pk=alert_id)
    alert.resolved = True
    alert.save(update_fields=['resolved'])
    messages.success(request, 'Alert marked as resolved.')
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


def model_status(request):
    metrics_file = Path(settings.CLOUDPILOT_MODEL_DIR) / 'training_metrics.json'
    model_files = ['cpu_regressor.joblib', 'memory_regressor.joblib', 'scaling_classifier.joblib', 'anomaly_detector.joblib']
    trained = all((Path(settings.CLOUDPILOT_MODEL_DIR) / file).exists() for file in model_files)
    metrics = json.loads(metrics_file.read_text(encoding='utf-8')) if metrics_file.exists() else None
    if metrics:
        metrics['action_accuracy_pct'] = round(metrics['action_accuracy'] * 100, 1)
    return render(request, 'monitoring/model_status.html', {'trained': trained, 'metrics': metrics, 'model_files': model_files})
