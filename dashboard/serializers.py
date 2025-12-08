from rest_framework import serializers


class ActiveUsersOverviewResultsSerializer(serializers.Serializer):
    active_users = serializers.IntegerField()
    percentage_difference = serializers.FloatField(allow_null=True, required=False)


class ActiveUsersOverviewResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    results = ActiveUsersOverviewResultsSerializer()


class TotalsResultsSerializer(serializers.Serializer):
    registered_organizations = serializers.IntegerField()
    total_users = serializers.IntegerField()
    organization_percentage_difference = serializers.FloatField(allow_null=True, required=False)
    user_percentage_difference = serializers.FloatField(allow_null=True, required=False)


class TotalsResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    results = TotalsResultsSerializer()


class RoleDistributionItemSerializer(serializers.Serializer):
    role_name = serializers.CharField()
    user_count = serializers.IntegerField()
    percentage = serializers.FloatField()


class RoleDistributionResultsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    distribution = RoleDistributionItemSerializer(many=True)


class RoleDistributionResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    results = RoleDistributionResultsSerializer()


class SignupChartDataSerializer(serializers.Serializer):
    active = serializers.ListField(child=serializers.IntegerField())
    inactive = serializers.ListField(child=serializers.IntegerField())


class OrganizationSignupsResultsSerializer(serializers.Serializer):
    labels = serializers.ListField(child=serializers.CharField())
    data = SignupChartDataSerializer()


class OrganizationSignupsResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    results = OrganizationSignupsResultsSerializer()
