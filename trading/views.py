import json
import logging
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils import timezone
from .models import Asset, Portfolio, Trade, WatchList, PriceAlert, NewsArticle
from accounts.models import UserWallet, Transaction

logger = logging.getLogger(__name__)


@login_required
def market_overview(request):
    """Main trading market page"""
    crypto_assets = Asset.objects.filter(asset_type='crypto', is_active=True)[:30]
    stock_assets = Asset.objects.filter(asset_type='stock', is_active=True)[:20]
    forex_assets = Asset.objects.filter(asset_type='forex', is_active=True)[:20]
    
    # User watchlist
    watchlist_ids = WatchList.objects.filter(user=request.user).values_list('asset_id', flat=True)
    
    context = {
        'crypto_assets': crypto_assets,
        'stock_assets': stock_assets,
        'forex_assets': forex_assets,
        'watchlist_ids': list(watchlist_ids),
    }
    return render(request, 'trading/market.html', context)


@login_required
def asset_detail(request, symbol):
    """Individual asset trading page"""
    asset = get_object_or_404(Asset, symbol=symbol.upper(), is_active=True)
    
    # User's position in this asset
    portfolio_item = Portfolio.objects.filter(user=request.user, asset=asset).first()
    
    # Recent trades for this asset
    recent_trades = Trade.objects.filter(user=request.user, asset=asset)[:10]
    
    # User's USD wallet
    usd_wallet = UserWallet.objects.filter(user=request.user, currency='USD').first()
    available_balance = usd_wallet.available_balance if usd_wallet else Decimal('0')
    
    # Watchlist status
    is_in_watchlist = WatchList.objects.filter(user=request.user, asset=asset).exists()
    
    # Price alerts
    alerts = PriceAlert.objects.filter(user=request.user, asset=asset, is_active=True)
    
    context = {
        'asset': asset,
        'portfolio_item': portfolio_item,
        'recent_trades': recent_trades,
        'available_balance': available_balance,
        'is_in_watchlist': is_in_watchlist,
        'alerts': alerts,
    }
    return render(request, 'trading/asset_detail.html', context)


@login_required
@require_POST
def execute_trade(request):
    """Execute a buy or sell trade"""
    try:
        data = json.loads(request.body)
        symbol = data.get('symbol', '').upper()
        trade_type = data.get('trade_type', '')
        quantity = Decimal(str(data.get('quantity', 0)))
        
        if not all([symbol, trade_type, quantity > 0]):
            return JsonResponse({'success': False, 'error': 'Datos inválidos'}, status=400)
        
        asset = get_object_or_404(Asset, symbol=symbol, is_active=True)
        
        price = asset.current_price
        total_value = quantity * price
        fee = total_value * Decimal(str(settings.NOVA_CAPITAL['TRADING_FEE_PERCENT'] / 100))
        
        usd_wallet, _ = UserWallet.objects.get_or_create(
            user=request.user,
            currency='USD',
            defaults={'balance': Decimal('0')}
        )
        
        if trade_type == 'buy':
            total_cost = total_value + fee
            if usd_wallet.available_balance < total_cost:
                return JsonResponse({'success': False, 'error': 'Saldo insuficiente'}, status=400)
            
            # Deduct USD
            usd_wallet.balance -= total_cost
            usd_wallet.save()
            
            # Update portfolio
            portfolio_item, created = Portfolio.objects.get_or_create(
                user=request.user,
                asset=asset,
                defaults={'quantity': Decimal('0'), 'average_buy_price': price, 'total_invested': Decimal('0')}
            )
            
            # Update average price
            if not created and portfolio_item.quantity > 0:
                total_qty = portfolio_item.quantity + quantity
                portfolio_item.average_buy_price = (
                    (portfolio_item.quantity * portfolio_item.average_buy_price + quantity * price) / total_qty
                )
            else:
                portfolio_item.average_buy_price = price
            
            portfolio_item.quantity += quantity
            portfolio_item.total_invested += total_value
            portfolio_item.save()
            
        elif trade_type == 'sell':
            portfolio_item = Portfolio.objects.filter(user=request.user, asset=asset).first()
            if not portfolio_item or portfolio_item.quantity < quantity:
                return JsonResponse({'success': False, 'error': 'No tienes suficientes activos'}, status=400)
            
            # Credit USD
            net_proceeds = total_value - fee
            usd_wallet.balance += net_proceeds
            usd_wallet.save()
            
            # Update portfolio
            portfolio_item.quantity -= quantity
            portfolio_item.total_invested -= (quantity * portfolio_item.average_buy_price)
            if portfolio_item.quantity <= 0:
                portfolio_item.delete()
            else:
                portfolio_item.save()
        else:
            return JsonResponse({'success': False, 'error': 'Tipo de operación inválido'}, status=400)
        
        # Record trade
        trade = Trade.objects.create(
            user=request.user,
            asset=asset,
            trade_type=trade_type,
            quantity=quantity,
            price=price,
            total_value=total_value,
            fee=fee,
            status='filled',
            filled_at=timezone.now(),
        )
        
        # Record transaction
        Transaction.objects.create(
            user=request.user,
            transaction_type=trade_type,
            amount=total_value,
            currency='USD',
            fee=fee,
            status='completed',
            description=f'{"Compra" if trade_type == "buy" else "Venta"} de {quantity} {symbol} @ ${price}',
            reference=str(trade.id)[:8].upper(),
        )
        
        return JsonResponse({
            'success': True,
            'message': f'{"Compra" if trade_type == "buy" else "Venta"} ejecutada exitosamente',
            'trade_id': str(trade.id),
            'new_balance': float(usd_wallet.balance),
        })
        
    except Exception as e:
        logger.error(f"Trade error for user {request.user.email}: {e}")
        return JsonResponse({'success': False, 'error': 'Error al procesar la operación'}, status=500)


