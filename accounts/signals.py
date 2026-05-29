"""
Signals for accounts app - auto-create wallets and log logins
"""
from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver
from django.utils import timezone


@receiver(post_save, sender='accounts.User')
def create_user_wallet(sender, instance, created, **kwargs):
    """Create default USD wallet when a new user registers"""
    if created:
        from accounts.models import UserWallet
        UserWallet.objects.get_or_create(
            user=instance,
            currency='USD',
            defaults={'balance': 0}
        )


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log successful login"""
    from accounts.models import LoginHistory
    ip = _get_ip(request)
    ua = request.META.get('HTTP_USER_AGENT', '')[:500]

    LoginHistory.objects.create(
        user=user,
        ip_address=ip,
        user_agent=ua,
        success=True,
    )

    # Update last login IP and reset failed attempts
    user.last_login_ip = ip
    user.failed_login_attempts = 0
    user.save(update_fields=['last_login_ip', 'failed_login_attempts'])


@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    """Log failed login and lock account after 5 attempts"""
    from accounts.models import User, LoginHistory
    ip = _get_ip(request)
    ua = request.META.get('HTTP_USER_AGENT', '')[:500]
    email = credentials.get('login', credentials.get('email', ''))

    try:
        user = User.objects.get(email=email)
        LoginHistory.objects.create(
            user=user,
            ip_address=ip,
            user_agent=ua,
            success=False,
        )
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.account_locked_until = timezone.now() + timezone.timedelta(minutes=30)
        user.save(update_fields=['failed_login_attempts', 'account_locked_until'])
    except Exception:
        pass


def _get_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')
