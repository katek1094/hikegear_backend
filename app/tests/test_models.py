from django.utils import timezone

from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase

from app.models import MyUser, Profile, Backpack, Brand, Category, Subcategory, Product, Review


class SetUpProduct(TestCase):
    def setUp(self):
        self.user = MyUser.objects.create_user(email='email@email.com', password='fasf3qf3ff')
        self.brand = Brand.objects.create(author=self.user.profile, name='brand_name')
        self.category = Category.objects.create(name='category_name')
        self.subcategory = Subcategory.objects.create(category=self.category, name='subcategory_name')
        self.product_name = 'product_name'
        self.product = Product.objects.create(author=self.user.profile, brand=self.brand,
                                              subcategory=self.subcategory, name=self.product_name)


class ReviewModelTestCase(SetUpProduct):
    def setUp(self):
        super().setUp()
        self.review = Review.objects.create(author=self.user.profile, product=self.product, summary='', text='')

    def test_unique_constraint(self):
        with self.assertRaises(IntegrityError):
            Review.objects.create(author=self.user.profile, product=self.product, summary='a', text='t')

    def test_created_updated(self):
        self.assertLess((timezone.now() - self.review.created).total_seconds(), 0.01)
        self.assertLess((timezone.now() - self.review.updated).total_seconds(), 0.01)


class ProductModelTestCase(SetUpProduct):
    def test_unique_constraint(self):
        user2 = MyUser.objects.create_user(email='email2@email.com', password='fasf3qf3ff')
        with self.assertRaises(IntegrityError):
            Product.objects.create(author=user2.profile, brand=self.brand,
                                   subcategory=self.subcategory, name=self.product_name)

    def test_reviews_amount(self):
        self.assertEqual(self.product.reviews_amount, 0)
        Review.objects.create(author=self.user.profile, product=self.product, summary='', text='')
        self.assertEqual(self.product.reviews_amount, 1)

    def test_full_name(self):
        self.assertEqual(self.product.full_name, f'{self.subcategory.name} {self.brand.name} {self.product.name}')
        subcategory2 = Subcategory.objects.create(category=self.category, name='inne')
        product2 = Product.objects.create(author=self.user.profile, brand=self.brand,
                                          subcategory=subcategory2, name=self.product_name)
        self.assertEqual(product2.full_name, f'{self.brand.name} {self.product.name}')

    def test_created_updated(self):
        self.assertLess((timezone.now() - self.product.created).total_seconds(), 0.01)
        self.assertLess((timezone.now() - self.product.updated).total_seconds(), 0.01)


class SubcategoryModelTestCase(TestCase):
    def test_unique_constraint(self):
        category = Category.objects.create(name='name')
        subcategory_name = 'subcat_name'
        Subcategory.objects.create(category=category, name=subcategory_name)
        Subcategory.objects.create(category=category, name='other name')  # create valid subcategory
        with self.assertRaises(IntegrityError):
            Subcategory.objects.create(category=category, name=subcategory_name)


class CategoryModelTestCase(TestCase):
    def test_unique_constraint(self):
        Category.objects.create(name='name')
        with self.assertRaises(IntegrityError):
            Category.objects.create(name='name')


class BrandModelTestCase(TestCase):
    model = Brand

    def setUp(self):
        self.user = MyUser.objects.create_user(email='email@email.com', password='fasf3qf3ff')

    def test_unique_constraint(self):
        name = 'name'
        self.model.objects.create(author=self.user.profile, name=name)
        with self.assertRaises(IntegrityError):
            self.model.objects.create(author=self.user.profile, name=name)

    def test_created_updated(self):
        brand = self.model.objects.create(author=self.user.profile, name='name')
        self.assertLess((timezone.now() - brand.created).total_seconds(), 0.01)
        self.assertLess((timezone.now() - brand.updated).total_seconds(), 0.01)


class BackpackModelTestCase(TestCase):
    model = Backpack

    def setUp(self):
        self.user = MyUser.objects.create_user(email='email@email.com', password='fasf3qf3ff')
        self.backpack = self.model.objects.create(profile=self.user.profile)

    def test_default_values(self):
        self.assertEqual(self.backpack.name, '')
        self.assertEqual(self.backpack.description, '')
        self.assertEqual(self.backpack.list, [])
        self.assertEqual(self.backpack.shared, False)
        self.assertLess((timezone.now() - self.backpack.created).total_seconds(), 0.01)
        self.assertLess((timezone.now() - self.backpack.updated).total_seconds(), 0.01)


class ProfileModelTestCase(TestCase):
    user_model = MyUser
    model = Profile
    valid_user_data = {'email': 'email@email.com', 'password': 'fas8asdvas'}

    def test_is_auto_created_after_user(self):
        user = self.user_model.objects.create_user(**self.valid_user_data)
        self.assertTrue(self.model.objects.get(user=user))

    def test_private_gear_default(self):
        user = self.user_model.objects.create_user(**self.valid_user_data)
        profile = self.model.objects.get(user=user)
        self.assertEqual(profile.private_gear, [])


class MyUserModelTestCase(TestCase):
    model = MyUser
    valid_user_data = {'email': 'email@email.com', 'password': 'fas8asdvas'}

    def setUp(self):
        self.user = self.model.objects.create_user(**self.valid_user_data)

    def test_password_min_len_validator(self):  # min len is 8 by default
        with self.assertRaises(ValidationError):
            self.model.objects.create_user(email='email1@email.com', password='mkjn123')  # password len = 7
        self.assertTrue(self.model.objects.create_user(email='email1@email.com', password='mkjn1256'))  # 8

    def test_password_numeric_validator(self):
        with self.assertRaises(ValidationError):
            self.model.objects.create_user(email='email1@email.com', password='874891094')

    def test_password_common_validator(self):
        with self.assertRaises(ValidationError):
            self.model.objects.create_user(email='email1@email.com', password='password')

    def test_email_is_unique(self):
        with self.assertRaises(IntegrityError):
            self.model.objects.create_user(**self.valid_user_data)

    def test_email_is_required(self):
        with self.assertRaises(TypeError):
            self.model.objects.create_user(password='fvava23f')