@login_required
def portfolio(request):
    """User portfolio page"""
    portfolio_items = Portfolio.objects.filter(user=request.user).select_related('asset')
    
    total_invested = sum(item.total_invested for item in portfolio_items)
    total_current = sum(item.current_value for item in portfolio_items)
    total_pnl = total_current - total_invested
    total_pnl_percent = (total_pnl / total_invested * 100) if total_invested > 0 else 0
    
    usd_wallet = UserWallet.objects.filter(user=request.user, currency='USD').first()
    
    context = {
        'portfolio_items': portfolio_items,
        'total_invested': total_invested,
        'total_current': total_current,
        'total_pnl': total_pnl,
        'total_pnl_percent': total_pnl_percent,
        'usd_balance': usd_wallet.balance if usd_wallet else 0,
    }
    return render(request, 'trading/portfolio.html', context)


@login_required
def trade_history(request):
    """Trade history page"""
    trades = Trade.objects.filter(user=request.user).select_related('asset')
    
    asset_filter = request.GET.get('asset', '')
    if asset_filter:
        trades = trades.filter(asset__symbol=asset_filter.upper())
    
    context = {
        'trades': trades[:100],
        'asset_filter': asset_filter,
    }
    return render(request, 'trading/trade_history.html', context)


@login_required
def watchlist(request):
    """User watchlist"""
    items = WatchList.objects.filter(user=request.user).select_related('asset')
    return render(request, 'trading/watchlist.html', {'items': items})


@login_required
@require_POST
def toggle_watchlist(request):
    """Add/remove asset from watchlist"""
    symbol = request.POST.get('symbol', '').upper()
    asset = get_object_or_404(Asset, symbol=symbol)
    
    item, created = WatchList.objects.get_or_create(user=request.user, asset=asset)
    if not created:
        item.delete()
        return JsonResponse({'status': 'removed'})
    
    return JsonResponse({'status': 'added'})


def news(request):
    """Financial news page"""
    category = request.GET.get('category', '')
    articles = NewsArticle.objects.all()
    
    if category:
        articles = articles.filter(category=category)
    
    context = {
        'articles': articles[:30],
        'category': category,
        'categories': NewsArticle.CATEGORIES,
    }
    return render(request, 'trading/news.html', context)
