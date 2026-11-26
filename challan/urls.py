from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("dc/new/", views.dc_form, name="dc_new"),
    path("dc/", views.dc_list, name="dc_list"),
    path("dc/bulk-delete-year/", views.dc_bulk_delete_year, name="dc_bulk_delete_year"),
    path("dc/<int:pk>/edit/", views.dc_form, name="dc_edit"),
    path("dc/<int:pk>/print/", views.dc_print, name="dc_print"),
    path("dc/<int:pk>/delete/", views.dc_delete, name="dc_delete"),
    path("import/", views.import_page, name="import_word"),
    path("backup/", views.backup_page, name="backup"),
    path("backup/create/", views.backup_create, name="backup_create"),
    path("backup/download/", views.backup_download, name="backup_download"),
    path("backup/download/<str:name>/", views.backup_download_file, name="backup_download_file"),
    path("backup/restore/", views.backup_restore, name="backup_restore"),
]
