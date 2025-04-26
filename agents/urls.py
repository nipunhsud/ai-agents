from django.urls import path
from .views import UserStockAnalysisView
from . import views

urlpatterns = [
    # ... your existing urls ...
    path('api/user/stock-analyses/', UserStockAnalysisView.as_view(), name='user_stock_analyses'),
    path('gmail/auth/', views.initiate_gmail_auth, name='gmail_auth'),
    path('gmail/callback/', views.gmail_oauth_callback, name='gmail_callback'),
] 