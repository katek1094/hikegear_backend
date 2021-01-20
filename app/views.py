from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework import parsers, renderers
from rest_framework.schemas import coreapi as coreapi_schema
from rest_framework.compat import coreapi, coreschema
from rest_framework.schemas import ManualSchema
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.decorators import action
from rest_framework import status
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .serializers import MyTokenSerializer, UserSerializer
from .models import MyUser
from.permissions import IsAuthenticatedOrPostOnly


class UserViewSet(GenericViewSet, CreateModelMixin):
    permission_classes = [IsAuthenticatedOrPostOnly]
    serializer_class = UserSerializer
    queryset = MyUser.objects.all()
    http_method_names = ['post', 'patch']

    @action(detail=False, methods=['patch'])
    def change_password(self, request):
        try:
            new_password = request.data['new_password']
            old_password = request.data['old_password']
            validate_password(new_password, request.user)
        except KeyError:
            msg = "you must provide 'old_password' and 'new_password'"
            return Response({'info': msg}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as msg:
            return Response({'info': msg}, status=status.HTTP_400_BAD_REQUEST)
        if authenticate(email=request.user.email, password=old_password):
            request.user.set_password(new_password)
            request.user.save()
            return Response()
        else:
            return Response({'info': 'provided wrong password!'}, status=status.HTTP_400_BAD_REQUEST)


class MyObtainAuthToken(ObtainAuthToken):
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = MyTokenSerializer

    if coreapi_schema.is_enabled():
        schema = ManualSchema(
            fields=[coreapi.Field(name='email', required=True, location='form',
                                  schema=coreschema.String(title='email',
                                                           description='Valid email for authentication'),),
                    coreapi.Field(name='password', required=True, location='form',
                                  schema=coreschema.String(title='password',
                                                           description='Valid password for authentication', ), ), ],
            encoding='application/json',)

    def get_serializer_context(self):
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    def get_serializer(self, *args, **kwargs):
        kwargs['context'] = self.get_serializer_context()
        return self.serializer_class(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})
