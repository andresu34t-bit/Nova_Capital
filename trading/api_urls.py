from django.urls import path
from . import api_views

urlpatterns = [
    path('prices/', api_views.get_prices, name='api_prices'),
    path('prices/<str:symbol>/', api_views.get_asset_price, name='api_asset_price'),
    path('news/', api_views.get_news, name='api_news'),
    path('portfolio/', api_views.get_portfolio, name='api_portfolio'),
    path('chart/<str:symbol>/', api_views.get_chart_data, name='api_chart'),
]
