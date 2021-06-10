from django.core import mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
import json
from openpyxl import Workbook
import os

from app.models import MyUser, Profile, Backpack
from .drf_tester import DRFTesterCase


class ImportFromExcelViewTestCase(DRFTesterCase):
    url = '/api/import_from_excel'

    @staticmethod
    def generate_valid_excel_file(empty=False):
        excel_file = open('private.xlsx', 'wb')
        workbook = Workbook()
        ws = workbook.active
        if not empty:
            ws.append(['plecak', 'OMW', 110])
            ws.append(['śpiwór', 'haha', 232])
            ws.append(['kategoria', 'nazwa kategorii'])
            ws.append(['karimata', 'decathlon', 11])
        workbook.save(excel_file)
        excel_file.close()
        return open('private.xlsx', 'rb')

    def test_unauthorized_request(self):
        response = self.client.post(self.url)
        self.status_check(response, 403)

    def test_valid_request(self):
        excel_file = self.generate_valid_excel_file
        self.login_client(self.user1)
        response = self.client.post(self.url, {'excel': excel_file})
        os.remove('private.xlsx')
        self.status_check(response, 200)
        self.assertEqual(response.json()['private_gear'], Profile.objects.get(user=self.user1).private_gear)
        data = response.json()['private_gear']
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['name'], 'importowane z pliku excel')
        self.assertEqual(data[1]['name'], 'nazwa kategorii')
        self.assertEqual(data[1]['items'][0]['name'], 'karimata')
        self.assertEqual(data[1]['items'][0]['description'], 'decathlon')
        self.assertEqual(data[1]['items'][0]['weight'], 11)

    def test_invalid_data_name(self):
        excel_file = self.generate_valid_excel_file
        self.login_client(self.user1)
        response = self.client.post(self.url, {'fasdf': excel_file})  # wrong dict key
        self.status_check(response, 400)

    def test_no_items_provided(self):
        excel_file = self.generate_valid_excel_file(True)
        self.login_client(self.user1)
        response = self.client.post(self.url, {'excel': excel_file})
        self.status_check(response, 400)


class ImportFromHgViewTestCase(DRFTesterCase):
    url = '/api/import_from_hg'

    def test_unauthorized_request(self):
        response = self.client.post(self.url)
        self.status_check(response, 403)

    def test_id_missing(self):
        self.login_client(self.user1)
        response = self.client.post(self.url)
        self.status_check(response, 400)

    def test_invalid_id(self):
        self.login_client(self.user1)
        response = self.client.post(self.url, {'backpack_id': '2137'})
        self.status_check(response, 404)

    def test_yours_shared(self):
        backpack = Backpack.objects.create(profile=self.user1.profile, shared=True)
        self.login_client(self.user1)
        response = self.client.post(self.url, {'backpack_id': backpack.id})
        self.status_check(response, 201)

    def test_yours_not_shared(self):
        backpack = Backpack.objects.create(profile=self.user1.profile, shared=False)
        self.login_client(self.user1)
        response = self.client.post(self.url, {'backpack_id': backpack.id})
        self.status_check(response, 201)

    def test_others_shared(self):
        backpack = Backpack.objects.create(profile=self.user2.profile, shared=True)
        self.login_client(self.user1)
        response = self.client.post(self.url, {'backpack_id': backpack.id})
        self.status_check(response, 201)

    def test_others_not_shared(self):
        backpack = Backpack.objects.create(profile=self.user2.profile, shared=False)
        self.login_client(self.user1)
        response = self.client.post(self.url, {'backpack_id': backpack.id})
        self.status_check(response, 403)

        #  TODO: test if copying backpack works correctly


class ImportFromLpViewTestCase(DRFTesterCase):
    url = '/api/import_from_lp'

    def test_unauthorized_request(self):
        response = self.client.post(self.url)
        self.status_check(response, 403)

    def test_url_missing(self):
        self.login_client(self.user1)
        response = self.client.post(self.url)
        self.status_check(response, 400)

    def test_invalid_url(self):
        self.login_client(self.user1)
        response = self.client.post(self.url, {'url': 'https://lighterpack.com/r/badurl'})
        self.status_check(response, 404)

    def test_valid_request(self):
        self.login_client(self.user1)
        response = self.client.post(self.url, {'url': 'https://lighterpack.com/r/ttdjjm'})
        self.status_check(response, 201)
        new_backpack = Backpack.objects.get(profile=self.user1.profile)
        self.assertEqual(new_backpack.name, 'for testing hikegear.pl')
        self.assertEqual(new_backpack.description, 'test description')

        #  TODO: test lpscraper functions and backpack data importing correctly


class PrivateGearViewTestCase(DRFTesterCase):
    url = '/api/private_gear'

    def test_unauthorized_request(self):
        response = self.client.patch(self.url)
        self.status_check(response, 403)

    def test_private_gear_missing(self):
        self.login_client(self.user1)
        response = self.client.patch(self.url)
        self.status_check(response, 400)

    def test_valid_request(self):
        self.login_client(self.user1)
        response = self.client.patch(self.url, {'private_gear': json.dumps([{'items': [1, 2, 3]}])})
        self.status_check(response, 200)
        self.check_response_fields(response.json(), ['private_gear'])


