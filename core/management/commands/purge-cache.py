from django.core.management.base import BaseCommand, CommandError

from core.utils.front_door import PurgeError, purge


class Command(BaseCommand):
    help = (
        'Purges paths from the Front Door cache, such as /api/v1/research/*. '
        'Import jobs run it after a successful import. Does nothing when '
        'Front Door is not configured.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'paths',
            nargs='+',
            help='Paths to purge; * matches everything under a folder'
        )

    def handle(self, *args, **options):
        paths = options['paths']

        for path in paths:
            if not path.startswith('/'):
                raise CommandError(f'Paths must start with /: {path}')

        try:
            purged = purge(paths)
        except PurgeError as e:
            raise CommandError(str(e))

        if purged:
            self.stdout.write(f'Requested a Front Door purge of {", ".join(paths)}')
        else:
            self.stdout.write('Front Door is not configured; nothing to purge.')
