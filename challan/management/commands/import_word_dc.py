from django.core.management.base import BaseCommand, CommandError

from challan import importer


class Command(BaseCommand):
    help = "Import old delivery challans from Word (.docx) files in a folder."

    def add_arguments(self, parser):
        parser.add_argument("folder", help="Folder containing the Word files")
        parser.add_argument("--dry-run", action="store_true",
                            help="Check the files and show what would be imported, save nothing")
        parser.add_argument("--no-subfolders", action="store_true")

    def handle(self, *args, **opts):
        files = importer.find_docx_files(opts["folder"], recursive=not opts["no_subfolders"])
        if not files:
            raise CommandError("No Word files found in that folder.")
        results = importer.import_files([(f.name, f) for f in files], dry_run=opts["dry_run"])
        counts = {}
        for r in results:
            counts[r["status"]] = counts.get(r["status"], 0) + 1
            self.stdout.write(f"[{r['status'].upper():8}] {r['file']}  DC {r['dc_no']}  {r['message']}")
        self.stdout.write(self.style.SUCCESS("Summary: " + ", ".join(f"{k}={v}" for k, v in counts.items())))
