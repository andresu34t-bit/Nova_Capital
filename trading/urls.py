from django.urls import path
from . import views

app_name = 'trading'

urlpatterns = [
    path('', views.market_overview, name='market'),
    path('asset/<str:symbol>/', views.asset_detail, name='asset_detail'),
    path('portfolio/', views.portfolio, name='portfolio'),
    path('history/', views.trade_history, name='trade_history'),
    path('watchlist/', views.watchlist, name='watchlist'),
    path('watchlist/toggle/', views.toggle_watchlist, name='toggle_watchlist'),
    path('news/', views.news, name='news'),
    path('execute/', views.execute_trade, name='execute_trade'),
]
