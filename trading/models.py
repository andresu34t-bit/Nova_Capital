from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class Asset(models.Model):
    """Financial asset model"""
    
    ASSET_TYPES = [
        ('crypto', 'Criptomoneda'),
        ('stock', 'Acción'),
        ('forex', 'Forex'),
        ('commodity', 'Commodity'),
        ('index', 'Índice'),
    ]
    
    symbol = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES)
    description = models.TextField(blank=True)
    logo_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Current price data (cached)
    current_price = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    price_change_24h = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    price_change_percent_24h = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    volume_24h = models.DecimalField(max_digits=30, decimal_places=2, default=0)
    market_cap = models.DecimalField(max_digits=30, decimal_places=2, default=0)
    high_24h = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    low_24h = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['asset_type', 'symbol']
        verbose_name = 'Activo'
        verbose_name_plural = 'Activos'
    
    def __str__(self):
        return f"{self.symbol} - {self.name}"
    
    @property
    def is_positive(self):
        return self.price_change_percent_24h >= 0


class Portfolio(models.Model):
    """User portfolio/holdings"""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='portfolio')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    average_buy_price = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    total_invested = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'asset']
        verbose_name = 'Portafolio'
        verbose_name_plural = 'Portafolios'
    
    def __str__(self):
        return f"{self.user.email} - {self.asset.symbol}: {self.quantity}"
    
    @property
    def current_value(self):
        return self.quantity * self.asset.current_price
    
    @property
    def profit_loss(self):
        return self.current_value - self.total_invested
    
    @property
    def profit_loss_percent(self):
        if self.total_invested > 0:
            return ((self.current_value - self.total_invested) / self.total_invested) * 100
        return 0


class Trade(models.Model):
    """Individual trade record"""
    
    TRADE_TYPES = [
        ('buy', 'Compra'),
        ('sell', 'Venta'),
    ]
    
    ORDER_TYPES = [
        ('market', 'Mercado'),
        ('limit', 'Límite'),
        ('stop', 'Stop Loss'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('open', 'Abierta'),
        ('filled', 'Ejecutada'),
        ('cancelled', 'Cancelada'),
        ('failed', 'Fallida'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trades')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    trade_type = models.CharField(max_length=10, choices=TRADE_TYPES)
    order_type = models.CharField(max_length=10, choices=ORDER_TYPES, default='market')
    quantity = models.DecimalField(max_digits=20, decimal_places=8)
    price = models.DecimalField(max_digits=20, decimal_places=8)
    total_value = models.DecimalField(max_digits=20, decimal_places=2)
    fee = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    limit_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    stop_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    filled_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Operación'
        verbose_name_plural = 'Operaciones'
    
    def __str__(self):
        return f"{self.user.email} - {self.trade_type} {self.quantity} {self.asset.symbol}"


class WatchList(models.Model):
    """User watchlist"""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='watchlist')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'asset']
        verbose_name = 'Lista de Seguimiento'
        verbose_name_plural = 'Listas de Seguimiento'


class PriceAlert(models.Model):
    """Price alert for assets"""
    
    ALERT_TYPES = [
        ('above', 'Por encima de'),
        ('below', 'Por debajo de'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='price_alerts')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=10, choices=ALERT_TYPES)
    target_price = models.DecimalField(max_digits=20, decimal_places=8)
    is_active = models.BooleanField(default=True)
    triggered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Alerta de Precio'
        verbose_name_plural = 'Alertas de Precio'


class NewsArticle(models.Model):
    """Financial news articles"""
    
    CATEGORIES = [
        ('crypto', 'Criptomonedas'),
        ('stocks', 'Acciones'),
        ('forex', 'Forex'),
        ('economy', 'Economía'),
        ('technology', 'Tecnología'),
        ('general', 'General'),
    ]
    
    title = models.CharField(max_length=300)
    summary = models.TextField()
    content = models.TextField(blank=True)
    source = models.CharField(max_length=100)
    source_url = models.URLField(blank=True)
    image_url = models.URLField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORIES, default='general')
    is_featured = models.BooleanField(default=False)
    published_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-published_at']
        verbose_name = 'Noticia'
        verbose_name_plural = 'Noticias'
    
    def __str__(self):
        return self.title
