from django.urls import path
from .views import UserStockAnalysisView, GmailAuthView, FetchEmailsView, GmailCallbackView
from . import views

urlpatterns = [
    # ... your existing urls ...
    path('api/user/stock-analyses/', UserStockAnalysisView.as_view(), name='user_stock_analyses'),
    path('api/gmail/auth/', GmailAuthView.as_view(), name='gmail_auth'),
    path('api/fetch_emails/', FetchEmailsView.as_view(), name='fetch_emails'),
    path('gmail/callback/', GmailCallbackView.as_view(), name='gmail_callback'),
] 