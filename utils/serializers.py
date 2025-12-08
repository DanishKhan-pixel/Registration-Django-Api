from rest_framework import serializers


class ValidationErrorSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()

class InternalServerErrorSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()


