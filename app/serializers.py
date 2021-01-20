from rest_framework import serializers
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError

from.models import MyUser


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = ['email', 'password', 'id']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        try:
            user = MyUser.objects.create_user(**validated_data)
        except ValidationError as msg:
            raise serializers.ValidationError(msg)
        return user


class MyTokenSerializer(serializers.Serializer):
    email = serializers.CharField(label='email', write_only=True)
    password = serializers.CharField(label='password', style={'input_type': 'password'},
                                     trim_whitespace=False, write_only=True)
    token = serializers.CharField(label="Token", read_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        if email and password:
            user = authenticate(request=self.context.get('request'), email=email, password=password)
            if not user:
                raise serializers.ValidationError('Unable to log in with provided credentials.', code='authorization')
        else:
            raise serializers.ValidationError('Must include "email" and "password".', code='authorization')
        attrs['user'] = user
        return attrs