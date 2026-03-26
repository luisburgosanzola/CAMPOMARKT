from django.db import migrations


def remove_duplicate_google_socialapp(apps, schema_editor):
    SocialApp = apps.get_model('socialaccount', 'SocialApp')
    SocialApp.objects.filter(provider='google').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('Usuarios', '0005_user_google_avatar'),
        ('socialaccount', '0006_alter_socialaccount_extra_data'),
    ]

    operations = [
        migrations.RunPython(
            remove_duplicate_google_socialapp,
            migrations.RunPython.noop,
        ),
    ]
