"""
API views for real-time market data
"""
import requests
import logging
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from .models import Asset, Portfolio, NewsArticle

logger = logging.getLogger(__name__)

COINGECKO_BASE = 'https://api.coingecko.com/api/v3'

# Mapping of our symbols to CoinGecko IDs
CRYPTO_IDS = {
    'BTC': 'bitcoin',
    'ETH': 'ethereum',
    'BNB': 'binancecoin',
    'SOL': 'solana',
    'ADA': 'cardano',
    'XRP': 'ripple',
    'DOT': 'polkadot',
    'DOGE': 'dogecoin',
    'AVAX': 'avalanche-2',
    'MATIC': 'matic-network',
    'LINK': 'chainlink',
    'UNI': 'uniswap',
    'LTC': 'litecoin',
    'ATOM': 'cosmos',
    'NEAR': 'near',
}


def fetch_crypto_prices():
    """Fetch real crypto prices from CoinGecko"""
    cache_key = 'crypto_prices_all'
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    try:
        ids = ','.join(CRYPTO_IDS.values())
        url = f"{COINGECKO_BASE}/simple/price"
        params = {
            'ids': ids,
            'vs_currencies': 'usd',
            'include_24hr_change': 'true',
            'include_24hr_vol': 'true',
            'include_market_cap': 'true',
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Transform to our format
        prices = {}
        reverse_map = {v: k for k, v in CRYPTO_IDS.items()}
        for coin_id, price_data in data.items():
            symbol = reverse_map.get(coin_id)
            if symbol:
                prices[symbol] = {
                    'price': price_data.get('usd', 0),
                    'change_24h': price_data.get('usd_24h_change', 0),
                    'volume_24h': price_data.get('usd_24h_vol', 0),
                    'market_cap': price_data.get('usd_market_cap', 0),
                }
        
        # Update database
        for symbol, data in prices.items():
            Asset.objects.filter(symbol=symbol).update(
                current_price=data['price'],
                price_change_percent_24h=data['change_24h'],
                volume_24h=data['volume_24h'],
                market_cap=data['market_cap'],
            )
        
        cache.set(cache_key, prices, 30)  # Cache for 30 seconds
        return prices
        
    except Exception as e:
        logger.error(f"Error fetching crypto prices: {e}")
        # Return cached DB prices as fallback
        assets = Asset.objects.filter(asset_type='crypto', is_active=True)
        return {
            a.symbol: {
                'price': float(a.current_price),
                'change_24h': float(a.price_change_percent_24h),
                'volume_24h': float(a.volume_24h),
                'market_cap': float(a.market_cap),
            }
            for a in assets
        }


@login_required
def get_prices(request):
    """Get all asset prices"""
    asset_type = request.GET.get('type', 'crypto')
    
    if asset_type == 'crypto':
        prices = fetch_crypto_prices()
        return JsonResponse({'success': True, 'prices': prices})
    
    # For stocks/forex, return DB cached prices
    assets = Asset.objects.filter(asset_type=asset_type, is_active=True)
    prices = {}
    for asset in assets:
        prices[asset.symbol] = {
            'price': float(asset.current_price),
            'change_24h': float(asset.price_change_percent_24h),
            'name': asset.name,
        }
    
    return JsonResponse({'success': True, 'prices': prices})


@login_required
def get_asset_price(request, symbol):
    """Get single asset price"""
    try:
        asset = Asset.objects.get(symbol=symbol.upper(), is_active=True)
        
        # Try to get fresh price for crypto
        if asset.asset_type == 'crypto':
            prices = fetch_crypto_prices()
            if symbol.upper() in prices:
                price_data = prices[symbol.upper()]
                return JsonResponse({
                    'success': True,
                    'symbol': symbol.upper(),
                    'price': price_data['price'],
                    'change_24h': price_data['change_24h'],
                    'volume_24h': price_data['volume_24h'],
                })
        
        return JsonResponse({
            'success': True,
            'symbol': asset.symbol,
            'price': float(asset.current_price),
            'change_24h': float(asset.price_change_percent_24h),
            'name': asset.name,
        })
    except Asset.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Asset not found'}, status=404)


@login_required
def get_news(request):
    """Get latest financial news"""
    articles = NewsArticle.objects.all()[:10]
    data = [{
        'title': a.title,
        'summary': a.summary,
        'source': a.source,
        'category': a.category,
        'image_url': a.image_url,
        'published_at': a.published_at.isoformat(),
        'url': a.source_url,
    } for a in articles]
    
    return JsonResponse({'success': True, 'articles': data})


@login_required
def get_portfolio(request):
    """Get user portfolio data"""
    items = Portfolio.objects.filter(user=request.user).select_related('asset')
    
    data = []
    for item in items:
        data.append({
            'symbol': item.asset.symbol,
            'name': item.asset.name,
            'quantity': float(item.quantity),
            'avg_price': float(item.average_buy_price),
            'current_price': float(item.asset.current_price),
            'current_value': float(item.current_value),
            'total_invested': float(item.total_invested),
            'pnl': float(item.profit_loss),
            'pnl_percent': float(item.profit_loss_percent),
        })
    
    return JsonResponse({'success': True, 'portfolio': data})


@login_required
def get_chart_data(request, symbol):
    """Get chart data for an asset - uses TradingView widget data"""
    # TradingView handles charts client-side, this provides metadata
    try:
        asset = Asset.objects.get(symbol=symbol.upper())
        return JsonResponse({
            'success': True,
            'symbol': asset.symbol,
            'name': asset.name,
            'type': asset.asset_type,
            'tradingview_symbol': _get_tradingview_symbol(asset),
        })
    except Asset.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Not found'}, status=404)


def _get_tradingview_symbol(asset):
    """Get TradingView symbol format"""
    if asset.asset_type == 'crypto':
        return f"BINANCE:{asset.symbol}USDT"
    elif asset.asset_type == 'stock':
        return f"NASDAQ:{asset.symbol}"
    elif asset.asset_type == 'forex':
        return f"FX:{asset.symbol}"
    return asset.symbol
