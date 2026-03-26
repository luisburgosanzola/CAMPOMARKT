from django.db import migrations


def ensure_site_exists(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    Site.objects.update_or_create(
        id=1,
        defaults={
            'domain': 'awake-spirit-production-ebac.up.railway.app',
            'name': 'CampoMarkt',
        }
    )


class Migration(migrations.Migration):

    dependencies = [
        ('Usuarios', '0006_remove_duplicate_google_socialapp'),
        ('sites', '0002_alter_domain_unique'),
    ]

    operations = [
        migrations.RunPython(
            ensure_site_exists,
            migrations.RunPython.noop,
        ),
    ]
