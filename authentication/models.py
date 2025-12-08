from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from role.models import Role
from utils.models import BaseModel
from .choices import GENDER_CHOICES, TYPE_CHOICES, TOKEN_TYPE_CHOICES, MEDIA_TYPES_CHOICES
from utils.validators import validate_username, validate_email, validate_password, validate_file_size, validate_positive_value
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
# Create your models here.


class User(AbstractUser, BaseModel):
    email = models.EmailField(unique=True, verbose_name="Email Address", max_length=255, validators=[validate_email])
    username = models.CharField(max_length=30, unique=True, verbose_name="Username",
                                validators=[validate_username])
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_roles', null=True, blank=True)
    gender = models.CharField(choices=GENDER_CHOICES, max_length=10, null=True, blank=True)
    contact = models.CharField(max_length=120, null=True, blank=True, unique=True)
    country_code = models.CharField(max_length=10, null=True, blank=True, default="+1")

    objects = UserManager()

    class Meta:
        db_table = 'users'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def clean(self):
        """ Validate password before saving """
        if self.password:
            validate_password(self.password)

    def save(self, *args, **kwargs):
        """ Ensure password is hashed before saving """
        if self.pk is None or not self.password.startswith('pbkdf2_sha256$'):
            self.set_password(self.password)  # Hash password properly
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email


class Media(BaseModel):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    media_type = models.CharField(choices=MEDIA_TYPES_CHOICES, max_length=15)
    file = models.FileField(upload_to='uploads/', validators=[validate_file_size])

    class Meta:
        db_table = 'media'

    def __str__(self):
        return f"{self.content_type} - {self.object_id}"


class Profile(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)


    class Meta:
        db_table = 'user_profiles'

    def __str__(self):
        return self.user.username


class Token(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    type = models.CharField(choices=TOKEN_TYPE_CHOICES, max_length=100, null=True, blank=True)
    code = models.CharField(max_length=100, null=True, blank=True, unique=True)
    expires = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'tokens'

    def __str__(self):
        return self.user.username


class LoginHistory(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history')
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    type = models.CharField(choices=TYPE_CHOICES, max_length=100, null=True, blank=True)

    class Meta:
        db_table = 'login_history'

    def __str__(self):
        return self.user.username
