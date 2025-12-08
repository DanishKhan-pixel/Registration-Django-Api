from rest_framework import serializers
import role
from role.models import Permission, Role
from utils.helpers import EXCLUDED_FIELDS


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        exclude = EXCLUDED_FIELDS


class RoleSerializer(serializers.ModelSerializer):
    permissions = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Permission.objects.all(), write_only=True
    )
    permissions_list = PermissionSerializer(source='permissions', many=True, read_only=True)
    total_permissions = serializers.SerializerMethodField()


    class Meta:
        model = Role
        exclude = EXCLUDED_FIELDS



    def get_total_permissions(self, obj):
        return obj.permissions.count()

    def create(self, validated_data):
        permissions = validated_data.pop('permissions', [])
        role = Role.objects.create(**validated_data)
        role.permissions.set(permissions)
        return role

    def update(self, instance, validated_data):
        permissions = validated_data.pop('permissions', None)
        instance = super().update(instance, validated_data)
        if permissions is not None:
            instance.permissions.set(permissions)
        return instance


class PermissionListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    results = serializers.ListField(child=PermissionSerializer())


class RoleResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    results = RoleSerializer()


class RoleListResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()



class RoleRequestSerializer(serializers.Serializer):
    role_ids = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)


class RoleStatusUpdateRequestSerializer(serializers.Serializer):
    role_ids = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)
    status = serializers.BooleanField()


class DeleteResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()


class UpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    results = serializers.ListField(child=serializers.DictField(), allow_empty=True)


class StatusUpdateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()


class RestoreResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()