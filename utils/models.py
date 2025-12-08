from django.db import models
from django.utils.timezone import now


class BaseModelManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    status = models.BooleanField(default=True)

    objects = BaseModelManager()

    class Meta:
        abstract = True

    def soft_delete(self):
        """Marks the object as deleted."""
        self.is_deleted = True
        self.deleted_at = now()
        self.status = False
        self.save(update_fields=["is_deleted", "deleted_at", "status"])

    def restore(self):
        """Restores the soft-deleted object."""
        self.is_deleted = False
        self.deleted_at = None
        self.status = True
        self.save(update_fields=["is_deleted", "deleted_at", "status"])

    def deactivate(self):
        self.status = False
        self.save(update_fields=["status"])

    def activate(self):
        self.status = True
        self.save(update_fields=["status"])

    @classmethod
    def trash(cls):
        """Returns only soft-deleted objects."""
        return cls.objects.filter(is_deleted=True)
