from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, ObtainAuthTokenView, BackpackViewSet, InitialView

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'backpacks', BackpackViewSet)

urlpatterns = [
    path('obtain_token', ObtainAuthTokenView.as_view(), name='obtain_token'),
    path('initial', InitialView.as_view(), name='initial_view'),
]
urlpatterns += router.urls
