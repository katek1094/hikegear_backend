from rest_framework import serializers
from django.core.exceptions import ValidationError

from .models import MyUser, Profile, Backpack, Category, Subcategory, Brand, Product
from .fields import CurrentProfileDefault


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name']


class SubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcategory
        fields = ['id', 'name']


class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubcategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'subcategories']


class ProductSerializer(serializers.ModelSerializer):
    brand = BrandSerializer()
    subcategory = SubcategorySerializer()

    class Meta:
        model = Product
        fields = ['id', 'name', 'brand', 'description', 'subcategory', 'sex']


class PrivateGearSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['private_gear']

    def validate(self, data):
        if 'private_gear' not in data:
            raise serializers.ValidationError("You must provide 'private_gear'")
        return data


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['user_id']


class BackpackReadSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Backpack
        fields = ['id', 'created', 'updated', 'profile', 'is_owner', 'shared', 'name', 'description', 'list']
        read_only_fields = ['__all__']

    def get_is_owner(self, obj):
        if self.context['request'].user.is_anonymous:
            return False
        profile = self.context['request'].user.profile
        return profile == obj.profile


class BackpackSerializer(serializers.ModelSerializer):
    profile = serializers.PrimaryKeyRelatedField(
        default=CurrentProfileDefault(),
        queryset=Profile.objects.all()
    )

    class Meta:
        model = Backpack
        fields = ['profile', 'name', 'description', 'list', 'shared']

    def create(self, validated_data):
        if len(validated_data['name']) > 60:
            validated_data['name'] = validated_data['name'][:59]
        if 'description' in validated_data:
            if len(validated_data['description']) > 1000:
                validated_data['description'] = validated_data['description'][:999]
        try:
            backpack = Backpack.objects.create(**validated_data)
        except ValidationError as msg:
            raise serializers.ValidationError(msg)
        return backpack


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = ['id', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        validated_data['is_active'] = False
        try:
            user = MyUser.objects.create_user(**validated_data)
        except ValidationError as msg:
            raise serializers.ValidationError(msg)
        return user
