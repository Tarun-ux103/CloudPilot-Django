from django.contrib import admin
from django.urls import path
from monitoring import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard, name='dashboard'),
    path('servers/add/', views.add_server, name='add_server'),
    path('servers/<int:server_id>/', views.server_detail, name='server_detail'),
    path('servers/<int:server_id>/metric/', views.add_metric, name='add_metric'),
    path('servers/<int:server_id>/optimize/', views.optimize_server_view, name='optimize_server'),
    path('alerts/<int:alert_id>/resolve/', views.resolve_alert, name='resolve_alert'),
    path('models/', views.model_status, name='model_status'),
]
