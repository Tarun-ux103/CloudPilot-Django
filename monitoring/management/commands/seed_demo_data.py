from datetime import timedelta
import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from monitoring.models import MetricSnapshot, Server

PLANS = {
    'small': {'vcpu': 2, 'ram_gb': 4, 'rate': 0.12},
    'medium': {'vcpu': 4, 'ram_gb': 8, 'rate': 0.24},
    'large': {'vcpu': 8, 'ram_gb': 16, 'rate': 0.48},
}

class Command(BaseCommand):
    help = 'Create sample servers and local workload readings.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Delete existing demo servers before seeding.')

    def handle(self, *args, **options):
        rng = random.Random(21)
        if options['reset']:
            Server.objects.all().delete()
        configurations = [
            ('web-frontend-01', 'Local Simulator', 'medium', 48, 52),
            ('api-worker-01', 'Local Simulator', 'large', 72, 68),
            ('batch-job-01', 'Local Simulator', 'small', 18, 27),
        ]
        created = 0
        now = timezone.now()
        for name, region, vm_type, base_cpu, base_memory in configurations:
            plan = PLANS[vm_type]
            server, was_created = Server.objects.get_or_create(name=name, defaults={
                'region': region, 'vm_type': vm_type, 'vcpu': plan['vcpu'], 'ram_gb': plan['ram_gb'],
                'storage_gb': 80, 'hourly_rate': plan['rate'], 'status': 'running'
            })
            if not was_created and server.metrics.exists():
                continue
            if not was_created:
                server.vm_type, server.vcpu, server.ram_gb = vm_type, plan['vcpu'], plan['ram_gb']
                server.hourly_rate = plan['rate']
                server.save()
            created += 1
            for index in range(18):
                trend = (index - 8) * rng.uniform(-1.0, 1.7)
                cpu = max(5, min(98, base_cpu + trend + rng.uniform(-12, 12)))
                memory = max(8, min(97, base_memory + trend * 0.6 + rng.uniform(-10, 10)))
                MetricSnapshot.objects.create(
                    server=server,
                    recorded_at=now - timedelta(minutes=(17 - index) * 20),
                    cpu_utilization=round(cpu, 1),
                    memory_utilization=round(memory, 1),
                    disk_utilization=round(max(8, min(95, 25 + index * 1.3 + rng.uniform(-8, 8))), 1),
                    network_mbps=round(max(5, 30 + cpu * 1.1 + rng.uniform(-20, 25)), 1),
                    requests_per_second=round(max(5, 100 + cpu * 10 + rng.uniform(-80, 120)), 1),
                )
        self.stdout.write(self.style.SUCCESS(f'Demo data ready. New demo servers: {created}.'))
