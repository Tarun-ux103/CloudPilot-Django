from django.test import TestCase
from django.urls import reverse
from .models import Alert, MetricSnapshot, Server
from .search_algorithms import astar_vm_search, best_first_vm_search, path_between_vm_sizes


class CloudPilotBasicTests(TestCase):
    def setUp(self):
        self.server = Server.objects.create(
            name='test-server', region='Local Simulator', vm_type='medium',
            vcpu=4, ram_gb=8, storage_gb=80, hourly_rate=0.24,
        )
        self.metric = MetricSnapshot.objects.create(
            server=self.server, cpu_utilization=50, memory_utilization=52,
            disk_utilization=40, network_mbps=60, requests_per_second=400,
        )

    def test_dashboard_loads(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cloud resource overview')
        self.assertContains(response, 'test-server')

    def test_server_detail_loads(self):
        response = self.client.get(reverse('server_detail', args=[self.server.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test-server')

    def test_optimizer_creates_recommendation(self):
        response = self.client.post(reverse('optimize_server', args=[self.server.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.server.recommendations.count(), 1)

    def test_high_metric_creates_alert(self):
        response = self.client.post(reverse('add_metric', args=[self.server.id]), {
            'cpu_utilization': 96, 'memory_utilization': 60,
            'disk_utilization': 40, 'network_mbps': 80, 'requests_per_second': 900,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Alert.objects.filter(server=self.server, level='critical').exists())

    def test_add_server_page_loads(self):
        response = self.client.get(reverse('add_server'))
        self.assertEqual(response.status_code, 200)


class ResourceSearchTests(TestCase):
    def test_astar_selects_smallest_feasible_vm(self):
        result = astar_vm_search(required_vcpu=3.0, required_ram=6.0)
        self.assertEqual(result['target'], 'medium')
        self.assertTrue(result['feasible'])

    def test_best_first_finds_feasible_vm(self):
        result = best_first_vm_search(required_vcpu=6.0, required_ram=12.0)
        self.assertEqual(result['target'], 'large')
        self.assertTrue(result['feasible'])

    def test_no_vm_meets_extreme_demand(self):
        result = astar_vm_search(required_vcpu=12.0, required_ram=24.0)
        self.assertEqual(result['target'], 'large')
        self.assertFalse(result['feasible'])

    def test_vm_resize_path(self):
        self.assertEqual(path_between_vm_sizes('small', 'large'), ['small', 'medium', 'large'])
