from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, BackpackViewSet, InitialView, LoginView, LogoutView
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'backpacks', BackpackViewSet)

urlpatterns = [
    path('initial', InitialView.as_view(), name='initial_view'),
    path('login', LoginView.as_view(), name='login_view'),
    path('logout', LogoutView.as_view(), name='logout_view'),
]
urlpatterns += router.urls
