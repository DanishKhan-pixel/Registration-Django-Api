from django.db import models
from utils.models import BaseModel
# Create your models here.


class Permission(BaseModel):
    name = models.CharField(max_length=255)
    codename = models.CharField(max_length=255, unique=True)
    model = models.CharField(max_length=255)

    class Meta:
        db_table = 'permissions'

    def __str__(self):
        return self.codename


class Role(BaseModel):
    name = models.CharField(max_length=255)

    description = models.TextField()
    status = models.BooleanField(default=True)
    permissions = models.ManyToManyField(Permission, blank=True)

    class Meta:
        db_table = 'roles'


    def __str__(self):
        return self.name


