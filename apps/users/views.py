from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import User, Role
from .permissions import IsAdminOrSuperAdmin, IsUserOwnerOrAdmin
from .serializers import (
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


@extend_schema(tags=['Auth'], auth=[])
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Foydalanuvchi login qilishi uchun API.
    Username yoki Phone orqali ishlaydi.
    Natijada access, refresh tokenlar va userning id, role lari qaytadi.
    """
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema(tags=['Auth'])
class ChangePasswordView(APIView):
    """
    Foydalanuvchi parolini o'zgartirish uchun API.
    Faqat autentifikatsiyadan o'tgan foydalanuvchilar uchun.
    new_password va new_password_confirm talab qilinadi.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ChangePasswordSerializer,
        responses={200: dict},
        description="Foydalanuvchi parolini yangilash (new_password va new_password_confirm orqali)."
    )
    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Parol muvaffaqiyatli o'zgartirildi."},
            status=status.HTTP_200_OK
        )


@extend_schema_view(
    list=extend_schema(description="Barcha foydalanuvchilar ro'yxati (faqat Admin va SuperAdmin uchun).", tags=['Users']),
    retrieve=extend_schema(description="Bitta foydalanuvchini ko'rish (faqat o'zi yoki Admin/SuperAdmin).", tags=['Users']),
    create=extend_schema(description="Yangi foydalanuvchi yaratish (SuperAdmin yaratish taqiqlangan; Admin faqat Teacher va Student yarata oladi).", tags=['Users']),
    partial_update=extend_schema(description="Foydalanuvchi ma'lumotlarini qisman yangilash (PATCH).", tags=['Users']),
    destroy=extend_schema(description="Foydalanuvchini o'chirish (faqat Admin va SuperAdmin).", tags=['Users']),
)
class UserViewSet(viewsets.ModelViewSet):
    """
    Foydalanuvchilarni boshqarish uchun ViewSet.
    DIQQAT: PUT metodi butunlay o'chirilgan, faqat PATCH ishlatiladi!
    """
    queryset = User.objects.all().order_by('-id')
    # PUT metodini chiqarib tashlaymiz, faqat PATCH ruxsat etiladi:
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_permissions(self):
        if self.action in ['create', 'list']:
            return [IsAdminOrSuperAdmin()]
        elif self.action in ['retrieve', 'partial_update', 'destroy']:
            return [IsUserOwnerOrAdmin()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'partial_update':
            return UserUpdateSerializer
        return UserSerializer

    @extend_schema(
        tags=['Users'],
        description="Hozirgi tizimga kirgan foydalanuvchi o'z profilini ko'rish yoki PATCH orqali tahrirlash endpointi."
    )
    @action(
        detail=False,
        methods=['get', 'patch'],
        permission_classes=[IsAuthenticated],
        url_path='me'
    )
    def me(self, request):
        user = request.user
        if request.method == 'GET':
            serializer = UserSerializer(user)
            return Response(serializer.data)
        elif request.method == 'PATCH':
            serializer = UserUpdateSerializer(
                user,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(UserSerializer(user).data)
