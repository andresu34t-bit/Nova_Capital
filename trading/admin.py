from django.contrib import admin
from .models import Asset, Portfolio, Trade, WatchList, PriceAlert, NewsArticle


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'name', 'asset_type', 'current_price', 'price_change_percent_24h', 
                    'is_active', 'is_featured']
    list_filter = ['asset_type', 'is_active', 'is_featured']
    search_fields = ['symbol', 'name']
    list_editable = ['is_active', 'is_featured']
    ordering = ['asset_type', 'symbol']


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ['user', 'asset', 'quantity', 'average_buy_price', 'total_invested']
    list_filter = ['asset__asset_type']
    search_fields = ['user__email', 'asset__symbol']


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ['user', 'asset', 'trade_type', 'quantity', 'price', 'total_value', 
                    'fee', 'status', 'created_at']
    list_filter = ['trade_type', 'status', 'asset__asset_type']
    search_fields = ['user__email', 'asset__symbol']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at', 'filled_at']


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'source', 'category', 'is_featured', 'published_at']
    list_filter = ['category', 'is_featured']
    search_fields = ['title', 'source']
    list_editable = ['is_featured']
    ordering = ['-published_at']


@admin.register(PriceAlert)
class PriceAlertAdmin(admin.ModelAdmin):
    list_display = ['user', 'asset', 'alert_type', 'target_price', 'is_active', 'created_at']
    list_filter = ['alert_type', 'is_active']
