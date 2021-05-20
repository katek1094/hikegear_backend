from rest_framework.test import APIClient
from django.test import TestCase

from app.models import MyUser


class DRFTesterException(Exception):
    pass


class DRFTesterCase(TestCase):
    url = None
    user1data = {'email': 'user1@email.com', 'password': '137sword1%'}
    user2data = {'email': 'user2@email.com', 'password': '137sword2%'}
    user1 = None
    user2 = None

    response_fields = None

    @classmethod
    def setUpTestData(cls):
        cls.check_for_url()
        cls.user1 = MyUser.objects.create_user(**cls.user1data)
        cls.user2 = MyUser.objects.create_user(**cls.user2data)
        cls.moreSetUpTestTestData()

    @classmethod
    def moreSetUpTestTestData(cls):
        pass

    def setUp(self):
        self.client = APIClient()

    @classmethod
    def check_for_url(cls):
        if cls.url is None:
            raise DRFTesterException('url not declared!')

    def login_client(self, user_instance):
        self.client.force_login(user_instance)

    def logout_client(self):
        self.client.logout()

    def check_response_fields(self, json, fields=None):
        if fields is None:
            if self.response_fields:
                fields = self.response_fields
                self.assertTrue(any(field in json for field in fields))
                self.assertEqual(len(json), len(fields))

    def status_check(self, response, code):
        self.assertEqual(response.status_code, code)
