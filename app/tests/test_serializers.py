from django.test import TestCase
from rest_framework.exceptions import ValidationError

from app.models import MyUser, Backpack, Category, Subcategory, Product, Review, Brand
from app.serializers import UserSerializer, BackpackSerializer, PrivateGearSerializer, CategorySerializer, \
    ProductSerializer, ReviewSerializer, SubcategorySerializer


class Empty:
    pass


valid_user_data = {'email': 'email@email.com', 'password': 'fas8asdvas'}


class SubcategorySerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MyUser.objects.create_user(**valid_user_data)
        cls.category = Category.objects.create(name='name')

    def create_subcategory(self):
        serializer = SubcategorySerializer(data={'name': 'name', 'category': self.category.pk})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return serializer

    def test_contains_expected_fields(self):
        serializer = self.create_subcategory()
        self.assertCountEqual(serializer.data.keys(), ['id', 'name', 'category'])

    def test_unique_validator(self):
        self.create_subcategory()
        with self.assertRaises(ValidationError):
            self.create_subcategory()


class ReviewSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = MyUser.objects.create_user(**valid_user_data)
        cls.cat = Category.objects.create(name='name')
        cls.sub_cat = Subcategory.objects.create(name='subname', category=cls.cat)
        cls.brand = Brand.objects.create(author=cls.user.profile, name='name')
        cls.product = Product.objects.create(author=cls.user.profile, brand=cls.brand,
                                             subcategory=cls.sub_cat, name='name')

    def create_review(self, user=None):
        if not user:
            user = self.user
        serializer = ReviewSerializer(data={'product': self.product.id, 'author': user.id,
                                            'summary': 'summary', 'text': 'text'})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return serializer

    def test_contains_expected_fields(self):
        serializer = self.create_review()
        self.assertCountEqual(serializer.data.keys(),
                              ['id', 'author', 'product', 'weight_net', 'weight_gross', 'summary', 'text'])

    def test_unique_validator(self):
        user2 = MyUser.objects.create_user(email='efa@fasd.com', password='fasgasgs3')
        self.create_review(user2)
        with self.assertRaises(ValidationError):
            self.create_review(user2)


class ProductSerializerTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.cat = Category.objects.create(name='name')
        cls.user = MyUser.objects.create_user(**valid_user_data)
        cls.sub_cat = Subcategory.objects.create(name='subname', category=cls.cat)
        cls.brand = Brand.objects.create(author=cls.user.profile, name='name')

    def create_product(self):
        serializer = ProductSerializer(data={'subcategory': self.sub_cat.id, 'author': self.user.id,
                                             'name': 'name', 'brand': self.brand.id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return serializer

    def test_contains_expected_fields(self):
        serializer = self.create_product()
        self.assertCountEqual(serializer.data.keys(),
                              ['id', 'author', 'name', 'full_name', 'brand', 'subcategory', 'url', 'reviews_amount',
                               'reviews'])

    def test_unique_validator(self):
        self.create_product()
        with self.assertRaises(ValidationError):
            self.create_product()


class CategorySerializerTestCase(TestCase):
    def test_contains_expected_fields(self):
        serializer = CategorySerializer(data={'name': 'cat_name'})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        self.assertCountEqual(serializer.data.keys(), ['id', 'name', 'subcategories'])


class PrivateGearSerializerTestCase(TestCase):

    def test_contains_expected_fields(self):
        user = MyUser.objects.create_user(**valid_user_data)
        serializer = PrivateGearSerializer(user.profile, data={'private_gear': []})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        self.assertCountEqual(serializer.data.keys(), ['private_gear'])

    def test_private_gear_required(self):
        user = MyUser.objects.create_user(**valid_user_data)
        serializer = PrivateGearSerializer(user.profile, data={})
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)


class BackpackSerializerTestCase(TestCase):
    serializer_class = BackpackSerializer

    def test_contains_expected_fields(self):
        user = MyUser.objects.create_user(**valid_user_data)
        backpack = Backpack.objects.create(profile=user.profile)
        request = Empty()
        request.user = user
        data = self.serializer_class(backpack, context={'request': request}).data
        self.assertCountEqual(data.keys(), ['id', 'created', 'updated', 'profile', 'is_owner',
                                            'shared', 'name', 'description', 'list'])

    def test_get_is_owner(self):
        user = MyUser.objects.create_user(**valid_user_data)
        backpack = Backpack.objects.create(profile=user.profile)
        request = Empty()
        request.user = user
        data = self.serializer_class(backpack, context={'request': request}).data
        self.assertTrue(data['is_owner'])
        request.user = MyUser.objects.create_user(email='email2@email.com', password='fasf23f3')
        data = self.serializer_class(backpack, context={'request': request}).data
        self.assertFalse(data['is_owner'])
        request.user = Empty()
        request.user.is_anonymous = True
        data = self.serializer_class(backpack, context={'request': request}).data
        self.assertFalse(data['is_owner'])


class UserSerializerTestCase(TestCase):
    serializer_class = UserSerializer

    def test_contains_expected_fields(self):
        user = MyUser.objects.create_user(**valid_user_data)
        data = self.serializer_class(user).data
        self.assertCountEqual(data.keys(), ['email', 'id'])

    def test_created_user_is_active_is_false(self):
        serializer = self.serializer_class(data=valid_user_data)
        serializer.is_valid()
        user = serializer.save()
        self.assertFalse(user.is_active)
