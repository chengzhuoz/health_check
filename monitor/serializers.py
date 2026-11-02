from rest_framework import serializers

from .models import Service, Team


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['id', 'name', 'owner']


class ServiceSerializer(serializers.ModelSerializer):
    token = serializers.CharField(write_only=True, max_length=189, trim_whitespace=False)

    class Meta:
        model = Service
        fields = ['id', 'team', 'name', 'environment', 'health_check_url', 'token']

    def validate_token(self, value):
        # 中文占多个字节，要按编码后的长度检查
        if len(value.encode()) > 189:
            raise serializers.ValidationError('Token 不能超过 189 字节。')
        return value
