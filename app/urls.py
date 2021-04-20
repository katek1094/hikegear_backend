from django.urls import path
from rest_framework.routers import SimpleRouter
from .views import UserViewSet, BackpackViewSet, InitialView, LoginView, LogoutView, PrivateGearView, \
    ImportFromLpView, ImportFromHgView, ImportFromExcel

router = SimpleRouter(trailing_slash=False)
router.register(r'users', UserViewSet)
router.register(r'backpacks', BackpackViewSet)

urlpatterns = [
    path('initial', InitialView.as_view(), name='initial_view'),
    path('login', LoginView.as_view(), name='login_view'),
    path('logout', LogoutView.as_view(), name='logout_view'),
    path('private_gear', PrivateGearView.as_view(), name='private_gear'),
    path('import_from_lp', ImportFromLpView.as_view(), name='import_from_lp'),
    path('import_from_hg', ImportFromHgView.as_view(), name='import_from_hg'),
    path('import_from_excel', ImportFromExcel.as_view(), name='import_from_excel'),
]
urlpatterns += router.urls
