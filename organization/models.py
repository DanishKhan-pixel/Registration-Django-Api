from django.db import models
from utils.models import BaseModel




class Country(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)

    class Meta:
        db_table = 'countries'


class Organization(BaseModel):
   user = models.OneToOneField('authentication.User', on_delete=models.CASCADE, related_name="organizations")
   name = models.CharField(max_length=255)
   contact = models.CharField(max_length=255, unique=True)
   country = models.CharField(max_length=120, null=True, blank=True)
   address = models.TextField()
   status = models.BooleanField(default=True)
   ip = models.GenericIPAddressField(unique=True, protocol="both", null=True, blank=True)
   ssh_key = models.TextField(unique=True, null=True, blank=True)
   validation_frequency = models.IntegerField(null=True, blank=True)
   api_key = models.TextField(null=True, blank=True, unique=True)
   secret_key = models.TextField(null=True, blank=True, unique=True)

   class Meta:
       db_table = "organizations"

   def __str__(self):
       return self.name
