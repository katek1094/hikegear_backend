from django.urls import path
from rest_framework.routers import SimpleRouter
from .views import UserViewSet, BackpackViewSet, InitialView, LoginView, LogoutView, PrivateGearView, \
    ImportFromLpView, ImportFromHgView, ImportFromExcelView, SearchForProductView, ProductViewSet, ReviewViewSet, \
    BrandViewSet

router = SimpleRouter(trailing_slash=False)
router.register(r'users', UserViewSet)
router.register(r'backpacks', BackpackViewSet)
router.register(r'products', ProductViewSet)
router.register(r'reviews', ReviewViewSet)
router.register(r'brands', BrandViewSet)

urlpatterns = [
    path('initial', InitialView.as_view(), name='initial_view'),
    path('login', LoginView.as_view(), name='login_view'),
    path('logout', LogoutView.as_view(), name='logout_view'),
    path('private_gear', PrivateGearView.as_view(), name='private_gear'),
    path('import_from_lp', ImportFromLpView.as_view(), name='import_from_lp'),
    path('import_from_hg', ImportFromHgView.as_view(), name='import_from_hg'),
    path('import_from_excel', ImportFromExcelView.as_view(), name='import_from_excel'),
    path('search_for_product', SearchForProductView.as_view(), name='search_for_product'),
]
urlpatterns += router.urls
