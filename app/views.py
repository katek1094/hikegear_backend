from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.contrib.postgres.search import TrigramSimilarity
from django.core.exceptions import ValidationError as DjangoValidationError, ObjectDoesNotExist
from django.shortcuts import redirect, render
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError, PermissionDenied
from rest_framework.mixins import DestroyModelMixin, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from .models import MyUser, Backpack, Category, Brand, Product, Review
from .permissions import IsAuthenticatedOrPostOnly, BackpackPermission, IsAuthor
from .serializers import UserSerializer, BackpackSerializer, PrivateGearSerializer, \
    CategorySerializer, BrandSerializer, ProductSerializer, ReviewSerializer
from .functions.emails import send_account_activation_email, send_password_reset_email, force_text, \
    default_token_generator, urlsafe_base64_decode
from .functions.lpscraper import import_backpack_from_lp
from .functions.excel_import import scrape_data_from_excel
from hikegear_backend.settings import FRONTEND_URL, PASSWORD_RESET_TIMEOUT


class BrandViewSet(GenericViewSet, CreateModelMixin):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsAuthenticated]


class ReviewViewSet(GenericViewSet, CreateModelMixin, UpdateModelMixin, DestroyModelMixin):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated, IsAuthor]


class ProductViewSet(GenericViewSet, CreateModelMixin, UpdateModelMixin, RetrieveModelMixin):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]


class SearchForProductView(APIView):  # TODO: write tests for this view
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get(request):
        requested_query = request.query_params.get('query')
        print('one')
        if requested_query is not None:
            products = Product.objects.all()
            subcategory_id = request.query_params.get('subcategory_id')
            category_id = request.query_params.get('category_id')
            print("two")
            if subcategory_id:
                products = products.filter(subcategory=subcategory_id)
            elif category_id:
                products = products.filter(subcategory__category=category_id)
            brand_id = request.query_params.get('brand_id')
            if brand_id:
                products = products.filter(brand=brand_id)
            print('three')
            results_by_name = products.annotate(similarity=TrigramSimilarity('name', requested_query)).filter(
                similarity__gt=0.06).order_by('-similarity')
            print('four')
            return Response(ProductSerializer(results_by_name, many=True, fields=(
                'id', 'full_name', 'brand', 'subcategory', 'reviews_amount')).data)
        else:
            raise ValidationError({'query': 'you must provide "query" to search for'})


class ImportFromExcelView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @staticmethod
    def post(request):
        try:
            excel_file = request.data['excel']
        except KeyError:
            raise ValidationError({'excel': "you must provide 'excel' file in request data"})
        data = scrape_data_from_excel(excel_file, request.user.profile.private_gear)
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
            raise ValidationError({'backpack_id': "you must provide 'backpack_id' of hikegear.pl backpack"})
        try:
            backpack = Backpack.objects.get(id=backpack_id)
        except Backpack.DoesNotExist:
            raise NotFound
        if not backpack.shared and request.user.profile != backpack.profile:
            raise PermissionDenied('this backpack is not shared')
        new_backpack = Backpack.objects.create(profile=request.user.profile, name=backpack.name,
                                               description=backpack.description, list=backpack.list)
        serializer = BackpackSerializer(new_backpack, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ImportFromLpView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def post(request):
        try:
            url = request.data['url']
        except KeyError:
            raise ValidationError({'url': "you must provide 'url' of lighterpack backpack"})
        json_data = import_backpack_from_lp(url)
        if not json_data:
            raise NotFound
        json_data['profile'] = request.user.profile
        serializer = BackpackSerializer(data=json_data)
        serializer.is_valid(raise_exception=True)
        return Response(BackpackSerializer(serializer.save(), context={'request': request}).data,
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
        backpacks_serializer = BackpackSerializer(backpacks, many=True, context={'request': request})
        private_gear_serializer = PrivateGearSerializer(request.user.profile)
        response = private_gear_serializer.data
        response['backpacks'] = backpacks_serializer.data
        response['categories'] = CategorySerializer(Category.objects.all(), many=True).data
        response['brands'] = BrandSerializer(Brand.objects.all().order_by('name'), many=True).data
        response['user_id'] = request.user.id
        return Response(response)


class BackpackViewSet(GenericViewSet, DestroyModelMixin, RetrieveModelMixin, CreateModelMixin, UpdateModelMixin):
    queryset = Backpack.objects.all()
    permission_classes = [BackpackPermission]
    serializer_class = BackpackSerializer
    http_method_names = ['get', 'post', 'delete', 'patch']


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
            raise ValidationError("You must provide 'old_password' and 'new_password'")
        except DjangoValidationError as err:
        except DjangoValidationError as err:
            raise ValidationError({'new_password': err.messages[0]})
        if authenticate(email=request.user.email, password=old_password):
            request.user.set_password(new_password)
            request.user.save()
            login(request, request.user)
            return Response()
        else:
            raise ValidationError({'password': 'provided wrong password'})

    @action(detail=False, methods=['post'])
    def reset_password_start(self, request):
        try:
            email = request.data['email']
        except KeyError:
            raise ValidationError({'email': 'You must provide email of user that password needs to be reset'})
        try:
            user = MyUser.objects.get(email=email)
        except ObjectDoesNotExist:
            return Response()
        if not user.is_active:
            return Response()
        send_password_reset_email(user)
        return Response()

    @action(detail=False, methods=['post'])
    def reset_password(self, request):
        try:
            password = request.data['password']
        except KeyError:
            raise ValidationError({'password': 'You must provide password'})
        try:
            uidb64 = request.data['uidb64']
        except KeyError:
            raise ValidationError({'uidb64': 'You must provide uidb64'})
        try:
            token = request.data['token']
        except KeyError:
            raise ValidationError({'token': 'You must provide token'})
        try:
            user_id = force_text(urlsafe_base64_decode(uidb64))
            user = MyUser.objects.get(pk=user_id)
        except MyUser.DoesNotExist:
            raise NotFound({'uidb64': 'invalid uidb64'})
        if default_token_generator.check_token(user, token):
            try:
                validate_password(password, user)
            except DjangoValidationError as err:
                raise ValidationError({'password': err.messages[0]})
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
