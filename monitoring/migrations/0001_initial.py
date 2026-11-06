import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='Server',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('region', models.CharField(default='Local Simulator', max_length=80)),
                ('vm_type', models.CharField(choices=[('small', 'Small · 2 vCPU / 4 GB'), ('medium', 'Medium · 4 vCPU / 8 GB'), ('large', 'Large · 8 vCPU / 16 GB')], default='medium', max_length=12)),
                ('vcpu', models.PositiveSmallIntegerField(default=4)),
                ('ram_gb', models.PositiveSmallIntegerField(default=8)),
                ('storage_gb', models.PositiveSmallIntegerField(default=80)),
                ('hourly_rate', models.DecimalField(decimal_places=4, default=0.24, max_digits=8)),
                ('status', models.CharField(choices=[('running', 'Running'), ('stopped', 'Stopped')], default='running', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='MetricSnapshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recorded_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('cpu_utilization', models.FloatField()),
                ('memory_utilization', models.FloatField()),
                ('disk_utilization', models.FloatField(default=30)),
                ('network_mbps', models.FloatField(default=50)),
                ('requests_per_second', models.FloatField(default=300)),
                ('server', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='metrics', to='monitoring.server')),
            ],
            options={'ordering': ['-recorded_at']},
        ),
        migrations.CreateModel(
            name='Recommendation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('predicted_cpu', models.FloatField()),
                ('predicted_memory', models.FloatField()),
                ('action', models.CharField(choices=[('scale_up', 'Scale up'), ('scale_down', 'Scale down'), ('maintain', 'Maintain')], max_length=12)),
                ('recommended_vm', models.CharField(max_length=12)),
                ('current_monthly_cost', models.FloatField()),
                ('recommended_monthly_cost', models.FloatField()),
                ('estimated_monthly_savings', models.FloatField()),
                ('anomaly_detected', models.BooleanField(default=False)),
                ('note', models.CharField(blank=True, max_length=240)),
                ('server', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recommendations', to='monitoring.server')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='Alert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('level', models.CharField(choices=[('info', 'Info'), ('warning', 'Warning'), ('critical', 'Critical')], default='warning', max_length=10)),
                ('message', models.CharField(max_length=255)),
                ('resolved', models.BooleanField(default=False)),
                ('server', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alerts', to='monitoring.server')),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
