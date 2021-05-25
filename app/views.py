from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, TrigramSimilarity
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.shortcuts import redirect, render
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.mixins import DestroyModelMixin
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from openpyxl import load_workbook

import time

from .models import MyUser, Backpack, Category, Brand, Product
from .permissions import IsAuthenticatedOrPostOnly, BackpackPermission
from .serializers import UserSerializer, BackpackSerializer, BackpackReadSerializer, PrivateGearSerializer, \
    CategorySerializer, BrandSerializer, ProductSerializer
from .emails import send_account_activation_email, send_password_reset_email, force_text, default_token_generator, \
    urlsafe_base64_decode
from .lpscraper import import_backpack_from_lp
from . import constants
from hikegear_backend.settings import FRONTEND_URL, PASSWORD_RESET_TIMEOUT, DEBUG


class SearchForProductView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get(request):
        requested_query = request.query_params.get('query')
        if requested_query is not None:
            products = Product.objects.all()
            subcategory_id = request.query_params.get('subcategory_id')
            if subcategory_id:
                products = products.filter(subcategory=subcategory_id)
            brand_id = request.query_params.get('brand_id')
            if brand_id:
                products = products.filter(brand=brand_id)
            sex = request.query_params.get('sex')
            if sex:
                products = products.filter(sex=sex)
            results_by_name = products.annotate(similarity=TrigramSimilarity('name', requested_query)).filter(
                similarity__gt=0.1).order_by('-similarity')
            # for r in results_by_name:
            #     print(r.name)
            #     print(r.similarity)
            return Response(ProductSerializer(results_by_name, many=True).data)
        else:
            return Response('you must provide query for search', status=status.HTTP_400_BAD_REQUEST)