class InitialViewTestCase(DRFTesterCase):
    url = '/api/initial'
    response_fields = ['backpacks', 'private_gear', 'categories', 'brands', 'user_id']

    def test_unauthorized_get_method(self):
        response = self.client.get(self.url)
        self.status_check(response, 403)

    def test_authorized_valid_get_request(self):
        self.login_client(self.user1)
        response = self.client.get(self.url)
        self.status_check(response, 200)
        self.check_response_fields(response.json())


class BackPackViewSetTestCase(DRFTesterCase):
    url = '/api/backpacks'
    name = 'backpack name'
    description = 'backpack description'
    list = {'type': 'category'}
    data = {'name': name, 'description': description, 'list': list}
    response_fields = ['created', 'updated', 'profile', 'description', 'name', 'list', 'id', 'is_owner', 'shared']

    def test_unauthorized_valid_get_request(self):
        backpack = Backpack.objects.create(profile=self.user1.profile)
        response = self.client.get(self.url + '/' + str(backpack.id))
        self.status_check(response, 403)

    def test_authorized_valid_get_request_of_yours_shared_backpack(self):
        backpack = Backpack.objects.create(profile=self.user1.profile, shared=True)
        self.get_request(self.user1, 200, backpack)

    def test_authorized_valid_get_request_of_yours_not_shared_backpack(self):
        backpack = Backpack.objects.create(profile=self.user1.profile)
        self.get_request(self.user1, 200, backpack)

    def test_authorized_valid_get_request_of_others_shared_backpack(self):
        backpack = Backpack.objects.create(profile=self.user2.profile, shared=True)
        self.get_request(self.user1, 200, backpack)

    def test_authorized_valid_get_request_of_others_not_shared_backpack(self):
        backpack = Backpack.objects.create(profile=self.user2.profile)
        self.get_request(self.user1, 403, backpack)

    def get_request(self, logged_user, expected_status, backpack):
        self.login_client(logged_user)
        response = self.client.get(self.url + '/' + str(backpack.id))
        self.status_check(response, expected_status)
        if expected_status == 200:
            json = response.json()
            self.check_response_fields(json)
            self.assertEqual(Backpack.objects.get(profile=json['profile'], id=json['id'], list=json['list']),
                             backpack)

    def test_invalid_get_request(self):
        self.login_client(self.user1)
        backpack = Backpack.objects.create(profile=self.user1.profile)
        response = self.client.get(self.url + '/' + str(backpack.id + 1))
        self.status_check(response, 404)

    def test_unauthorized_valid_post_request(self):
        request = self.client.post(self.url, {'name': self.name, 'list': self.list}, format='json')
        self.status_check(request, 403)

    def test_authorized_valid_post_request(self):
        self.login_client(self.user1)
        request = self.client.post(self.url, {'name': self.name, 'list': self.list}, format='json')
        self.status_check(request, 201)
        json = request.json()
        self.check_response_fields(json)
        self.assertTrue(Backpack.objects.get(name=self.name, id=json['id'], list=self.list, profile=self.user1.profile))

    def test_unauthorized_valid_patch_request(self):
        request = self.client.patch(self.url, {'name': self.name, 'list': self.list}, format='json')
        self.status_check(request, 403)

    def test_authorized_valid_patch_request_of_yours_data(self):
        backpack = Backpack.objects.create(profile=self.user1.profile)
        self.login_client(self.user1)
        request = self.client.patch(self.url + '/' + str(backpack.id), self.data, format='json')
        self.status_check(request, 200)
        json = request.json()
        self.check_response_fields(json)
        self.assertTrue(Backpack.objects.get(name=self.name, id=backpack.id, list=self.list, profile=backpack.profile,
                                             description=self.description))

    def test_authorized_valid_patch_request_of_others_data(self):
        backpack = Backpack.objects.create(profile=self.user2.profile)
        self.login_client(self.user1)
        request = self.client.patch(self.url + '/' + str(backpack.id), self.data, format='json')
        self.status_check(request, 403)

    def test_unauthorized_valid_delete_request(self):
        backpack = Backpack.objects.create(profile=self.user1.profile)
        request = self.client.delete(self.url + '/' + str(backpack.id))
        self.status_check(request, 403)

    def test_authorized_valid_delete_request_of_yours_data(self):
        backpack = Backpack.objects.create(profile=self.user1.profile)
        self.login_client(self.user1)
        request = self.client.delete(self.url + '/' + str(backpack.id))
        self.status_check(request, 204)
        self.assertFalse(Backpack.objects.filter(id=backpack.id, profile=backpack.profile))

    def test_authorized_valid_delete_request_of_others_data(self):
        backpack = Backpack.objects.create(profile=self.user1.profile)
        self.login_client(self.user2)
        request = self.client.delete(self.url + '/' + str(backpack.id))
        self.status_check(request, 403)


