from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserWallet, Transaction, DepositRequest, WithdrawalRequest, LoginHistory


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'get_full_name', 'account_type', 'verification_status', 
                    'is_2fa_enabled', 'is_active', 'created_at']
    list_filter = ['account_type', 'verification_status', 'is_active', 'is_2fa_enabled']
    search_fields = ['email', 'first_name', 'last_name', 'username']
    ordering = ['-created_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Nova Capital Info', {
            'fields': ('phone', 'country', 'city', 'account_type', 'verification_status',
                      'is_2fa_enabled', 'referral_code', 'referred_by')
        }),
        ('Security', {
            'fields': ('last_login_ip', 'failed_login_attempts', 'account_locked_until')
        }),
    )


@admin.register(UserWallet)
class UserWalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'currency', 'balance', 'locked_balance', 'updated_at']
    list_filter = ['currency']
    search_fields = ['user__email']
    
    actions = ['credit_demo_funds']
    
    def credit_demo_funds(self, request, queryset):
        for wallet in queryset.filter(currency='USD'):
            wallet.balance += 10000
            wallet.save()
        self.message_user(request, f'Fondos demo acreditados.')
    credit_demo_funds.short_description = 'Acreditar $10,000 demo'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'transaction_type', 'amount', 'currency', 'status', 'created_at']
    list_filter = ['transaction_type', 'status', 'currency']
    search_fields = ['user__email', 'reference']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(DepositRequest)
class DepositRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'currency', 'payment_method', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'currency']
    search_fields = ['user__email']
    ordering = ['-created_at']
    
    actions = ['approve_deposits', 'reject_deposits']
    
    def approve_deposits(self, request, queryset):
        from accounts.models import UserWallet, Transaction
        for deposit in queryset.filter(status='pending'):
            # Credit user wallet
            wallet, _ = UserWallet.objects.get_or_create(
                user=deposit.user,
                currency=deposit.currency,
                defaults={'balance': 0}
            )
            wallet.balance += deposit.amount
            wallet.save()
            
            # Update transaction status
            Transaction.objects.filter(
                user=deposit.user,
                reference=str(deposit.id)[:8].upper()
            ).update(status='completed')
            
            deposit.status = 'approved'
            deposit.save()
        
        self.message_user(request, f'{queryset.count()} depósitos aprobados.')
    approve_deposits.short_description = 'Aprobar depósitos seleccionados'
    
    def reject_deposits(self, request, queryset):
        queryset.filter(status='pending').update(status='rejected')
        self.message_user(request, 'Depósitos rechazados.')
    reject_deposits.short_description = 'Rechazar depósitos seleccionados'


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'currency', 'destination_type', 'status', 'created_at']
    list_filter = ['status', 'destination_type']
    search_fields = ['user__email', 'destination_address']
    ordering = ['-created_at']


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'success', 'created_at']
    list_filter = ['success']
    search_fields = ['user__email', 'ip_address']
    ordering = ['-created_at']
    readonly_fields = ['user', 'ip_address', 'user_agent', 'success', 'created_at']
