from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context

from apps.customers.models import Client
from apps.users.models import Role


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            'name',type=str
        )

        parser.add_argument(
            '--username',type=str,default='admin'
        )

        parser.add_argument(
            '--password',type=str,default='123'
        )

    def handle(self, *args, **options):
        name = options['name']
        username = options.get('username')
        password = options.get('password')


        try:
            client = Client.objects.get(
                schema_name = name
            )
        except Client.DoesNotExist:
            raise CommandError(
                self.style.ERROR(
                    'Bunday markaz "%s" mavjud emas!' %name
                )
            )

        User = get_user_model()

        with schema_context(client.schema_name):
            if User.objects.filter(username = username):
                raise CommandError(
                    self.style.ERROR(
                        '"%s" bunday usernamedagi superuser oldin yaratilgan ' %username
                    )
                )

            User.objects.create_superuser(
                username=username,
                password=password,
                role = Role.SUPER_ADMIN
            )

            self.stdout.write(self.style.SUCCESS(
                f'User yaratildi username = {username}, password = {password}'
            ))
        