from django.utils import timezone

from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase

from app.models import MyUser, Profile, Backpack


class BackpackModelTestCase(TestCase):
    model = Backpack

    def setUp(self):
        self.user = MyUser.objects.create_user(email='email@email.com', password='fasf3qf3ff')
        self.backpack = self.model.objects.create(profile=self.user.profile)

    def test_str(self):
        name = 'name'
        self.backpack.name = name
        self.backpack.save()
        self.assertEqual(str(self.backpack), name)

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

    def test_str(self):
        user = self.user_model.objects.create_user(**self.valid_user_data)
        profile = self.model.objects.get(user=user)
        self.assertEqual(str(profile), str(user))


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

    def test_str(self):
        self.assertEqual(str(self.user), self.valid_user_data['email'])

    def test_email_is_unique(self):
        with self.assertRaises(IntegrityError):
            self.model.objects.create_user(**self.valid_user_data)

    def test_email_is_required(self):
        with self.assertRaises(TypeError):
            self.model.objects.create_user(password='fvava23f')