class ImportFromExcelView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @staticmethod
    def new_my_gear_cat_id(private_gear):
        ids = []
        for cat in private_gear:
            ids.append(cat['id'])
        for x in range(1000):
            if x not in ids:
                return x
        return False

    def post(self, request):
        try:
            wb = load_workbook(request.data['excel'])
        except KeyError:
            return Response('bad format', status=status.HTTP_400_BAD_REQUEST)  # TODO: bad format ? wtf
        data = wb.active['A:C']
        if len(data[0]) > 2000:
            return Response({'info': 'too many items'}, status=status.HTTP_400_BAD_REQUEST)
        elif len(data[0]) == 0:
            return Response({'info': 'no items supplied'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            old_list = request.user.profile.private_gear
            items_ids = []
            for cat in old_list:
                for item in cat['items']:
                    items_ids.append(item['id'])
            new_categories = [
                {'name': 'importowane z pliku excel', 'items': [], 'id': self.new_my_gear_cat_id(old_list)}]
            for (name, description, weight) in zip(data[0], data[1], data[2]):
                if name.value == 'kategoria':
                    new_id = self.new_my_gear_cat_id(old_list + new_categories)
                    if not new_id:
                        return Response("cant find new id for category", status=status.HTTP_400_BAD_REQUEST)
                    new_categories.append({'name': description.value, 'items': [], 'id': new_id})
                else:
                    if name.value or description.value:
                        final_id = 0
                        for x in range(10000):
                            if x not in items_ids:
                                items_ids.append(x)
                                final_id = x
                                break
                        final_name = ""
                        final_description = ""
                        final_weight = 0
                        if isinstance(name.value, (str, int)):
                            final_name = name.value[:constants.item_max_name_len]
                        if isinstance(description.value, (str, int)):
                            final_description = description.value[:constants.item_max_description_len]
                        if isinstance(weight.value, int):
                            if weight.value <= constants.item_max_weight:
                                final_weight = weight.value
                            else:
                                final_weight = constants.item_max_weight
                        new_categories[-1]['items'].append(
                            {'name': final_name, 'description': final_description, 'weight': final_weight,
                             "id": final_id})
            data = {'private_gear': old_list + new_categories}
            serializer = PrivateGearSerializer(request.user.profile, data=data)
            serializer.is_valid(raise_exception=True)
            return Response(PrivateGearSerializer(serializer.save()).data)


class ImportFromHgView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def post(request):
        try:
            backpack_id = request.data['backpack_id']
        except KeyError:
            msg = "you must provide 'backpack_id' of hikegear.pl backpack"
            return Response({'info': msg}, status=status.HTTP_400_BAD_REQUEST)
        try:
            backpack = Backpack.objects.get(id=backpack_id)
        except Backpack.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if not backpack.shared and request.user.profile != backpack.profile:
            return Response({"info": 'this backpack is not shared'}, status=status.HTTP_403_FORBIDDEN)
        new_backpack = Backpack.objects.create(profile=request.user.profile, name=backpack.name,
                                               description=backpack.description, list=backpack.list)
        serializer = BackpackReadSerializer(new_backpack, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ImportFromLpView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def post(request):
        try:
            url = request.data['url']
        except KeyError:
            msg = "you must provide 'url' of lighterpack backpack"
            return Response({'info': msg}, status=status.HTTP_400_BAD_REQUEST)
        json_data = import_backpack_from_lp(url)
        if not json_data:
            raise NotFound
        json_data['profile'] = request.user.profile
        serializer = BackpackSerializer(data=json_data)
        serializer.is_valid(raise_exception=True)
        return Response(BackpackReadSerializer(serializer.save(), context={'request': request}).data,
                        status=status.HTTP_201_CREATED)


class PrivateGearView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def patch(request):
        serializer = PrivateGearSerializer(request.user.profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(PrivateGearSerializer(serializer.save()).data)


class InitialView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get(request):
        backpacks = Backpack.objects.filter(profile=request.user.profile).order_by('-updated')
        backpacks_serializer = BackpackReadSerializer(backpacks, many=True, context={'request': request})
        private_gear_serializer = PrivateGearSerializer(request.user.profile)
        response = private_gear_serializer.data
        response['backpacks'] = backpacks_serializer.data
        response['categories'] = CategorySerializer(Category.objects.all(), many=True).data
        response['brands'] = BrandSerializer(Brand.objects.all().order_by('name'), many=True).data
        return Response(response)


class BackpackViewSet(GenericViewSet, DestroyModelMixin):
    queryset = Backpack.objects.all()
    permission_classes = [BackpackPermission]
    serializer_class = BackpackSerializer
    http_method_names = ['get', 'post', 'delete', 'patch']

    def retrieve(self, request, pk=None):
        return Response(BackpackReadSerializer(self.get_object(), context={'request': request}).data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(BackpackReadSerializer(serializer.save(), context={'request': request}).data,
                        status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        if DEBUG:
            time.sleep(.7)
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        return Response(BackpackReadSerializer(serializer.save(), context={'request': request}).data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class UserViewSet(GenericViewSet):
    permission_classes = [IsAuthenticatedOrPostOnly]
    serializer_class = UserSerializer
    queryset = MyUser.objects.all()
    http_method_names = ['post', 'patch']

    def create(self, request, *args, **kwargs):
        try:
            email = request.data['email']
            user = MyUser.objects.get(email=email)
            seconds_from_joined = (timezone.now() - user.date_joined).seconds
            if not user.is_active and seconds_from_joined >= PASSWORD_RESET_TIMEOUT:
                user.delete()
        except (KeyError, MyUser.DoesNotExist):
            pass
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        send_account_activation_email(request, user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['patch'])
    def change_password(self, request):
        try:
            new_password = request.data['new_password']
            old_password = request.data['old_password']
            validate_password(new_password, request.user)
        except KeyError:
            msg = "You must provide 'old_password' and 'new_password'"
            return Response({'info': msg}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as msg:
            return Response({'info': msg}, status=status.HTTP_400_BAD_REQUEST)
        if authenticate(email=request.user.email, password=old_password):
            request.user.set_password(new_password)
            request.user.save()
            login(request, request.user)
            return Response()
        else:
            return Response({'info': 'provided wrong password!'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def reset_password_start(self, request):
        try:
            email = request.data['email']
        except KeyError:
            msg = 'You must provide email of user that password needs to be reset'
            return Response({'info': msg}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = MyUser.objects.get(email=email)
        except ObjectDoesNotExist:
            return Response()
        if not user.is_active:
            return Response()
        send_password_reset_email(request, user)
        return Response()

    @action(detail=False, methods=['post'])
    def reset_password(self, request):
        try:
            password = request.data['password']
        except KeyError:
            return Response({'info': 'You must provide password'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            uidb64 = request.data['uidb64']
        except KeyError:
            return Response({'info': 'You must provide uidb64'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = request.data['token']
        except KeyError:
            return Response({'info': 'You must provide token'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user_id = force_text(urlsafe_base64_decode(uidb64))
            user = MyUser.objects.get(pk=user_id)
        except MyUser.DoesNotExist:
            return Response('invalid uidb64', status=status.HTTP_404_NOT_FOUND)
        if default_token_generator.check_token(user, token):
            try:
                validate_password(password, user)
            except ValidationError as msg:
                return Response({'info': msg}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(password)
            user.save()
            login(request, user)
            return Response()
        else:
            return Response({'info': 'password reset token expired'}, status=status.HTTP_410_GONE)


class LoginView(APIView):
    @staticmethod
    def post(request):
        bad_credentials_response = Response({'info': "can not login with provided credentials"},
                                            status=status.HTTP_401_UNAUTHORIZED)
        try:
            email = request.data['email']
            password = request.data['password']
        except KeyError:
            msg = "you must provide 'email' and 'password'"
            return Response({'info': msg}, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            msg = "You are successfully logged in"
            return Response({'info': msg})
        else:
            try:
                user = MyUser.objects.get(email=email)
            except ObjectDoesNotExist:
                return bad_credentials_response
            else:
                if user.is_active is True:
                    return bad_credentials_response
                else:
                    return Response({'info': 'you have to verify your email and activate your account'},
                                    status=status.HTTP_403_FORBIDDEN)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def post(request):
        logout(request)
        return Response({'info': 'Your are logged out'})


def page_not_found_view(request, exception):
    return redirect(FRONTEND_URL + 'not_found')


def stats_view(request):
    users = MyUser.objects.all()
    backpacks = Backpack.objects.all()
    time_threshold24 = timezone.now() - timezone.timedelta(hours=24)
    time_threshold1 = timezone.now() - timezone.timedelta(hours=1)
    time_threshold10 = timezone.now() - timezone.timedelta(minutes=10)
    context = {
        'users': {
            'all': len(users),
            'last24h': len(users.filter(date_joined__gt=time_threshold24)),
            'last1h': len(users.filter(date_joined__gt=time_threshold1)),
            'last10min': len(users.filter(date_joined__gt=time_threshold10)),
        },
        'backpacks': {
            'all': len(backpacks),
            'last24h': len(backpacks.filter(created__gt=time_threshold24)),
            'last1h': len(backpacks.filter(created__gt=time_threshold1)),
            'last10min': len(backpacks.filter(created__gt=time_threshold10)),
        },
    }

    return render(request, 'stats.html', context)
