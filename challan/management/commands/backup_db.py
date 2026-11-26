from django.core.management.base import BaseCommand

from challan import backup


class Command(BaseCommand):
    help = "Create a timestamped backup of the database in the backups folder."

    def add_arguments(self, parser):
        parser.add_argument("--keep", type=int, default=30,
                            help="How many automatic backups to keep (default 30)")

    def handle(self, *args, **opts):
        path = backup.make_backup()
        backup.prune_backups(opts["keep"])
        self.stdout.write(self.style.SUCCESS(f"Backup created: {path}"))
