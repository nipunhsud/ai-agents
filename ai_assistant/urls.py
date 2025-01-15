from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from agents import views
from slack_agent.views import test
from code_reviewer_agent.views import code_reviewer_view,github_webhook,github_keys_form,submit_keys,success_view
from help_desk_agent.views import test_help_desk_agent_view,help_desk,help_desk_receive
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
    path("add-slack-token/",add_slack_token, name='add_slack_token'),
    path("assistant/",views.AssistantView.as_view(), name='assistant'),
    path("email_assistant/",views.EmailAssistantView.as_view(), name='email_assistant'),
    path('analyst/', views.quant_analyst_page, name='quant_analyst_page'),
    path("stock_assistant/",views.StockAssistantView.as_view(), name='stock_assistant'),
    path("code_reviewer/",code_reviewer_view, name='code_reviewer'),
    #path("github_webhook/",github_webhook, name='github_webhook'),
    path('github_webhook/<str:variable>/', github_webhook, name='github_webhook'),
    path('github_keys_form/', github_keys_form, name='github_keys_form'),
    path('submit_keys/', submit_keys, name='submit_keys'),
    path('success_view/', success_view, name='success_page'),
    path('test_help_desk_agent_view/', test_help_desk_agent_view, name='test_help_desk_agent_view'),
    path('help_desk/', help_desk, name='help_desk'),
    path('help_desk_receive/', help_desk_receive, name='help_desk_receive'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



