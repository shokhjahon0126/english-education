from django.contrib import admin
from django_tenants.admin import TenantAdminMixin
from apps.customers.models import Client, Domain


class CentralOnlyAdmin(admin.ModelAdmin):

    def has_module_permission(self, request):
        return request.tenant.schema_name == "public"

    def has_view_permission(self, request, obj=None):
        return request.tenant.schema_name == "public"

    def has_add_permission(self, request):
        return request.tenant.schema_name == "public"

    def has_change_permission(self, request, obj=None):
        return request.tenant.schema_name == "public"

    def has_delete_permission(self, request, obj=None):
        return request.tenant.schema_name == "public"

    
@admin.register(Client)
class ClientAdmin(CentralOnlyAdmin):
    list_display = ('name', 'schema_name', 'paid_until', 'on_trial', 'created_on')
    search_fields = ('name', 'schema_name')

    def has_add_permission(self, request):
        return request.user.is_superuser

@admin.register(Domain)
class DomainAdmin(CentralOnlyAdmin):
    list_display = ('domain', 'tenant', 'is_primary')
    search_fields = ('domain',)

    def has_module_permission(self, request):
        return request.user.is_superuser