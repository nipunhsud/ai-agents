from django.urls import path
from .views import UserStockAnalysisView

urlpatterns = [
    # ... your existing urls ...
    path('api/user/stock-analyses/', UserStockAnalysisView.as_view(), name='user_stock_analyses'),
] 