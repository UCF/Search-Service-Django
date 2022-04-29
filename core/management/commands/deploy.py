from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Runs deployment related tasks.'

    def handle(self, *args, **options):
        call_command('migrate', 'locations', '--database=locations')
        call_command('migrate', '--database=default')
        call_command('collectstatic', '--link', '--no-input')
