from django.db import connection
from rest_framework import exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_spectacular.extensions import OpenApiAuthenticationExtension


class TenantJWTAuthentication(JWTAuthentication):
    """
    Tenant asosidagi JWT Authentication.
    Tokendagi 'schema_name' bilan joriy so'rov yuborilgan tenantning 'schema_name' sini solishtiradi.
    Agar boshqa tenantning tokeni bilan so'rov yuborilsa, 401 Unauthorized (AuthenticationFailed) qaytaradi.
    """

    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)

        # 1. Joriy so'rov kelgan tenant schemasi
        current_schema = None
        if hasattr(request, 'tenant') and request.tenant is not None:
            current_schema = getattr(request.tenant, 'schema_name', None)
        if not current_schema:
            current_schema = getattr(connection, 'schema_name', 'public')

        # 2. Tokendagi schema_name
        token_schema = validated_token.get('schema_name')

        # 3. Solishtirish: agar tokendagi schema bilan joriy schema mos kelmasa -> 401 Unauthorized
        if token_schema and current_schema and token_schema != current_schema:
            raise exceptions.AuthenticationFailed(
                f"Ushbu token '{token_schema}' tenantiga tegishli. "
                f"Joriy '{current_schema}' tenantiga kirish taqiqlanadi (401 Unauthorized)."
            )

        user = self.get_user(validated_token)
        return (user, validated_token)


class TenantJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    """
    Swagger (OpenAPI) da Authorize tugmasi (JWT Bearer Token kiritish oynasi)
    paydo bo'lishi va TenantJWTAuthentication ni tanishi uchun extension.
    """
    target_class = 'apps.users.authentication.TenantJWTAuthentication'
    name = 'jwtAuth'

    def get_security_requirement(self, auto_schema):
        return {self.name: []}

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
            'description': "JWT access tokenni kiriting. Masalan: Bearer <token>",
        }
