from django.conf import settings


def global_context(request):
    """Global context available in all templates"""
    nova_settings = settings.NOVA_CAPITAL
    
    context = {
        'PLATFORM_NAME': nova_settings['PLATFORM_NAME'],
        'PLATFORM_TAGLINE': nova_settings['PLATFORM_TAGLINE'],
        'SUPPORT_EMAIL': nova_settings['SUPPORT_EMAIL'],
    }
    
    if request.user.is_authenticated:
        try:
            from accounts.models import UserWallet
            usd_wallet = UserWallet.objects.filter(user=request.user, currency='USD').first()
            context['user_usd_balance'] = usd_wallet.balance if usd_wallet else 0
        except Exception:
            context['user_usd_balance'] = 0
    
    return context
