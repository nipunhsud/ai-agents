from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from chat import views
from slack_agent.views import test,handle_message
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.upload_page, name='upload_page'),
    path('upload/', views.UploadView.as_view(), name='upload_document'),
    path('uploads/', views.upload_document, name='upload_document'),
    path('summary/<int:document_id>/', views.custom_summary, name='custom_summary'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('agent/', views.AgentView.as_view(), name='agent'),
    path('react/', views.react_page, name='react_page'), 
    path('query/', views.query_page, name='query_page'), 
    path("gift/",views.gift_prediction_view, name='gift'),
    path("slack/",test, name='slack'),
    path('writer/', views.technical_writer_view, name='technical_writer'),
    path("slack2/",handle_message, name='slack_message'),
    path("assistant/",views.AssistantView.as_view(), name='assistant'),
    path("email_assistant/",views.EmailAssistantView.as_view(), name='email_assistant'),
    path('analyst/', views.quant_analyst_page, name='quant_analyst_page'),
    path("stock_assistant/",views.StockAssistantView.as_view(), name='stock_assistant'),
    path("email/",views.email_assistant_page, name='email_assistant_page'),
    path('fetch_emails/', views.fetch_emails, name='fetch_emails'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



