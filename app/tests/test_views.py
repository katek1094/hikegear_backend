from rest_framework.authtoken.models import Token

from .drf_tester import DRFTesterCase
from app.models import MyUser, Profile

# python manage.py test


class TestUserViewSetChangePasswordAction(DRFTesterCase):
    url = '/api/users/change_password/'
    valid_new_password = '1k2j3b4j'

    def test_unauthorized_valid_request(self):
        response = self.client.patch(self.url, {'old_password': self.user1data['password'],
                                                'new_password': self.valid_new_password})
        self.status_check(response, 401)

    def test_authorized_valid_request(self):
        self.login_client(self.user1)
        response = self.client.patch(self.url, {'old_password': self.user1data['password'],
                                                'new_password': self.valid_new_password})
        self.status_check(response, 200)
        self.assertTrue(MyUser.objects.get(id=self.user1.id).check_password(self.valid_new_password))

    def test_authorized_request_no_data(self):
        self.login_client(self.user1)
        response = self.client.patch(self.url, {})
        self.status_check(response, 400)

    def test_authorized_request_no_old_password(self):
        self.login_client(self.user1)
        response = self.client.patch(self.url, {'new_password': self.valid_new_password})
        self.status_check(response, 400)

    def test_authorized_request_no_new_password(self):
        self.login_client(self.user1)
        response = self.client.patch(self.url, {'old_password': self.user1data['password']})
        self.status_check(response, 400)

    def test_authorized_request_invalid_old_password(self):
        self.login_client(self.user1)
        response = self.client.patch(self.url, {'new_password': self.valid_new_password,
                                                'old_password': 'invalid'})
        self.status_check(response, 400)

    def test_authorized_request_invalid_new_password(self):
        self.login_client(self.user1)
        response = self.client.patch(self.url, {'new_password': 'invalid',
                                                'old_password': self.user1data['password']})
        self.status_check(response, 400)


class TestUserViewSetCreateAction(DRFTesterCase):
    url = '/api/users/'
    new_user_data = {'email': 'new_user@email.com', 'password': 'new_pass137'}
    response_fields = ['email', 'id']

    def test_unauthorized_valid_request(self):
        response = self.client.post(self.url, self.new_user_data)
        json = response.json()
        self.status_check(response, 201)
        self.check_response_fields(json)
        self.assertTrue(MyUser.objects.get(**json).check_password(self.new_user_data['password']))
        self.assertTrue(Profile.objects.get(user_id=json['id']))
        self.assertTrue(Token.objects.get(user_id=json['id']))

    def test_post_method_data_missing(self):
        response = self.client.post(self.url)
        self.status_check(response, 400)

    def test_post_method_email_missing(self):
        response = self.client.post(self.url, {'password': self.new_user_data['password']})
        self.status_check(response, 400)

    def test_post_method_password_missing(self):
        response = self.client.post(self.url, {'email': self.new_user_data['email']})
        self.status_check(response, 400)

    def test_post_method_email_occupied(self):
        response = self.client.post(self.url, {'email': self.user1.email, 'password': self.new_user_data['password']})
        self.status_check(response, 400)

    def test_post_method_password_invalid(self):
        response = self.client.post(self.url, {'email': self.new_user_data['email'], 'password': '1k2j3b6'})
        self.status_check(response, 400)


class ObtainTokenTestCase(DRFTesterCase):
    url = '/api/obtain_token'

    def test_obtaining_token(self):
        response = self.client.post(self.url, {'email': self.user1data['email'],
                                               'password': self.user1data['password']})
        self.status_check(response, 200)
        self.assertTrue('token' in response.json())
        self.assertEqual(response.json()['token'], self.user1.auth_token.key)
