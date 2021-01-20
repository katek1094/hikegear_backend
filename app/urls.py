from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, MyObtainAuthToken


router = DefaultRouter()
router.register(r'users', UserViewSet)


urlpatterns = [
    path('obtain_token', MyObtainAuthToken.as_view(), name='obtain_token'),
]
urlpatterns += router.urls
