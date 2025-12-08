from rest_framework import serializers, viewsets
import organization
from .models import Organization
from utils.helpers import EXCLUDED_FIELDS
from authentication.serializers import UserSerializer
from utils.microservices.subscriptions import get_active_subscriptions
from django.core.validators import validate_ipv46_address
from django.core.exceptions import ValidationError as DjangoValidationError
from authentication.serializers import UserSerializer


class OrganizationSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    plan = serializers.CharField(read_only=True, required=False)
    expiry_date = serializers.DateTimeField(read_only=True, required=False)
    payment_method = serializers.CharField(read_only=True, required=False)
    
    class Meta:
        model = Organization
        exclude = EXCLUDED_FIELDS

    def validate_ip(self, value):
        # Allow None or empty string to pass through
        if value in (None, ""):
            return None
        try:
            validate_ipv46_address(value)
        except DjangoValidationError:
            raise serializers.ValidationError("Enter a valid IPv4 or IPv6 address.")
        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        # Get subscription details for this organization
        subscriptions = get_active_subscriptions([instance.id])
        
        if instance.id in subscriptions:
            subscription = subscriptions[instance.id]
            data['plan'] = subscription.get('plan_name')
            data['expiry_date'] = subscription.get('expiry_date')
            data['payment_method'] = subscription.get('payment_method')
        
        return data


class ExternalOrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name']


class ExternalOrganizationsListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    results = serializers.ListField(child=ExternalOrganizationSerializer())


class ExternalOrganizationsNamesResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    results = serializers.ListField(child=ExternalOrganizationSerializer())


class ExternalOrganizationNamesQuerySerializer(serializers.Serializer):
    org_ids = serializers.CharField(
        help_text="Comma-separated organization IDs, e.g. 1,2,3",
    )


class OrganizationResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    results = OrganizationSerializer()


class EmptyResultsResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    results = serializers.ListField(child=serializers.DictField(), allow_empty=True)


class OrganizationUserResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    results = UserSerializer()


class OrganizationUserStatsSerializer(serializers.Serializer):
    all_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    un_active_users = serializers.IntegerField()
    trash_users = serializers.IntegerField()


class OrganizationUserStatsResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    results = OrganizationUserStatsSerializer()


class OrganizationCreateRequestSerializer(serializers.Serializer):
    # Admin user fields
    email = serializers.EmailField()
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    gender = serializers.CharField()
    contact = serializers.CharField()
    country_code = serializers.CharField(required=False)

    # Organization fields
    name = serializers.CharField()
    country = serializers.CharField()
    address = serializers.CharField()
    status = serializers.BooleanField()
    validation_frequency = serializers.CharField()
    ip = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    ssh_key = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    api_key = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    secret_key = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    
class OrganizationUpdateRequestSerializer(serializers.Serializer):
    # Admin user fields (all optional for PATCH)
    email = serializers.EmailField(required=False)
    username = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True, required=False)
    first_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    last_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    gender = serializers.CharField(required=False)
    contact = serializers.CharField(required=False)
    country_code = serializers.CharField(required=False)

    # Organization fields (all optional for PATCH)
    name = serializers.CharField(required=False)
    country = serializers.CharField(required=False)
    address = serializers.CharField(required=False)
    status = serializers.BooleanField(required=False)
    validation_frequency = serializers.CharField(required=False)
    ip = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    ssh_key = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    api_key = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    secret_key = serializers.CharField(required=False, allow_blank=True, allow_null=True)

class BulkStatusUpdateRequestSerializer(serializers.Serializer):
    organization_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1), allow_empty=False
    )
    status = serializers.BooleanField()

class ResultsResponseSerializer(serializers.Serializer):
        status = serializers.BooleanField()
        message = serializers.CharField()
        results = serializers.IntegerField()


class UpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()


class DeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()


class OrganizationRequestSerializer(serializers.Serializer):
        organization_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1), allow_empty=False
    )

class OrganizationUserRequestSerializer(serializers.Serializer):
        user_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1), allow_empty=False
    )

class UserStatusUpdateRequestSerializer(serializers.Serializer):
    user_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1), allow_empty=False
    )
    status = serializers.BooleanField()