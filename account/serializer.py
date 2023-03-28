from rest_framework import serializers

from account.models import User, UserAPIToken


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'is_activated']


class UserAPITokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAPIToken
        fields = ['token', 'is_active', 'is_deleted']
