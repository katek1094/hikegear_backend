from django.test import TestCase

from app.models import MyUser
from app.serializers import UserSerializer


class UserSerializerTestCase(TestCase):
    model = MyUser
    serializer_class = UserSerializer
    valid_user_data = {'email': 'email@email.com', 'password': 'fas8asdvas'}

    def test_contains_expected_fields(self):
        user = self.model.objects.create_user(**self.valid_user_data)
        data = self.serializer_class(user).data
        self.assertCountEqual(data.keys(), ['email', 'id'])

    def test_created_user_is_active_is_false(self):
        serializer = self.serializer_class(data=self.valid_user_data)
        serializer.is_valid()
        user = serializer.save()
        self.assertFalse(user.is_active)




