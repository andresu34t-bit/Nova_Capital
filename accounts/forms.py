from django import forms
from django.conf import settings
from decimal import Decimal
from .models import User, DepositRequest, WithdrawalRequest


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'country', 'city', 'address', 
                  'date_of_birth', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 234 567 8900'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'País'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ciudad'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }


class DepositForm(forms.ModelForm):
    class Meta:
        model = DepositRequest
        fields = ['amount', 'currency', 'payment_method', 'proof_of_payment', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': '0.00',
                'min': '100',
                'step': '0.01',
            }),
            'currency': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'payment_method': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'proof_of_payment': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notas adicionales...'}),
        }
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        min_deposit = Decimal(str(settings.NOVA_CAPITAL['MIN_DEPOSIT']))
        max_deposit = Decimal(str(settings.NOVA_CAPITAL['MAX_DEPOSIT']))
        
        if amount < min_deposit:
            raise forms.ValidationError(f'El depósito mínimo es ${min_deposit}')
        if amount > max_deposit:
            raise forms.ValidationError(f'El depósito máximo es ${max_deposit:,}')
        return amount


class WithdrawalForm(forms.ModelForm):
    class Meta:
        model = WithdrawalRequest
        fields = ['amount', 'destination_address', 'destination_type', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': '0.00',
                'min': '50',
                'step': '0.01',
            }),
            'destination_address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'IBAN, dirección crypto o cuenta bancaria',
            }),
            'destination_type': forms.Select(
                choices=[
                    ('bank', 'Cuenta Bancaria'),
                    ('crypto_btc', 'Bitcoin (BTC)'),
                    ('crypto_eth', 'Ethereum (ETH)'),
                    ('crypto_usdt', 'USDT (TRC20)'),
                    ('paypal', 'PayPal'),
                    ('wire', 'Wire Transfer'),
                ],
                attrs={'class': 'form-select'}
            ),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        min_withdrawal = Decimal(str(settings.NOVA_CAPITAL['MIN_WITHDRAWAL']))
        if amount < min_withdrawal:
            raise forms.ValidationError(f'El retiro mínimo es ${min_withdrawal}')
        return amount
