from rest_framework import permissions
from .models import Role


class IsSuperAdmin(permissions.BasePermission):
    """
    Faqat SuperAdmin yoki is_superuser bo'lgan foydalanuvchilarga ruxsat beradi.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role == Role.SUPER_ADMIN or request.user.is_superuser)
        )


class IsAdminOrSuperAdmin(permissions.BasePermission):
    """
    Admin yoki SuperAdmin bo'lgan foydalanuvchilarga ruxsat beradi.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role in [Role.ADMIN, Role.SUPER_ADMIN] or request.user.is_superuser)
        )


class IsUserOwnerOrAdmin(permissions.BasePermission):
    """
    Foydalanuvchilar va ularning obyektlari ustidan huquqlarni boshqarish:
    - SuperAdmin: Barcha foydalanuvchilar ustidan to'liq huquqqa ega.
    - Admin: Ro'yxatni ko'ra oladi, lekin tahrirlash (PATCH) va o'chirish (DELETE) amallarini
             FAQAT Teacher va Studentlar ustida bajara oladi (o'zidan boshqa Admin yoki SuperAdminga teginolmaydi).
    - Teacher va Student: Faqat o'z profilini ko'ra oladi va o'z profilini PATCH qila oladi.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Foydalanuvchi yaratish (POST) faqat Admin va SuperAdminga ruxsat berilgan
        if view.action == 'create':
            return request.user.is_admin_user

        # Ro'yxatni ko'rish (GET list) faqat Admin va SuperAdmin uchun
        if view.action == 'list':
            return request.user.is_admin_user

        return True

    def has_object_permission(self, request, view, obj):
        user = request.user

        # 1. SuperAdmin barcha foydalanuvchilar ustidan to'liq ruxsatga ega
        if user.is_super_admin:
            return True

        # 2. Xavfsiz metodlar (GET retrieve)
        if request.method in permissions.SAFE_METHODS:
            # Admin barcha foydalanuvchilarni ko'ra oladi
            if user.role == Role.ADMIN:
                return True
            # Teacher va Student faqat o'zini ko'ra oladi
            return obj == user

        # 3. O'chirish (DELETE)
        if request.method == 'DELETE':
            # Admin faqat Teacher va Studentlarni o'chira oladi (boshqa Admin yoki SuperAdminni emas, o'zini ham emas)
            if user.role == Role.ADMIN:
                return obj.role in [Role.TEACHER, Role.STUDENT] and obj != user
            # Oddiy user hech kimni o'chira olmaydi
            return False

        # 4. Tahrirlash (PATCH)
        if request.method == 'PATCH':
            # Admin o'zini yoki Teacher/Studentlarni tahrirlashi mumkin
            if user.role == Role.ADMIN:
                if obj == user:
                    return True
                return obj.role in [Role.TEACHER, Role.STUDENT]
            # Teacher va Student faqat o'z profilini tahrirlashi mumkin
            return obj == user

        return False
