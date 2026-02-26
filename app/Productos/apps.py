from django.apps import AppConfig

class ProductosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.Productos'

    def ready(self):
        import app.Productos.signals
