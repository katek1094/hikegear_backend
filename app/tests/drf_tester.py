# import io

# from PIL import Image as Img
from rest_framework.test import APIClient
# from django.core.files.base import File
from django.test import TestCase

from app.models import MyUser


class DRFTesterException(Exception):
    pass


class DRFTesterCase(TestCase):
    url = None
    user1data = {'email': f'user1@email.com', 'password': f'137sword1%'}
    user2data = {'email': f'user2@email.com', 'password': f'137sword2%'}
    user1 = None
    user2 = None

    images_uploaded = False
    response_fields = None

    @classmethod
    def setUpTestData(cls):
        cls.check_for_url()
        cls.user1 = MyUser.objects.create_user(**cls.user1data)
        cls.user2 = MyUser.objects.create_user(**cls.user2data)

    def setUp(self):
        self.client = APIClient()
        self.images_uploaded = False

    # def tearDown(self):
    #     if self.images_uploaded:
    #         for img in Image.objects.all():
    #             img.image.delete()

    @classmethod
    def check_for_url(cls):
        if cls.url is None:
            raise DRFTesterException('url not declared!')

    def login_client(self, user_instance):
        self.client.force_login(user_instance)

    def logout_client(self):
        self.client.logout()

    # def generate_photo_file(self):
    #     file = io.BytesIO()
    #     image = Img.new('RGBA', size=(100, 100), color=(155, 0, 0))
    #     image.save(file, 'png')
    #     file.name = 'test.png'
    #     file.seek(0)
    #     self.images_uploaded = True
    #     return file

    # def get_django_image_file(self):
    #     return File(self.generate_photo_file())

    def check_response_fields(self, json, fields=None):
        if fields is None:
            if self.response_fields:
                fields = self.response_fields
                self.assertTrue(any(field in json for field in fields))
                self.assertEqual(len(json), len(fields))

    def status_check(self, response, code):
        self.assertEqual(response.status_code, code)