class TestUserViewSetResetPasswordAction(DRFTesterCase):
    url = '/api/users/reset_password'

    @classmethod
    def moreSetUpTestTestData(cls):
        cls.uidb64 = urlsafe_base64_encode(force_bytes(cls.user1.id))
        cls.token = default_token_generator.make_token(cls.user1)

    def test_password_missing(self):
        response = self.client.post(self.url, {'uidb64': self.uidb64, 'token': self.token})
        self.status_check(response, 400)

    def test_uidb64_missing(self):
        response = self.client.post(self.url, {'uidb64': self.uidb64, 'password': 'new_password'})
        self.status_check(response, 400)

    def test_token_missing(self):
        response = self.client.post(self.url, {'password': 'new_password', 'token': self.token})
        self.status_check(response, 400)

    def test_invalid_uidb64(self):
        wrong_uidb64 = urlsafe_base64_encode(force_bytes(2137))
        response = self.client.post(self.url, {'uidb64': wrong_uidb64, 'token': self.token, 'password': 'new_password'})
        self.status_check(response, 404)

    def test_invalid_password(self):
        response = self.client.post(self.url, {'uidb64': self.uidb64, 'token': self.token, 'password': '1234'})
        self.status_check(response, 400)

    def test_expired_token(self):
        generator = default_token_generator
        expired_token = generator._make_token_with_timestamp(self.user1, generator._num_seconds(
            generator._now()) - settings.PASSWORD_RESET_TIMEOUT - 10)
        response = self.client.post(self.url, {'uidb64': self.uidb64, 'token': expired_token, 'password': 'password'})
        self.status_check(response, 410)

    def test_valid_request(self):
        response = self.client.post(self.url, {'uidb64': self.uidb64, 'token': self.token, 'password': 'new_password'})
        self.status_check(response, 200)
        self.assertTrue(response.cookies['sessionid'])


class TestUserViewSetResetPasswordStartAction(DRFTesterCase):
    url = '/api/users/reset_password_start'

    def test_email_missing(self):
        response = self.client.post(self.url)
        self.status_check(response, 400)

    def test_nonexistent_user(self):
        response = self.client.post(self.url, {'email': 'nonexistent@email.com'})
        self.status_check(response, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_valid_request(self):
        response = self.client.post(self.url, {'email': self.user1data['email']})
        self.status_check(response, 200)
        self.assertEqual(len(mail.outbox), 1)

    def test_inactive_user(self):
        self.user1.is_active = False
        self.user1.save()
        response = self.client.post(self.url, {'email': self.user1data['email']})
        self.status_check(response, 200)
        self.assertEqual(len(mail.outbox), 0)


class TestUserViewSetChangePasswordAction(DRFTesterCase):
    url = '/api/users/change_password'
    valid_new_password = '1k2j3b4j'

    def test_unauthorized_valid_request(self):
        response = self.client.patch(self.url, {'old_password': self.user1data['password'],
                                                'new_password': self.valid_new_password})
        self.status_check(response, 403)

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
    url = '/api/users'
    new_user_data = {'email': 'new_user@email.com', 'password': 'new_pass137'}
    response_fields = ['email', 'id']

    def test_unauthorized_valid_request(self):
        response = self.client.post(self.url, self.new_user_data)
        json = response.json()
        self.status_check(response, 201)
        self.check_response_fields(json)
        self.assertTrue(MyUser.objects.get(**json).check_password(self.new_user_data['password']))
        self.assertTrue(Profile.objects.get(user_id=json['id']))
        self.assertEqual(len(mail.outbox), 1)

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


class TestLoginView(DRFTesterCase):
    url = '/api/login'

    def test_email_missing(self):
        response = self.client.post(self.url, {'password': self.user1data['password']})
        self.status_check(response, 400)

    def test_password_missing(self):
        response = self.client.post(self.url, {'email': self.user1data['email']})
        self.status_check(response, 400)

    def test_email_and_password_missing(self):
        response = self.client.post(self.url)
        self.status_check(response, 400)

    def test_login(self):
        response = self.client.post(self.url, self.user1data)
        self.status_check(response, 200)
        self.assertTrue(response.cookies.get('sessionid'))

    def test_bad_wrong_password(self):
        response = self.client.post(self.url, {'email': self.user1data['email'], 'password': 'wrong password'})
        self.status_check(response, 401)

    def test_nonexistent_user(self):
        response = self.client.post(self.url, {'email': 'nonexists@email.com', 'password': 'random password'})
        self.status_check(response, 401)

    def test_non_activated_user(self):
        self.user1.is_active = False
        self.user1.save()
        response = self.client.post(self.url, self.user1data)
        self.status_check(response, 403)


class TestLogoutView(DRFTesterCase):
    url = '/api/logout'

    def test_unauthenticated_logout(self):
        response = self.client.post(self.url)
        self.status_check(response, 403)

    def test_authenticated_logout(self):
        self.login_client(self.user1)
        response = self.client.post(self.url)
        self.status_check(response, 200)
        response = self.client.post(self.url)
        self.status_check(response, 403)
