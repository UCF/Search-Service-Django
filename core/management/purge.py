from django.core.management.base import CommandError

from core.utils.front_door import PurgeError, purge


class PurgeAfterImportMixin:
    """
    For import commands. After the command finishes, purges its
    purge_paths from Front Door so the imported data appears without
    waiting out the cache TTLs. --no-purge skips it, and so does a
    command's --dry-run. Does nothing when Front Door isn't configured,
    as when running locally.

    Program data appears across most of /api/v1/, so the programs and
    units imports purge all of it.
    """
    purge_paths = []

    def create_parser(self, prog_name, subcommand, **kwargs):
        parser = super().create_parser(prog_name, subcommand, **kwargs)
        parser.add_argument(
            '--no-purge',
            action='store_true',
            dest='no_purge',
            help="Don't purge this import's API paths from Front Door afterward"
        )
        return parser

    def execute(self, *args, **options):
        output = super().execute(*args, **options)

        if not options.get('no_purge') and not options.get('dry_run'):
            try:
                if purge(self.purge_paths):
                    self.stdout.write(f'Requested a Front Door purge of {", ".join(self.purge_paths)}')
            except PurgeError as e:
                raise CommandError(f'The import finished, but the Front Door purge failed: {e}')

        return output
