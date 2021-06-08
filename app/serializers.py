from rest_framework import serializers, validators
from django.core.exceptions import ValidationError

from .models import MyUser, Profile, Backpack, Category, Subcategory, Brand, Product, Review
from .fields import CurrentProfileDefault


class ModelRepresentationPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def __init__(self, **kwargs):
        self.serializer = kwargs.pop('serializer', None)
        if self.serializer is not None and not issubclass(self.serializer, serializers.Serializer):
            raise TypeError('"serializer" is not a valid serializer class')

        super().__init__(**kwargs)

    def use_pk_only_optimization(self):
        return False if self.serializer else True

    def to_representation(self, instance):
        if self.serializer:
            return self.serializer(instance, context=self.context).data
        return super().to_representation(instance)


class DynamicFieldsModelSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name']


class SubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcategory
        fields = ['id', 'name']
        validators = [
            validators.UniqueTogetherValidator(queryset=Subcategory.objects.all(), fields=['name', 'category'])
        ]


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(default=CurrentProfileDefault(), queryset=Profile.objects.all())
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = Review
        fields = ['id', 'author', 'product', 'weight_net', 'weight_gross', 'summary', 'text']
        validators = [
            validators.UniqueTogetherValidator(queryset=Review.objects.all(), fields=['author', 'product'])
        ]


class ProductSerializer(DynamicFieldsModelSerializer):
    author = serializers.PrimaryKeyRelatedField(
        default=CurrentProfileDefault(),
        queryset=Profile.objects.all()
    )

    brand = ModelRepresentationPrimaryKeyRelatedField(queryset=Brand.objects.all(), serializer=BrandSerializer)
    subcategory = ModelRepresentationPrimaryKeyRelatedField(queryset=Subcategory.objects.all(),
                                                            serializer=SubcategorySerializer)
    reviews = ReviewSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'author', 'name', 'full_name', 'brand', 'subcategory', 'url', 'reviews_amount', 'reviews']
        read_only_fields = ['id', 'full_name', 'reviews_amount', 'reviews']
        validators = [
            validators.UniqueTogetherValidator(queryset=Product.objects.all(), fields=['brand', 'subcategory', 'name'])
        ]


class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubcategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'subcategories']


class PrivateGearSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['private_gear']

    def validate(self, data):
        if 'private_gear' not in data:
            raise serializers.ValidationError("You must provide 'private_gear'")
        return data


class BackpackSerializer(serializers.ModelSerializer):
    profile = serializers.PrimaryKeyRelatedField(
        default=CurrentProfileDefault(),
        queryset=Profile.objects.all()
    )
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Backpack
        fields = ['id', 'created', 'updated', 'profile', 'is_owner', 'shared', 'name', 'description', 'list']
        read_only_fields = ['id', 'created', 'updated', 'is_owner']

    def create(self, validated_data):
        if 'name' in validated_data and len(validated_data['name']) > 60:
            validated_data['name'] = validated_data['name'][:59]
        if 'description' in validated_data:
            if len(validated_data['description']) > 1000:
                validated_data['description'] = validated_data['description'][:999]
        try:
            backpack = Backpack.objects.create(**validated_data)
        except ValidationError as msg:
            raise serializers.ValidationError(msg)
        return backpack

    def get_is_owner(self, obj):
        if self.context['request'].user.is_anonymous:
            return False
        profile = self.context['request'].user.profile
        return profile == obj.profile


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
