from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from accounts.models import UserWallet, Transaction
from trading.models import Portfolio, Trade, Asset, NewsArticle


@login_required
def index(request):
    """Main dashboard"""
    user = request.user
    
    # Wallets
    wallets = UserWallet.objects.filter(user=user)
    usd_wallet = wallets.filter(currency='USD').first()
    total_balance = usd_wallet.balance if usd_wallet else 0
    
    # Portfolio summary
    portfolio_items = Portfolio.objects.filter(user=user).select_related('asset')
    total_portfolio_value = sum(item.current_value for item in portfolio_items)
    total_invested = sum(item.total_invested for item in portfolio_items)
    total_pnl = total_portfolio_value - total_invested
    
    # Recent transactions
    recent_transactions = Transaction.objects.filter(user=user)[:5]
    
    # Recent trades
    recent_trades = Trade.objects.filter(user=user).select_related('asset')[:5]
    
    # Featured assets for quick trade
    featured_assets = Asset.objects.filter(is_featured=True, is_active=True)[:6]
    
    # Latest news
    latest_news = NewsArticle.objects.all()[:4]
    
    # Stats
    total_trades = Trade.objects.filter(user=user, status='filled').count()
    total_deposits = Transaction.objects.filter(
        user=user, transaction_type='deposit', status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'total_balance': total_balance,
        'total_portfolio_value': total_portfolio_value,
        'total_invested': total_invested,
        'total_pnl': total_pnl,
        'total_pnl_percent': (total_pnl / total_invested * 100) if total_invested > 0 else 0,
        'recent_transactions': recent_transactions,
        'recent_trades': recent_trades,
        'portfolio_items': portfolio_items[:5],
        'featured_assets': featured_assets,
        'latest_news': latest_news,
        'total_trades': total_trades,
        'total_deposits': total_deposits,
        'wallets': wallets,
    }
    return render(request, 'dashboard/index.html', context)
