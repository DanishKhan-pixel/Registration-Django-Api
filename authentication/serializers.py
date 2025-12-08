from unittest import result
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from authentication.models import User, Profile, LoginHistory
from authentication.models import Media
from django.contrib.contenttypes.models import ContentType
from .models import Token
from utils.helpers import EXCLUDED_FIELDS
from urllib.parse import urljoin
from django.conf import settings
import re


class UserSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False)
    organization = serializers.SerializerMethodField()
    role_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        exclude = EXCLUDED_FIELDS + ["groups", "user_permissions", "last_login", "is_staff", "date_joined"]
        read_only_fields = ('is_superuser',)
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'email': {
                'required': True,
                'validators': [UniqueValidator(queryset=User.objects.all(), message='Email Address already exists.')]
            },
            'username': {
                'required': True,
                'validators': [UniqueValidator(queryset=User.objects.all(), message='Username already exists.')]
            },
            'contact': {
                'required': False,
                'allow_blank': True,
                'validators': [UniqueValidator(queryset=User.objects.all(), message='Contact already exists.')]
            },
            'country_code': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate_contact(self, value):
        """Validate phone number format."""
        # Check if value is empty, None, or only whitespace
        if not value or (isinstance(value, str) and value.strip() == ""):
            raise serializers.ValidationError("This field may not be blank.")
        
        # Remove any spaces, dashes, or other separators
        cleaned_value = re.sub(r'[\s\-\(\)]', '', str(value))
        
        # Check if it contains only numbers
        if not re.match(r'^[0-9]+$', cleaned_value):
            raise serializers.ValidationError("Contact must contain only numbers.")
        
        # Validate phone number length (exactly 9 digits)
        if len(cleaned_value) != 9:
            raise serializers.ValidationError("Phone number must be 9 digits.")
        
        return cleaned_value

    def validate_country_code(self, value):
        """Validate country code format."""
        # Country code must not be empty
        if value is None or (isinstance(value, str) and value.strip() == ""):
            raise serializers.ValidationError("Country code is required.")

        # Ensure country code starts with +
        if not value.startswith('+'):
            value = '+' + value
        
        # Validate format (e.g., +966, +1, +44)
        if not re.match(r'^\+\d{1,4}$', value):
            raise serializers.ValidationError("Country code must be in format +XXX (e.g., +966, +1).")
        
        return value

    def create(self, validated_data):
        """Ensure password is hashed before saving a new user."""
        password = validated_data.pop('password', None)
        image = validated_data.pop("image", None)

        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()

        # Handle image separately
        if image:
            Media.objects.update_or_create(
                content_type=ContentType.objects.get_for_model(User),
                object_id=user.id,
                defaults={"file": image}
            )

        return user

    def validate_first_name(self, value):
        """Ensure first name is not blank or whitespace only."""
        if value is None or (isinstance(value, str) and value.strip() == ""):
            raise serializers.ValidationError("This field may not be blank.")
        return value

    def validate_last_name(self, value):
        """Ensure last name is not blank or whitespace only."""
        if value is None or (isinstance(value, str) and value.strip() == ""):
            raise serializers.ValidationError("This field may not be blank.")
        return value

    def update(self, instance, validated_data):
        """Ensure password is hashed and image is updated correctly."""
        password = validated_data.pop('password', None)
        image = validated_data.pop("image", None)

        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()

        # Handle image update separately
        if image:
            Media.objects.update_or_create(
                content_type=ContentType.objects.get_for_model(User),
                object_id=user.id,
                defaults={"file": image}
            )

        return user

    def get_organization(self, obj):
        """Return organization ID from Profile"""
        profile = Profile.objects.filter(user=obj).first()
        return profile.organization.id if profile and profile.organization else None

    def get_role_name(self, obj):
        return obj.role.name if obj.role else None

    def to_representation(self, instance):
        data = super().to_representation(instance)

        data['gender'] = instance.get_gender_display() if instance.gender else None

        media = Media.objects.filter(
            content_type=ContentType.objects.get_for_model(User),
            object_id=instance.id
        ).first()

        data["image"] = urljoin(settings.BASE_URL, media.file.url) if media else None

        return data


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        exclude = EXCLUDED_FIELDS


class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        exclude = EXCLUDED_FIELDS


class LoginHistorySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = LoginHistory
        exclude = EXCLUDED_FIELDS

    def get_name(self, obj):
        return obj.user.full_name

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['type'] = instance.get_type_display() if instance.type is not None else None
        return representation



class TokensSerializer(serializers.Serializer):
    access_token = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)

class LoginSerializer(serializers.Serializer):
    tokens = TokensSerializer(read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)
    token_type = serializers.CharField(read_only=True)
    role = serializers.CharField(allow_blank=True, allow_null=True, required=False, read_only=True)
    organization = serializers.IntegerField(allow_null=True, required=False, read_only=True)

class LoginRequestSerializer(serializers.Serializer):
    identifier = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)



class LoginResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    results = LoginSerializer()


class LogoutResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()


class ResetPasswordRequestSerializer(serializers.Serializer):
    code = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)



class ForgotPasswordRequestSerializer(serializers.Serializer):
    identifier = serializers.CharField(write_only=True)


class ForgotPasswordResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
