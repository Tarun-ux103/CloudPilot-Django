from django import forms
from .models import Server, MetricSnapshot

VM_PRICING = {
    'small': {'vcpu': 2, 'ram_gb': 4, 'hourly_rate': 0.12},
    'medium': {'vcpu': 4, 'ram_gb': 8, 'hourly_rate': 0.24},
    'large': {'vcpu': 8, 'ram_gb': 16, 'hourly_rate': 0.48},
}


class ServerForm(forms.ModelForm):
    class Meta:
        model = Server
        fields = ['name', 'region', 'vm_type', 'storage_gb']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. api-server-04'}),
            'region': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Local Simulator'}),
            'vm_type': forms.Select(attrs={'class': 'form-control'}),
            'storage_gb': forms.NumberInput(attrs={'class': 'form-control', 'min': 20, 'max': 2000}),
        }

    def save(self, commit=True):
        server = super().save(commit=False)
        plan = VM_PRICING[server.vm_type]
        server.vcpu = plan['vcpu']
        server.ram_gb = plan['ram_gb']
        server.hourly_rate = plan['hourly_rate']
        if commit:
            server.save()
        return server


class MetricForm(forms.ModelForm):
    class Meta:
        model = MetricSnapshot
        fields = ['cpu_utilization', 'memory_utilization', 'disk_utilization', 'network_mbps', 'requests_per_second']
        widgets = {
            'cpu_utilization': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'step': '0.1'}),
            'memory_utilization': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'step': '0.1'}),
            'disk_utilization': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'step': '0.1'}),
            'network_mbps': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': '0.1'}),
            'requests_per_second': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': '0.1'}),
        }

    def clean(self):
        cleaned = super().clean()
        for field in ['cpu_utilization', 'memory_utilization', 'disk_utilization']:
            value = cleaned.get(field)
            if value is not None and not 0 <= value <= 100:
                self.add_error(field, 'Enter a value between 0 and 100.')
        for field in ['network_mbps', 'requests_per_second']:
            value = cleaned.get(field)
            if value is not None and value < 0:
                self.add_error(field, 'Value cannot be negative.')
        return cleaned
