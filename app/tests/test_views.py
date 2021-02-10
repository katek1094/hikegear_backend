from rest_framework.authtoken.models import Token
from app.models import MyUser, Profile, Backpack
from .drf_tester import DRFTesterCase


class InitialViewTestCase(DRFTesterCase):
    url = '/api/initial'
    response_fields = ['backpacks']

    def test_unauthorized_get_method(self):
        response = self.client.get(self.url)
        self.status_check(response, 401)

    def test_authorized_valid_get_request(self):
        self.login_client(self.user1)
        response = self.client.get(self.url)
        self.status_check(response, 200)
        self.check_response_fields(response.json())
        # TODO: check backpacks


class BackPackViewSetTestCase(DRFTesterCase):
    url = '/api/backpacks/'
    name = 'backpack name'
    description = 'backpack description'
    list = {'type': 'category'}
    data = {'name': name, 'description': description, 'list': list}
    response_fields = ['created', 'updated', 'profile', 'description', 'name', 'list', 'id']

    def test_unauthorized_valid_get_request(self):
        backpack = Backpack.objects.create(profile=self.user1.profile)
        response = self.client.get(self.url + str(backpack.id) + '/')
        self.status_check(response, 401)

    def test_authorized_valid_get_request_of_yours_data(self):
        self.get_request(self.user1, self.user1)

    def test_authorized_valid_get_request_of_others_data(self):
        self.get_request(self.user1, self.user2)

    def get_request(self, logged, owner):
        self.login_client(logged)
        backpack = Backpack.objects.create(profile=owner.profile)
        response = self.client.get(self.url + str(backpack.id) + '/')
        self.status_check(response, 200)
        json = response.json()
        self.check_response_fields(json)
        self.assertEqual(Backpack.objects.get(profile=json['profile']['user_id'], id=json['id'], list=json['list']),
                         backpack)

    def test_invalid_get_request(self):
        self.login_client(self.user1)
        backpack = Backpack.objects.create(profile=self.user1.profile)
        response = self.client.get(self.url + str(backpack.id + 1) + '/')
        self.status_check(response, 404)

    def test_unauthorized_valid_post_request(self):
        request = self.client.post(self.url, {'name': self.name, 'list': self.list}, format='json')
        self.status_check(request, 401)

    def test_authorized_valid_post_request(self):
        self.login_client(self.user1)
        request = self.client.post(self.url, {'name': self.name, 'list': self.list}, format='json')
        self.status_check(request, 201)
        json = request.json()
        self.check_response_fields(json)
        self.assertTrue(Backpack.objects.get(name=self.name, id=json['id'], list=self.list, profile=self.user1.profile))

    def test_unauthorized_valid_patch_request(self):
        request = self.client.patch(self.url, {'name': self.name, 'list': self.list}, format='json')
        self.status_check(request, 401)

    def test_authorized_valid_patch_request_of_yours_data(self):
        backpack = Backpack.objects.create(profile=self.user1.profile)
        self.login_client(self.user1)
        request = self.client.patch(self.url + str(backpack.id) + '/', self.data, format='json')
        self.status_check(request, 200)
        json = request.json()
        self.check_response_fields(json)
        self.assertTrue(Backpack.objects.get(name=self.name, id=backpack.id, list=self.list, profile=backpack.profile,
                                             description=self.description))

    def test_authorized_valid_patch_request_of_others_data(self):
        backpack = Backpack.objects.create(profile=self.user2.profile)
        self.login_client(self.user1)
        request = self.client.patch(self.url + str(backpack.id) + '/', self.data, format='json')
        self.status_check(request, 403)

    def test_unauthorized_valid_delete_request(self):
        backpack = Backpack.objects.create(profile=self.user1.profile)
        request = self.client.delete(self.url + str(backpack.id) + '/')
        self.status_check(request, 401)

    def test_authorized_valid_delete_request_of_yours_data(self):
        backpack = Backpack.objects.create(profile=self.user1.profile)
        self.login_client(self.user1)
        request = self.client.delete(self.url + str(backpack.id) + '/')
        self.status_check(request, 204)
        self.assertFalse(Backpack.objects.filter(id=backpack.id, profile=backpack.profile))

    def test_authorized_valid_delete_request_of_others_data(self):
        backpack = Backpack.objects.create(profile=self.user1.profile)
        self.login_client(self.user2)
        request = self.client.delete(self.url + str(backpack.id) + '/')
        self.status_check(request, 403)


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
        response = self.client.patch(self.url, {'new_password': self.valid_new_password, 'old_password': 'invalid'})
        self.status_check(response, 400)

    def test_authorized_request_invalid_new_password(self):
        self.login_client(self.user1)
        response = self.client.patch(self.url, {'new_password': 'invalid', 'old_password': self.user1data['password']})
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
