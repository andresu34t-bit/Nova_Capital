from django import template
from django.utils.html import format_html, mark_safe

register = template.Library()

# Real CoinGecko logo URLs for crypto
CRYPTO_LOGOS = {
    'BTC':   'https://assets.coingecko.com/coins/images/1/small/bitcoin.png',
    'ETH':   'https://assets.coingecko.com/coins/images/279/small/ethereum.png',
    'BNB':   'https://assets.coingecko.com/coins/images/825/small/bnb-icon2_2x.png',
    'SOL':   'https://assets.coingecko.com/coins/images/4128/small/solana.png',
    'XRP':   'https://assets.coingecko.com/coins/images/44/small/xrp-symbol-white-128.png',
    'ADA':   'https://assets.coingecko.com/coins/images/975/small/cardano.png',
    'DOGE':  'https://assets.coingecko.com/coins/images/5/small/dogecoin.png',
    'AVAX':  'https://assets.coingecko.com/coins/images/12559/small/Avalanche_Circle_RedWhite_Trans.png',
    'DOT':   'https://assets.coingecko.com/coins/images/12171/small/polkadot.png',
    'MATIC': 'https://assets.coingecko.com/coins/images/4713/small/matic-token-icon.png',
    'LINK':  'https://assets.coingecko.com/coins/images/877/small/chainlink-new-logo.png',
    'UNI':   'https://assets.coingecko.com/coins/images/12504/small/uniswap-uni.png',
    'LTC':   'https://assets.coingecko.com/coins/images/2/small/litecoin.png',
    'ATOM':  'https://assets.coingecko.com/coins/images/1481/small/cosmos_hub.png',
    'NEAR':  'https://assets.coingecko.com/coins/images/10365/small/near.jpg',
    'USDT':  'https://assets.coingecko.com/coins/images/325/small/Tether.png',
    'USDC':  'https://assets.coingecko.com/coins/images/6319/small/USD_Coin_icon.png',
    'USD':   'https://assets.coingecko.com/coins/images/325/small/Tether.png',
    'EUR':   '',
}

# Stock colors for styled badges
STOCK_COLORS = {
    'AAPL':  {'bg': '#1c1c1e', 'color': '#f5f5f7', 'text': 'A'},
    'MSFT':  {'bg': '#0078d4', 'color': '#ffffff', 'text': 'M'},
    'GOOGL': {'bg': '#4285f4', 'color': '#ffffff', 'text': 'G'},
    'AMZN':  {'bg': '#ff9900', 'color': '#000000', 'text': 'A'},
    'TSLA':  {'bg': '#cc0000', 'color': '#ffffff', 'text': 'T'},
    'NVDA':  {'bg': '#76b900', 'color': '#000000', 'text': 'N'},
    'META':  {'bg': '#0866ff', 'color': '#ffffff', 'text': 'M'},
    'NFLX':  {'bg': '#e50914', 'color': '#ffffff', 'text': 'N'},
    'AMD':   {'bg': '#ed1c24', 'color': '#ffffff', 'text': 'A'},
    'COIN':  {'bg': '#0052ff', 'color': '#ffffff', 'text': 'C'},
}

# Forex flag emojis
FOREX_INFO = {
    'EURUSD': {'flag': '🇪🇺', 'color': '#003399'},
    'GBPUSD': {'flag': '🇬🇧', 'color': '#012169'},
    'USDJPY': {'flag': '🇯🇵', 'color': '#bc002d'},
    'USDCHF': {'flag': '🇨🇭', 'color': '#ff0000'},
    'AUDUSD': {'flag': '🇦🇺', 'color': '#00008b'},
    'USDCAD': {'flag': '🇨🇦', 'color': '#ff0000'},
    'NZDUSD': {'flag': '🇳🇿', 'color': '#00247d'},
    'EURGBP': {'flag': '🇪🇺', 'color': '#003399'},
}


@register.simple_tag
def asset_icon(symbol, asset_type='crypto', size=36, extra_class=''):
    """Returns HTML for a premium asset icon — real logo for crypto, styled badge for stocks/forex."""
    symbol = str(symbol).upper()
    size = int(size)
    br = size // 3  # border-radius

    # --- CRYPTO: real logo image ---
    logo_url = CRYPTO_LOGOS.get(symbol, '')
    if logo_url and asset_type in ('crypto', 'Criptomoneda'):
        fallback_letter = symbol[0] if symbol else '?'
        return format_html(
            '<span class="asset-icon-wrap {extra}" style="display:inline-flex;flex-shrink:0;">'
            '<img src="{url}" alt="{sym}" '
            'style="width:{s}px;height:{s}px;border-radius:50%;object-fit:cover;'
            'box-shadow:0 2px 8px rgba(0,0,0,0.4);flex-shrink:0;" '
            'onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\'">'
            '<span style="display:none;width:{s}px;height:{s}px;border-radius:50%;'
            'background:linear-gradient(135deg,#0066ff,#00d4ff);color:#fff;'
            'font-weight:800;font-size:{fs}px;align-items:center;justify-content:center;flex-shrink:0;">'
            '{letter}</span></span>',
            extra=extra_class, url=logo_url, sym=symbol,
            s=size, fs=max(size // 3, 8), letter=fallback_letter
        )

    # --- STOCK: colored badge ---
    stock = STOCK_COLORS.get(symbol)
    if stock or asset_type in ('stock', 'Acción'):
        bg = stock['bg'] if stock else '#1a2035'
        color = stock['color'] if stock else '#ffffff'
        letter = stock['text'] if stock else symbol[:2]
        fs = max(size // 3, 7)
        return format_html(
            '<span class="asset-icon-stock {extra}" '
            'style="display:inline-flex;align-items:center;justify-content:center;'
            'width:{s}px;height:{s}px;background:{bg};color:{color};'
            'border-radius:{br}px;font-size:{fs}px;font-weight:800;font-family:monospace;'
            'flex-shrink:0;border:1px solid rgba(255,255,255,0.12);'
            'box-shadow:0 2px 8px rgba(0,0,0,0.4);">{letter}</span>',
            extra=extra_class, s=size, bg=bg, color=color,
            br=br, fs=fs, letter=letter
        )

    # --- FOREX: flag emoji ---
    forex = FOREX_INFO.get(symbol)
    if forex or asset_type in ('forex', 'Forex'):
        flag = forex['flag'] if forex else '🌐'
        bg = forex['color'] if forex else '#1a3a5c'
        fs = max(size // 2, 10)
        return format_html(
            '<span class="asset-icon-forex {extra}" '
            'style="display:inline-flex;align-items:center;justify-content:center;'
            'width:{s}px;height:{s}px;background:{bg};'
            'border-radius:{br}px;font-size:{fs}px;flex-shrink:0;'
            'border:1px solid rgba(255,255,255,0.15);'
            'box-shadow:0 2px 8px rgba(0,0,0,0.4);">{flag}</span>',
            extra=extra_class, s=size, bg=bg, br=br, fs=fs, flag=flag
        )

    # --- FALLBACK: gradient circle with letter ---
    letter = symbol[0] if symbol else '?'
    fs = max(size // 3, 8)
    return format_html(
        '<span class="asset-icon {extra}" '
        'style="display:inline-flex;align-items:center;justify-content:center;'
        'width:{s}px;height:{s}px;border-radius:50%;'
        'background:linear-gradient(135deg,#0066ff,#00d4ff);color:#fff;'
        'font-weight:800;font-size:{fs}px;flex-shrink:0;">{letter}</span>',
        extra=extra_class, s=size, fs=fs, letter=letter
    )
