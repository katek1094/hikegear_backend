from rest_framework import serializers
from django.core.exceptions import ValidationError

from .models import MyUser, Profile, Backpack
from .fields import CurrentProfileDefault


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['user_id']


class BackpackReadSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = Backpack
        fields = ['id', 'created', 'updated', 'profile', 'name', 'description', 'list']
        read_only_fields = ['__all__']


class BackpackSerializer(serializers.ModelSerializer):
    profile = serializers.PrimaryKeyRelatedField(
        default=CurrentProfileDefault(),
        queryset=Profile.objects.all()
    )

    class Meta:
        model = Backpack
        fields = ['profile', 'name', 'description', 'list']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = ['email', 'password', 'id']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        try:
            user = MyUser.objects.create_user(**validated_data)
        except ValidationError as msg:
            raise serializers.ValidationError(msg)
        return user
