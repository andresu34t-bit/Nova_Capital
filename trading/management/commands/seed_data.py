"""
Management command to seed initial market data
Usage: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from trading.models import Asset, NewsArticle
import requests
import datetime


CRYPTO_ASSETS = [
    ('BTC', 'Bitcoin', True),
    ('ETH', 'Ethereum', True),
    ('BNB', 'BNB', True),
    ('SOL', 'Solana', True),
    ('XRP', 'XRP', True),
    ('ADA', 'Cardano', False),
    ('DOGE', 'Dogecoin', True),
    ('AVAX', 'Avalanche', False),
    ('DOT', 'Polkadot', False),
    ('MATIC', 'Polygon', False),
    ('LINK', 'Chainlink', False),
    ('UNI', 'Uniswap', False),
    ('LTC', 'Litecoin', False),
    ('ATOM', 'Cosmos', False),
    ('NEAR', 'NEAR Protocol', False),
]

STOCK_ASSETS = [
    ('AAPL', 'Apple Inc.', True),
    ('MSFT', 'Microsoft Corp.', True),
    ('GOOGL', 'Alphabet Inc.', True),
    ('AMZN', 'Amazon.com Inc.', True),
    ('TSLA', 'Tesla Inc.', True),
    ('NVDA', 'NVIDIA Corp.', True),
    ('META', 'Meta Platforms', False),
    ('NFLX', 'Netflix Inc.', False),
    ('AMD', 'Advanced Micro Devices', False),
    ('COIN', 'Coinbase Global', False),
]

FOREX_ASSETS = [
    ('EURUSD', 'Euro / US Dollar', True),
    ('GBPUSD', 'British Pound / US Dollar', True),
    ('USDJPY', 'US Dollar / Japanese Yen', True),
    ('USDCHF', 'US Dollar / Swiss Franc', False),
    ('AUDUSD', 'Australian Dollar / US Dollar', False),
    ('USDCAD', 'US Dollar / Canadian Dollar', False),
    ('NZDUSD', 'New Zealand Dollar / US Dollar', False),
    ('EURGBP', 'Euro / British Pound', False),
]

SAMPLE_NEWS = [
    {
        'title': 'Bitcoin supera los $70,000 en medio de la aprobación de ETFs spot',
        'summary': 'El precio de Bitcoin alcanzó nuevos máximos históricos impulsado por la demanda institucional y la aprobación de ETFs de Bitcoin spot por parte de la SEC.',
        'source': 'CoinDesk',
        'category': 'crypto',
        'is_featured': True,
        'image_url': 'https://images.unsplash.com/photo-1518546305927-5a555bb7020d?w=800',
    },
    {
        'title': 'La Fed mantiene tasas de interés sin cambios en su última reunión',
        'summary': 'La Reserva Federal de Estados Unidos decidió mantener las tasas de interés en el rango actual, señalando que esperará más datos de inflación antes de realizar recortes.',
        'source': 'Reuters',
        'category': 'economy',
        'is_featured': True,
        'image_url': 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800',
    },
    {
        'title': 'Ethereum completa actualización de red mejorando escalabilidad',
        'summary': 'La red Ethereum completó exitosamente su última actualización de protocolo, reduciendo las tarifas de gas y mejorando significativamente la velocidad de las transacciones.',
        'source': 'The Block',
        'category': 'crypto',
        'is_featured': True,
        'image_url': 'https://images.unsplash.com/photo-1622630998477-20aa696ecb05?w=800',
    },
    {
        'title': 'NVIDIA reporta ganancias récord impulsadas por demanda de IA',
        'summary': 'NVIDIA superó todas las expectativas de Wall Street con ingresos trimestrales récord, impulsados por la demanda masiva de chips para inteligencia artificial.',
        'source': 'Bloomberg',
        'category': 'stocks',
        'is_featured': False,
        'image_url': 'https://images.unsplash.com/photo-1591696205602-2f950c417cb9?w=800',
    },
    {
        'title': 'El mercado de criptomonedas alcanza capitalización de $3 billones',
        'summary': 'La capitalización total del mercado de criptomonedas superó los 3 billones de dólares por primera vez, marcando un hito histórico para el sector.',
        'source': 'CoinTelegraph',
        'category': 'crypto',
        'is_featured': False,
        'image_url': 'https://images.unsplash.com/photo-1639762681485-074b7f938ba0?w=800',
    },
    {
        'title': 'Solana procesa más de 65,000 transacciones por segundo',
        'summary': 'La blockchain de Solana estableció un nuevo récord de rendimiento, procesando más de 65,000 transacciones por segundo durante períodos de alta demanda.',
        'source': 'Decrypt',
        'category': 'crypto',
        'is_featured': False,
        'image_url': 'https://images.unsplash.com/photo-1642790551116-18e150f248e3?w=800',
    },
]

# Default prices (fallback if API fails)
DEFAULT_PRICES = {
    'BTC': (67500, 2.3, 28000000000, 1320000000000, 69000, 65000),
    'ETH': (3800, 1.8, 15000000000, 456000000000, 3950, 3700),
    'BNB': (580, 0.9, 2100000000, 87000000000, 595, 565),
    'SOL': (185, 3.2, 8500000000, 82000000000, 192, 178),
    'XRP': (0.62, 1.1, 3200000000, 34000000000, 0.65, 0.60),
    'ADA': (0.48, -0.5, 450000000, 17000000000, 0.50, 0.46),
    'DOGE': (0.18, 4.2, 2800000000, 25000000000, 0.19, 0.17),
    'AVAX': (38, 2.1, 650000000, 15000000000, 40, 36),
    'DOT': (8.5, -1.2, 320000000, 11000000000, 9.0, 8.2),
    'MATIC': (0.92, 1.5, 580000000, 9200000000, 0.96, 0.89),
    'LINK': (18.5, 2.8, 420000000, 10800000000, 19.2, 17.8),
    'UNI': (12.3, 1.4, 180000000, 7400000000, 12.8, 11.9),
    'LTC': (95, 0.7, 620000000, 7100000000, 98, 92),
    'ATOM': (9.8, -0.8, 210000000, 3800000000, 10.2, 9.5),
    'NEAR': (7.2, 3.5, 380000000, 7800000000, 7.5, 6.9),
    # Stocks
    'AAPL': (189.5, 0.8, 0, 0, 191, 187),
    'MSFT': (415.2, 1.2, 0, 0, 418, 412),
    'GOOGL': (175.8, 0.5, 0, 0, 177, 174),
    'AMZN': (198.3, 1.8, 0, 0, 200, 196),
    'TSLA': (245.6, -2.1, 0, 0, 252, 242),
    'NVDA': (875.4, 3.2, 0, 0, 890, 860),
    'META': (520.1, 1.5, 0, 0, 525, 515),
    'NFLX': (628.5, 0.9, 0, 0, 635, 622),
    'AMD': (178.2, 2.4, 0, 0, 182, 175),
    'COIN': (245.8, 4.1, 0, 0, 252, 240),
    # Forex
    'EURUSD': (1.0875, 0.12, 0, 0, 1.0920, 1.0840),
    'GBPUSD': (1.2680, 0.08, 0, 0, 1.2720, 1.2650),
    'USDJPY': (149.85, -0.15, 0, 0, 150.20, 149.50),
    'USDCHF': (0.8920, 0.05, 0, 0, 0.8950, 0.8895),
    'AUDUSD': (0.6580, 0.18, 0, 0, 0.6610, 0.6555),
    'USDCAD': (1.3620, -0.08, 0, 0, 1.3650, 1.3595),
    'NZDUSD': (0.6120, 0.22, 0, 0, 0.6145, 0.6098),
    'EURGBP': (0.8580, 0.04, 0, 0, 0.8605, 0.8560),
}


class Command(BaseCommand):
    help = 'Seed initial market data for Nova Capital Group'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('🚀 Seeding Nova Capital Group data...'))

        # Try to fetch live crypto prices
        live_prices = self._fetch_live_prices()

        # Create crypto assets
        self.stdout.write('Creating crypto assets...')
        for symbol, name, featured in CRYPTO_ASSETS:
            price_data = live_prices.get(symbol) or DEFAULT_PRICES.get(symbol, (0, 0, 0, 0, 0, 0))
            asset, created = Asset.objects.update_or_create(
                symbol=symbol,
                defaults={
                    'name': name,
                    'asset_type': 'crypto',
                    'is_active': True,
                    'is_featured': featured,
                    'current_price': price_data[0],
                    'price_change_percent_24h': price_data[1],
                    'volume_24h': price_data[2],
                    'market_cap': price_data[3],
                    'high_24h': price_data[4],
                    'low_24h': price_data[5],
                }
            )
            status = '✓ Created' if created else '↻ Updated'
            self.stdout.write(f'  {status}: {symbol} @ ${price_data[0]:,.2f}')

        # Create stock assets
        self.stdout.write('Creating stock assets...')
        for symbol, name, featured in STOCK_ASSETS:
            price_data = DEFAULT_PRICES.get(symbol, (100, 0, 0, 0, 105, 95))
            Asset.objects.update_or_create(
                symbol=symbol,
                defaults={
                    'name': name,
                    'asset_type': 'stock',
                    'is_active': True,
                    'is_featured': featured,
                    'current_price': price_data[0],
                    'price_change_percent_24h': price_data[1],
                    'high_24h': price_data[4],
                    'low_24h': price_data[5],
                }
            )
            self.stdout.write(f'  ✓ {symbol}')

        # Create forex assets
        self.stdout.write('Creating forex assets...')
        for symbol, name, featured in FOREX_ASSETS:
            price_data = DEFAULT_PRICES.get(symbol, (1.0, 0, 0, 0, 1.01, 0.99))
            Asset.objects.update_or_create(
                symbol=symbol,
                defaults={
                    'name': name,
                    'asset_type': 'forex',
                    'is_active': True,
                    'is_featured': featured,
                    'current_price': price_data[0],
                    'price_change_percent_24h': price_data[1],
                    'high_24h': price_data[4],
                    'low_24h': price_data[5],
                }
            )
            self.stdout.write(f'  ✓ {symbol}')

        # Create news articles
        self.stdout.write('Creating news articles...')
        for i, article_data in enumerate(SAMPLE_NEWS):
            pub_date = timezone.now() - datetime.timedelta(hours=i * 3)
            NewsArticle.objects.update_or_create(
                title=article_data['title'],
                defaults={
                    'summary': article_data['summary'],
                    'source': article_data['source'],
                    'category': article_data['category'],
                    'is_featured': article_data['is_featured'],
                    'image_url': article_data.get('image_url', ''),
                    'published_at': pub_date,
                }
            )
            self.stdout.write(f'  ✓ {article_data["title"][:50]}...')

        total_assets = Asset.objects.count()
        total_news = NewsArticle.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Done! {total_assets} assets and {total_news} news articles ready.'
        ))

    def _fetch_live_prices(self):
        """Try to fetch live prices from CoinGecko"""
        try:
            self.stdout.write('Fetching live crypto prices from CoinGecko...')
            ids = 'bitcoin,ethereum,binancecoin,solana,ripple,cardano,dogecoin,avalanche-2,polkadot,matic-network,chainlink,uniswap,litecoin,cosmos,near'
            url = f'https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true&include_market_cap=true'
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            id_map = {
                'bitcoin': 'BTC', 'ethereum': 'ETH', 'binancecoin': 'BNB',
                'solana': 'SOL', 'ripple': 'XRP', 'cardano': 'ADA',
                'dogecoin': 'DOGE', 'avalanche-2': 'AVAX', 'polkadot': 'DOT',
                'matic-network': 'MATIC', 'chainlink': 'LINK', 'uniswap': 'UNI',
                'litecoin': 'LTC', 'cosmos': 'ATOM', 'near': 'NEAR',
            }

            prices = {}
            for coin_id, pdata in data.items():
                symbol = id_map.get(coin_id)
                if symbol:
                    price = pdata.get('usd', 0)
                    change = pdata.get('usd_24h_change', 0)
                    vol = pdata.get('usd_24h_vol', 0)
                    cap = pdata.get('usd_market_cap', 0)
                    high = price * 1.03
                    low = price * 0.97
                    prices[symbol] = (price, change, vol, cap, high, low)
                    self.stdout.write(f'  📡 Live: {symbol} = ${price:,.2f} ({change:+.2f}%)')

            return prices
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  ⚠ Could not fetch live prices: {e}. Using defaults.'))
            return {}
