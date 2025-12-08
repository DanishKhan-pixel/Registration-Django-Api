from django.core.management.base import BaseCommand
from django.utils.timezone import now
from datetime import timedelta
from utils.models import BaseModel
from django.conf import settings

class Command(BaseCommand):
    help = "Permanently delete soft-deleted records older than 2 months"

    def handle(self, *args, **kwargs):
        # Calculate the date 2 months ago
        threshold_date = now() - timedelta(days=settings.HARD_DELETE_OLD_DATA_DAYS)

        # Get all models that inherit from BaseModel
        for model in BaseModel.__subclasses__():
            deleted_records = model.objects.filter(is_deleted=True, deleted_at__lte=threshold_date)
            count = deleted_records.count()
            deleted_records.delete()
            self.stdout.write(self.style.SUCCESS(f"Deleted {count} records from {model.__name__}"))
