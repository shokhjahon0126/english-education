# apps/customers/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.sites.models import Site
from django_tenants.utils import schema_context
from apps.customers.models import Domain

@receiver(post_save, sender=Domain)
def sync_tenant_site(sender, instance, created, **kwargs):
  """Yangi domen yaratilganda yoki o'zgarganda o'sha tenantning

  schemasi ichidagi django_site jadvalini avtomatik to'ldiradi.
  """
  tenant_schema = instance.tenant.schema_name

  # Shu schema ichiga kiramiz
  with schema_context(tenant_schema):
    # Har bir schemaning o'zida Site har doim id=1 bo'ladi
    site, _ = Site.objects.get_or_create(id=1)
    site.domain = instance.domain
    site.name = instance.tenant.name
    site.save()