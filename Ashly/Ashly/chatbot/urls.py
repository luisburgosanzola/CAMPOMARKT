from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_page, name='chat_page'),
    path('chat/', views.chat_api, name='chat_api'),
    path('ask/', views.ask_api, name='ask_api'),           # ✅ NUEVO (chat pro)
    path('upload-image/', views.upload_image_api, name='upload_image_api'),
]
