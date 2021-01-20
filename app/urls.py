from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, MyObtainAuthToken, BackpackViewSet


router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'backpacks', BackpackViewSet)


urlpatterns = [
    path('obtain_token', MyObtainAuthToken.as_view(), name='obtain_token'),
]
urlpatterns += router.urls
