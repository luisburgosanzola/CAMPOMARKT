from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.Usuarios'
    
    def ready(self):
        import app.Usuarios.signals

        