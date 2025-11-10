from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Imports episodes for all registered podcasts'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("Called import-podcasts!")
        )
