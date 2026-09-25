# from rest_framework.permissions import BasePermission

# from .models import User,Role

# class SuperadminPermissions(BasePermission):
#     message = "'Siz Super Admin emassiz!"

#     def has_permission(self, request, view):
#         return (
#             request.user,
#             request.is_authanticate,
#             request.user.role == Role.SUPER_ADMIN,
#         )


# class AdminPermissions(BasePermission):
#     message = "Siz Admin emassiz!"

#     def has_permission(self, request, view):
#         return (
#             request.user,
            
#         )