from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, BackpackViewSet, InitialView, LoginView, LogoutView, PrivateGearView, ImportFromLpView

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'backpacks', BackpackViewSet)

# from django.views.decorators.csrf import ensure_csrf_cookie

urlpatterns = [
    path('initial', InitialView.as_view(), name='initial_view'),
    path('login', LoginView.as_view(), name='login_view'),
    path('logout', LogoutView.as_view(), name='logout_view'),
    path('private_gear', PrivateGearView.as_view(), name='private_gear'),
    path('import_from_lp', ImportFromLpView.as_view(), name='import_from_lp'),
]
urlpatterns += router.urls
