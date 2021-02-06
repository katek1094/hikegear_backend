from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from .models import MyUser, Backpack
from .permissions import IsAuthenticatedOrPostOnly, IsOwnerPermission
from .serializers import MyTokenSerializer, UserSerializer, BackpackSerializer, BackpackReadSerializer


class InitialView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get(request):
        backpacks = Backpack.objects.filter(profile=request.user.profile).order_by('-updated')
        serializer = BackpackReadSerializer(backpacks, many=True)
        return Response({'backpacks': serializer.data})


class BackpackViewSet(GenericViewSet, DestroyModelMixin):
    queryset = Backpack.objects.all()
    permission_classes = [IsAuthenticated, IsOwnerPermission]
    serializer_class = BackpackSerializer
    http_method_names = ['get', 'post', 'delete', 'patch']

    @staticmethod
    def retrieve(request, pk=None):
        backpack = get_object_or_404(Backpack, id=pk)
        return Response(BackpackReadSerializer(backpack).data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return Response(BackpackReadSerializer(serializer.save()).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        return Response(BackpackReadSerializer(serializer.save()).data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


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


class ObtainAuthTokenView(ObtainAuthToken):
    serializer_class = MyTokenSerializer
