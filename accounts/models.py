from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid


class User(AbstractUser):
    """Custom user model for Nova Capital Group"""
    
    ACCOUNT_TYPES = [
        ('basic', 'Basic'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
        ('vip', 'VIP Elite'),
    ]
    
    VERIFICATION_STATUS = [
        ('unverified', 'Sin Verificar'),
        ('pending', 'Pendiente'),
        ('verified', 'Verificado'),
        ('rejected', 'Rechazado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    # Account settings
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='basic')
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='unverified')
    is_2fa_enabled = models.BooleanField(default=False)
    
    # Security
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    
    # Referral
    referral_code = models.CharField(max_length=20, unique=True, blank=True)
    referred_by = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='referrals')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self._generate_referral_code()
        super().save(*args, **kwargs)
    
    def _generate_referral_code(self):
        import random
        import string
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        while User.objects.filter(referral_code=code).exists():
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return code
    
    @property
    def is_account_locked(self):
        if self.account_locked_until and self.account_locked_until > timezone.now():
            return True
        return False
    
    @property
    def account_level_display(self):
        levels = {
            'basic': {'name': 'Basic', 'color': '#6c757d', 'icon': '⭐'},
            'silver': {'name': 'Silver', 'color': '#adb5bd', 'icon': '⭐⭐'},
            'gold': {'name': 'Gold', 'color': '#ffc107', 'icon': '⭐⭐⭐'},
            'platinum': {'name': 'Platinum', 'color': '#0dcaf0', 'icon': '⭐⭐⭐⭐'},
            'vip': {'name': 'VIP Elite', 'color': '#6f42c1', 'icon': '👑'},
        }
        return levels.get(self.account_type, levels['basic'])


class UserWallet(models.Model):
    """User wallet/balance model"""
    
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('BTC', 'Bitcoin'),
        ('ETH', 'Ethereum'),
        ('USDT', 'Tether'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallets')
    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default='USD')
    balance = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    locked_balance = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'currency']
        verbose_name = 'Billetera'
        verbose_name_plural = 'Billeteras'
    
    def __str__(self):
        return f"{self.user.email} - {self.currency}: {self.balance}"
    
    @property
    def available_balance(self):
        return self.balance - self.locked_balance


class Transaction(models.Model):
    """Transaction history model"""
    
    TRANSACTION_TYPES = [
        ('deposit', 'Depósito'),
        ('withdrawal', 'Retiro'),
        ('buy', 'Compra'),
        ('sell', 'Venta'),
        ('fee', 'Comisión'),
        ('bonus', 'Bono'),
        ('referral', 'Referido'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('cancelled', 'Cancelado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    currency = models.CharField(max_length=10, default='USD')
    fee = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    description = models.TextField(blank=True)
    reference = models.CharField(max_length=100, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Transacción'
        verbose_name_plural = 'Transacciones'
    
    def __str__(self):
        return f"{self.user.email} - {self.transaction_type} - {self.amount} {self.currency}"


class DepositRequest(models.Model):
    """Deposit request model"""
    
    PAYMENT_METHODS = [
        ('bank_transfer', 'Transferencia Bancaria'),
        ('credit_card', 'Tarjeta de Crédito'),
        ('crypto', 'Criptomoneda'),
        ('paypal', 'PayPal'),
        ('wire', 'Wire Transfer'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deposit_requests')
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    proof_of_payment = models.ImageField(upload_to='deposits/', blank=True, null=True)
    notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Solicitud de Depósito'
        verbose_name_plural = 'Solicitudes de Depósito'


class WithdrawalRequest(models.Model):
    """Withdrawal request model"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('approved', 'Aprobado'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('rejected', 'Rechazado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='withdrawal_requests')
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    destination_address = models.CharField(max_length=200)
    destination_type = models.CharField(max_length=50, default='bank')
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Solicitud de Retiro'
        verbose_name_plural = 'Solicitudes de Retiro'


class LoginHistory(models.Model):
    """Login history for security tracking"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    success = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Historial de Acceso'
        verbose_name_plural = 'Historial de Accesos'
