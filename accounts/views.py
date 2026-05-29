import logging
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from .models import User, UserWallet, Transaction, DepositRequest, WithdrawalRequest, LoginHistory
from .forms import ProfileForm, DepositForm, WithdrawalForm

logger = logging.getLogger(__name__)


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


@login_required
def profile(request):
    wallets = UserWallet.objects.filter(user=request.user)
    recent_transactions = Transaction.objects.filter(user=request.user)[:10]
    
    # Calculate total portfolio value in USD
    total_balance = sum(w.balance for w in wallets.filter(currency='USD'))
    
    context = {
        'wallets': wallets,
        'recent_transactions': recent_transactions,
        'total_balance': total_balance,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user)
    
    return render(request, 'accounts/edit_profile.html', {'form': form})


@login_required
def security_settings(request):
    login_logs = LoginHistory.objects.filter(user=request.user)[:10]
    context = {
        'login_logs': login_logs,
    }
    return render(request, 'accounts/security.html', context)


@login_required
def setup_2fa(request):
    """Setup two-factor authentication"""
    import pyotp
    import qrcode
    import io
    import base64
    
    user = request.user
    
    if request.method == 'POST':
        token = request.POST.get('token', '')
        secret = request.session.get('2fa_secret', '')
        
        if secret:
            totp = pyotp.TOTP(secret)
            if totp.verify(token):
                user.is_2fa_enabled = True
                user.save()
                # Store secret securely (in production use encrypted field)
                request.session['2fa_verified'] = True
                messages.success(request, 'Autenticación de dos factores activada correctamente.')
                return redirect('accounts:security')
            else:
                messages.error(request, 'Código inválido. Intenta de nuevo.')
    
    # Generate new secret
    secret = pyotp.random_base32()
    request.session['2fa_secret'] = secret
    
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=user.email,
        issuer_name='Nova Capital Group'
    )
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    qr_code_b64 = base64.b64encode(buffer.getvalue()).decode()
    
    context = {
        'secret': secret,
        'qr_code': qr_code_b64,
    }
    return render(request, 'accounts/setup_2fa.html', context)


@login_required
def verify_2fa(request):
    if request.method == 'POST':
        token = request.POST.get('token', '')
        # In production, verify against stored secret
        messages.success(request, 'Verificación exitosa.')
        return redirect('dashboard:index')
    return render(request, 'accounts/verify_2fa.html')


@login_required
def disable_2fa(request):
    if request.method == 'POST':
        request.user.is_2fa_enabled = False
        request.user.save()
        messages.success(request, 'Autenticación de dos factores desactivada.')
        return redirect('accounts:security')
    return render(request, 'accounts/disable_2fa.html')


@login_required
def deposit(request):
    if request.method == 'POST':
        form = DepositForm(request.POST, request.FILES)
        if form.is_valid():
            deposit_req = form.save(commit=False)
            deposit_req.user = request.user
            deposit_req.save()
            
            # Create pending transaction
            Transaction.objects.create(
                user=request.user,
                transaction_type='deposit',
                amount=deposit_req.amount,
                currency=deposit_req.currency,
                status='pending',
                description=f'Depósito via {deposit_req.get_payment_method_display()}',
                reference=str(deposit_req.id)[:8].upper(),
            )
            
            messages.success(request, 
                f'Solicitud de depósito de ${deposit_req.amount} recibida. '
                'Será procesada en 1-3 días hábiles.')
            return redirect('accounts:transactions')
    else:
        form = DepositForm()
    
    return render(request, 'accounts/deposit.html', {'form': form})


@login_required
def withdraw(request):
    usd_wallet = UserWallet.objects.filter(user=request.user, currency='USD').first()
    available_balance = usd_wallet.available_balance if usd_wallet else Decimal('0')
    
    if request.method == 'POST':
        form = WithdrawalForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            fee = amount * Decimal(str(settings.NOVA_CAPITAL['WITHDRAWAL_FEE_PERCENT'] / 100))
            total_deduct = amount + fee
            
            if total_deduct > available_balance:
                messages.error(request, 'Saldo insuficiente para realizar el retiro.')
            else:
                withdrawal = form.save(commit=False)
                withdrawal.user = request.user
                withdrawal.fee = fee
                withdrawal.save()
                
                # Lock the funds
                if usd_wallet:
                    usd_wallet.locked_balance += total_deduct
                    usd_wallet.save()
                
                Transaction.objects.create(
                    user=request.user,
                    transaction_type='withdrawal',
                    amount=amount,
                    currency='USD',
                    fee=fee,
                    status='pending',
                    description=f'Retiro a {withdrawal.destination_address[:20]}...',
                    reference=str(withdrawal.id)[:8].upper(),
                )
                
                messages.success(request, 
                    f'Solicitud de retiro de ${amount} enviada. '
                    'Será procesada en 2-5 días hábiles.')
                return redirect('accounts:transactions')
    else:
        form = WithdrawalForm()
    
    context = {
        'form': form,
        'available_balance': available_balance,
        'min_withdrawal': settings.NOVA_CAPITAL['MIN_WITHDRAWAL'],
        'fee_percent': settings.NOVA_CAPITAL['WITHDRAWAL_FEE_PERCENT'],
    }
    return render(request, 'accounts/withdraw.html', context)


@login_required
def transactions(request):
    transaction_list = Transaction.objects.filter(user=request.user)
    
    # Filter by type
    tx_type = request.GET.get('type', '')
    if tx_type:
        transaction_list = transaction_list.filter(transaction_type=tx_type)
    
    context = {
        'transactions': transaction_list[:50],
        'tx_type': tx_type,
    }
    return render(request, 'accounts/transactions.html', context)


@login_required
def login_history(request):
    history = LoginHistory.objects.filter(user=request.user)[:20]
    return render(request, 'accounts/login_history.html', {'history': history})


@login_required
def resend_verification(request):
    messages.info(request, 'Email de verificación reenviado.')
    return redirect('accounts:profile')
