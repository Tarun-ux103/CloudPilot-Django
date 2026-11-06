from django.contrib import admin
from .models import Alert, MetricSnapshot, Recommendation, Server

@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'vm_type', 'vcpu', 'ram_gb', 'status')
    search_fields = ('name', 'region')
    list_filter = ('vm_type', 'status')

@admin.register(MetricSnapshot)
class MetricSnapshotAdmin(admin.ModelAdmin):
    list_display = ('server', 'recorded_at', 'cpu_utilization', 'memory_utilization', 'disk_utilization')
    list_filter = ('server',)

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('server', 'created_at', 'action', 'recommended_vm', 'estimated_monthly_savings')

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('server', 'created_at', 'level', 'resolved')
    list_filter = ('level', 'resolved')
