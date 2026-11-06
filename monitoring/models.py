from django.db import models
from django.utils import timezone


class Server(models.Model):
    VM_CHOICES = [('small', 'Small · 2 vCPU / 4 GB'), ('medium', 'Medium · 4 vCPU / 8 GB'), ('large', 'Large · 8 vCPU / 16 GB')]
    STATUS_CHOICES = [('running', 'Running'), ('stopped', 'Stopped')]

    name = models.CharField(max_length=100, unique=True)
    region = models.CharField(max_length=80, default='Local Simulator')
    vm_type = models.CharField(max_length=12, choices=VM_CHOICES, default='medium')
    vcpu = models.PositiveSmallIntegerField(default=4)
    ram_gb = models.PositiveSmallIntegerField(default=8)
    storage_gb = models.PositiveSmallIntegerField(default=80)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=4, default=0.2400)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='running')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.get_vm_type_display()})'


class MetricSnapshot(models.Model):
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name='metrics')
    recorded_at = models.DateTimeField(default=timezone.now)
    cpu_utilization = models.FloatField()
    memory_utilization = models.FloatField()
    disk_utilization = models.FloatField(default=30)
    network_mbps = models.FloatField(default=50)
    requests_per_second = models.FloatField(default=300)

    class Meta:
        ordering = ['-recorded_at']

    def __str__(self):
        return f'{self.server.name} · {self.recorded_at:%Y-%m-%d %H:%M}'


class Recommendation(models.Model):
    ACTION_CHOICES = [('scale_up', 'Scale up'), ('scale_down', 'Scale down'), ('maintain', 'Maintain')]
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name='recommendations')
    created_at = models.DateTimeField(auto_now_add=True)
    predicted_cpu = models.FloatField()
    predicted_memory = models.FloatField()
    action = models.CharField(max_length=12, choices=ACTION_CHOICES)
    recommended_vm = models.CharField(max_length=12)
    current_monthly_cost = models.FloatField()
    recommended_monthly_cost = models.FloatField()
    estimated_monthly_savings = models.FloatField()
    anomaly_detected = models.BooleanField(default=False)
    note = models.CharField(max_length=240, blank=True)

    class Meta:
        ordering = ['-created_at']


class Alert(models.Model):
    LEVEL_CHOICES = [('info', 'Info'), ('warning', 'Warning'), ('critical', 'Critical')]
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name='alerts')
    created_at = models.DateTimeField(auto_now_add=True)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='warning')
    message = models.CharField(max_length=255)
    resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.level.upper()}: {self.server.name}'
