from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from chat import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.upload_page, name='upload_page'),
    path('upload/', views.UploadView.as_view(), name='upload_document'),
    path('uploads/', views.upload_document, name='upload_document'),
    path('summary/<int:document_id>/', views.custom_summary, name='custom_summary'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 