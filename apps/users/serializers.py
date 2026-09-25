from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User, Role


from django.db import connection


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Login uchun JWT serializer.
    Username yoki Phone orqali autentifikatsiya qilishni qo'llab-quvvatlaydi.
    Token bilan birga user ning id, role va joriy tenantning schema_name sini qaytaradi.
    """
    username_field = 'username'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Login maydoni sifatida username yoki phone kiritish mumkin
        self.fields['username'] = serializers.CharField(
            required=True,
            help_text="Username yoki telefon raqami (+998...)"
        )

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Token payloadiga id, role va schema_name ni qo'shamiz
        token['id'] = user.id
        token['role'] = user.role
        token['username'] = user.username
        token['schema_name'] = getattr(connection, 'schema_name', 'public')
        return token

    def validate(self, attrs):
        username_or_phone = attrs.get('username')
        password = attrs.get('password')

        user = None
        # Agar telefon raqam ko'rinishida bo'lsa yoki username topilmasa, phone bo'yicha qidiramiz
        if username_or_phone:
            user = User.objects.filter(username=username_or_phone).first()
            if not user:
                user = User.objects.filter(phone=username_or_phone).first()

        if user and user.check_password(password):
            if not user.is_active:
                raise serializers.ValidationError("Foydalanuvchi hisobi faol emas.")
            self.user = user
        else:
            raise serializers.ValidationError("Username/Telefon raqam yoki parol noto'g'ri kiritildi.")

        # Joriy so'rov kelgan tenant schemasini aniqlaymiz
        request = self.context.get('request')
        current_schema = None
        if request and hasattr(request, 'tenant') and request.tenant:
            current_schema = getattr(request.tenant, 'schema_name', None)
        if not current_schema:
            current_schema = getattr(connection, 'schema_name', 'public')

        refresh = self.get_token(self.user)
        # Tokenlar ichiga schema_name ni joylaymiz
        refresh['schema_name'] = current_schema
        refresh.access_token['schema_name'] = current_schema

        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'id': self.user.id,
            'role': self.user.role,
            'schema_name': current_schema,
            'username': self.user.username,
            'phone': str(self.user.phone) if self.user.phone else None,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
        }

        return data



class ChangePasswordSerializer(serializers.Serializer):
    """
    Parolni o'zgartirish uchun serializer.
    new_password va new_password_confirm talab qilinadi.
    Ixtiyoriy ravishda old_password ham tekshirilishi mumkin.
    """
    old_password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text="Eski parol (ixtiyoriy, agar kiritilsa tekshiriladi)"
    )
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Yangi parol"
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Yangi parolni tasdiqlash"
    )

    def validate(self, attrs):
        user = self.context['request'].user
        old_password = attrs.get('old_password')
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')

        # Agar eski parol kiritilgan bo'lsa, uning to'g'riligini tekshiramiz
        if old_password and not user.check_password(old_password):
            raise serializers.ValidationError({
                "old_password": "Eski parol noto'g'ri kiritildi."
            })

        # Yangi parollar bir-biriga mos kelishini tekshiramiz
        if new_password != new_password_confirm:
            raise serializers.ValidationError({
                "new_password_confirm": "Yangi kiritilgan parollar bir-biriga mos kelmadi."
            })

        # Django password validation
        validate_password(new_password, user=user)

        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Foydalanuvchilar ro'yxati va batafsil ma'lumotlarini ko'rish uchun serializer.
    """
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'phone',
            'first_name',
            'last_name',
            'email',
            'role',
            'is_active',
            'date_joined',
        ]
        read_only_fields = ['id', 'date_joined']


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Foydalanuvchi yaratish uchun serializer.
    - SuperAdmin rolini hech qaysi user create qila olmaydi (faqat admin panel).
    - Admin faqat Teacher va Student rollarini yarata oladi.
    - SuperAdmin esa Admin, Teacher, Student yarata oladi (lekin SuperAdmin emas).
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    role = serializers.ChoiceField(
        choices=Role.choices,
        default=Role.STUDENT,
        help_text="Foydalanuvchi roli (SUPER_ADMIN rolini yaratish mumkin emas)"
    )

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'phone',
            'first_name',
            'last_name',
            'email',
            'role',
            'password',
        ]
        read_only_fields = ['id']

    def validate_role(self, value):
        # 1. Superadmin rolini hech kim API orqali create qila olmaydi
        if value == Role.SUPER_ADMIN:
            raise serializers.ValidationError(
                "SUPER_ADMIN rolini yaratish taqiqlangan! Superadmin faqat Django admin panel orqali yaratiladi."
            )
        return value

    def validate(self, attrs):
        request = self.context.get('request')
        current_user = request.user if request else None
        target_role = attrs.get('role', Role.STUDENT)

        if current_user and current_user.is_authenticated:
            # Agar yaratayotgan user ADMIN bo'lsa:
            # U faqat TEACHER va STUDENT yarata oladi! ADMIN yoki SUPER_ADMIN yarata olmaydi!
            if current_user.role == Role.ADMIN:
                if target_role not in [Role.TEACHER, Role.STUDENT]:
                    raise serializers.ValidationError({
                        "role": "Admin rolidagi foydalanuvchi faqat Teacher va Student rollaridagi foydalanuvchilarni yaratish huquqiga ega."
                    })
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Foydalanuvchini faqat PATCH orqali qisman tahrirlash uchun serializer.
    """
    role = serializers.ChoiceField(
        choices=Role.choices,
        required=False,
        help_text="Foydalanuvchi roli"
    )

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'phone',
            'first_name',
            'last_name',
            'email',
            'role',
            'is_active',
        ]
        read_only_fields = ['id', 'username']

    def validate_role(self, value):
        # Hech kim rolni SUPER_ADMIN ga o'zgartira olmaydi
        if value == Role.SUPER_ADMIN:
            raise serializers.ValidationError(
                "Rolni SUPER_ADMIN ga o'zgartirish taqiqlangan!"
            )
        return value

    def validate(self, attrs):
        request = self.context.get('request')
        current_user = request.user if request else None
        new_role = attrs.get('role')

        if new_role and current_user:
            # Oddiy foydalanuvchi (Teacher yoki Student) o'zining yoki boshqaning rolini o'zgartira olmaydi
            if not current_user.is_admin_user:
                raise serializers.ValidationError({
                    "role": "Sizda foydalanuvchi rolini o'zgartirish huquqi yo'q."
                })

            # Admin faqat TEACHER yoki STUDENT qilib belgilashi mumkin
            if current_user.role == Role.ADMIN:
                if new_role not in [Role.TEACHER, Role.STUDENT]:
                    raise serializers.ValidationError({
                        "role": "Admin faqat Teacher yoki Student roliga o'zgartirishi mumkin."
                    })

        return attrs
