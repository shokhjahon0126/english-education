from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.utils import extend_schema

from .views import (
    ChangePasswordView,
    CustomTokenObtainPairView,
    UserViewSet,
)

router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')

# TokenRefreshView ni Auth tegi ostida ko'rsatish
DecoratedTokenRefreshView = extend_schema(
    tags=['Auth'],
    auth=[],
    description="Yangi access token olish uchun refresh tokenni yuborish."
)(TokenRefreshView)


urlpatterns = [
    # Auth endpoints
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', DecoratedTokenRefreshView.as_view(), name='token_refresh'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),

    # User CRUD endpoints (PUT taqiqlangan, faqat PATCH)
    path('', include(router.urls)),
]
