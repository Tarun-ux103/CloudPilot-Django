from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from monitoring.ml import train_all

class Command(BaseCommand):
    help = 'Train CloudPilot workload prediction, scaling and anomaly models.'

    def handle(self, *args, **options):
        try:
            metrics = train_all(settings.CLOUDPILOT_DATASET, settings.CLOUDPILOT_MODEL_DIR)
        except Exception as exc:
            raise CommandError(f'Model training failed: {exc}') from exc
        self.stdout.write(self.style.SUCCESS('CloudPilot models trained successfully.'))
        self.stdout.write(f"Training rows: {metrics['rows']}")
        self.stdout.write(f"CPU MAE: {metrics['cpu_mae']} | Memory MAE: {metrics['memory_mae']} | Action accuracy: {metrics['action_accuracy']}")
