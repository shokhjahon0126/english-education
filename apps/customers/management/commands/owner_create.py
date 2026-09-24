# apps/customers/management/commands/create_owner.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context

from apps.users.models import Role
from apps.customers.models import Client, Domain

User = get_user_model()

class Command(BaseCommand):
    help = "Platformaning asosiy egasini (Public Glavniy Owner) va public tenantni yaratish"

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='admin', help="Owner username")
        parser.add_argument('--password', type=str, default='123', help="Owner paroli")
        parser.add_argument('--email', type=str, default='owner@platform.uz', help="Owner emaili")

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']

        # 1-QADAM: Public tenant (Glavniy tizim) mavjudligini ta'minlash
        public_client, created = Client.objects.get_or_create(
            schema_name='public',
            defaults={
                'name': 'Master Platform (SaaS Owner)',
                'paid_until': '2099-12-31',
                'on_trial': False
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS("Public Client yaratildi."))

        # 2-QADAM: Glavniy domen (localhost) ni public ga ulash
        domain, d_created = Domain.objects.get_or_create(
            domain='localhost',
            tenant=public_client,
            defaults={'is_primary': True}
        )
        if d_created:
            self.stdout.write(self.style.SUCCESS("Glavniy domen (localhost) ulandi."))

        # 3-QADAM: Aynan PUBLIC schema ichida Glavniy Owner superuserini yaratish
        with schema_context('public'):
            if not User.objects.filter(username=username).exists():
                owner_user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password,
                    role=Role.SUPER_ADMIN if hasattr(User, 'role') else None # agar CustomUser da role maydoni bo'lsa
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n Tabriklaymiz! Glavniy Owner yaratildi:\n"
                        f" - Username: {username}\n"
                        f" - Parol: {password}\n"
                        f" - Manzil: http://localhost:8000/admin/\n"
                    )
                )
            else:
                self.stdout.write(self.style.WARNING(f"'{username}' nomli Glavniy Owner allaqachon mavjud!"))