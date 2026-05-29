"""
Genera datos falsos pero realistas para Nova Capital Group
Simula historial de transacciones, trades, portafolios de múltiples usuarios
"""
import random
import decimal
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction as db_transaction


class Command(BaseCommand):
    help = 'Genera datos realistas de transacciones, trades y portafolios'

    def handle(self, *args, **options):
        from accounts.models import User, UserWallet, Transaction, DepositRequest, WithdrawalRequest
        from trading.models import Asset, Portfolio, Trade

        self.stdout.write(self.style.MIGRATE_HEADING('💰 Generando datos realistas...'))

        # Obtener activos
        crypto_assets = list(Asset.objects.filter(asset_type='crypto', is_active=True))
        stock_assets  = list(Asset.objects.filter(asset_type='stock',  is_active=True))
        all_assets    = crypto_assets + stock_assets

        if not all_assets:
            self.stdout.write(self.style.ERROR('No hay activos. Ejecuta seed_data primero.'))
            return

        # ── Usuarios demo adicionales ──────────────────────────────────────
        demo_users_data = [
            ('carlos.mendez',  'carlos.mendez@gmail.com',  'Carlos',   'Mendez',   'gold',     45820.50),
            ('sofia.ramirez',  'sofia.ramirez@hotmail.com','Sofia',    'Ramirez',  'platinum', 128340.00),
            ('andres.torres',  'andres.torres@yahoo.com',  'Andres',   'Torres',   'silver',   12500.75),
            ('maria.garcia',   'maria.garcia@gmail.com',   'Maria',    'Garcia',   'vip',      385000.00),
            ('luis.hernandez', 'luis.hernandez@gmail.com', 'Luis',     'Hernandez','basic',     3200.00),
            ('ana.lopez',      'ana.lopez@outlook.com',    'Ana',      'Lopez',    'gold',      67450.25),
            ('pedro.silva',    'pedro.silva@gmail.com',    'Pedro',    'Silva',    'platinum', 210000.00),
            ('valentina.ruiz', 'valentina.ruiz@gmail.com', 'Valentina','Ruiz',     'silver',    8900.00),
        ]

        users = []
        for username, email, first, last, acct, balance in demo_users_data:
            u, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first,
                    'last_name': last,
                    'account_type': acct,
                    'verification_status': 'verified',
                    'is_active': True,
                }
            )
            if created:
                u.set_password('Demo1234!')
                u.save()
            wallet, _ = UserWallet.objects.get_or_create(
                user=u, currency='USD',
                defaults={'balance': decimal.Decimal(str(balance))}
            )
            if not created:
                wallet.balance = decimal.Decimal(str(balance))
                wallet.save()
            users.append(u)
            status = '✓ Creado' if created else '↻ Actualizado'
            self.stdout.write(f'  {status}: {first} {last} (${balance:,.2f})')

        # Incluir usuario demo original
        try:
            demo = User.objects.get(username='demo')
            users.append(demo)
        except User.DoesNotExist:
            pass

        self.stdout.write(f'\n📊 Generando historial para {len(users)} usuarios...')

        for user in users:
            self._generate_user_history(user, all_assets, crypto_assets)

        # ── Estadísticas globales ──────────────────────────────────────────
        total_tx    = Transaction.objects.count()
        total_trades = Trade.objects.count()
        total_dep   = DepositRequest.objects.count()
        total_with  = WithdrawalRequest.objects.count()

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Datos generados:\n'
            f'   • {total_tx} transacciones\n'
            f'   • {total_trades} operaciones de trading\n'
            f'   • {total_dep} solicitudes de depósito\n'
            f'   • {total_with} solicitudes de retiro\n'
        ))

    # ──────────────────────────────────────────────────────────────────────
    def _generate_user_history(self, user, all_assets, crypto_assets):
        from accounts.models import UserWallet, Transaction, DepositRequest, WithdrawalRequest
        from trading.models import Portfolio, Trade

        now = timezone.now()

        # Cuántos meses de historial según nivel de cuenta
        months = {'basic': 2, 'silver': 4, 'gold': 8, 'platinum': 14, 'vip': 20}.get(user.account_type, 3)

        # ── 1. Depósitos ──────────────────────────────────────────────────
        deposit_amounts = {
            'basic':    [500, 1000, 500],
            'silver':   [1000, 2500, 1000, 2000],
            'gold':     [5000, 10000, 5000, 8000, 3000],
            'platinum': [20000, 15000, 25000, 10000, 30000],
            'vip':      [50000, 75000, 100000, 50000, 80000, 30000],
        }
        amounts = deposit_amounts.get(user.account_type, [1000])
        methods = ['bank_transfer', 'credit_card', 'crypto', 'wire']

        for i, amount in enumerate(amounts):
            days_ago = random.randint(i * 15 + 5, i * 15 + 30)
            created_at = now - timedelta(days=days_ago)
            dep = DepositRequest.objects.create(
                user=user,
                amount=decimal.Decimal(str(amount)),
                currency='USD',
                payment_method=random.choice(methods),
                status='approved',
                created_at=created_at,
                updated_at=created_at,
            )
            Transaction.objects.create(
                user=user,
                transaction_type='deposit',
                amount=decimal.Decimal(str(amount)),
                currency='USD',
                fee=decimal.Decimal('0'),
                status='completed',
                description=f'Depósito via {dep.get_payment_method_display()}',
                reference=str(dep.id)[:8].upper(),
                created_at=created_at,
                updated_at=created_at,
            )

        # ── 2. Trades y portafolio ────────────────────────────────────────
        num_trades = {'basic': 8, 'silver': 20, 'gold': 45, 'platinum': 90, 'vip': 150}.get(user.account_type, 10)

        # Seleccionar activos favoritos del usuario (2-6 activos)
        num_fav = min(random.randint(2, 6), len(all_assets))
        fav_assets = random.sample(all_assets, num_fav)

        portfolio_data = {}  # symbol -> {qty, avg_price, total_invested}

        for i in range(num_trades):
            asset = random.choice(fav_assets)
            days_ago = random.randint(1, months * 30)
            trade_time = now - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))

            price = float(asset.current_price)
            # Simular precio histórico con variación ±30%
            hist_price = price * random.uniform(0.70, 1.30)
            hist_price = max(hist_price, 0.0001)

            # Determinar tipo de trade
            sym = asset.symbol
            has_position = sym in portfolio_data and portfolio_data[sym]['qty'] > 0

            if not has_position or random.random() < 0.65:
                trade_type = 'buy'
            else:
                trade_type = 'sell'

            # Calcular cantidad según saldo del usuario
            usd_amount = random.uniform(50, min(2000, float(asset.current_price) * 10))
            quantity = decimal.Decimal(str(round(usd_amount / hist_price, 8)))
            hist_price_dec = decimal.Decimal(str(round(hist_price, 8)))
            total_value = quantity * hist_price_dec
            fee = total_value * decimal.Decimal('0.001')

            trade = Trade.objects.create(
                user=user,
                asset=asset,
                trade_type=trade_type,
                order_type='market',
                quantity=quantity,
                price=hist_price_dec,
                total_value=total_value,
                fee=fee,
                status='filled',
                created_at=trade_time,
                updated_at=trade_time,
                filled_at=trade_time,
            )

            # Actualizar portafolio en memoria
            if trade_type == 'buy':
                if sym not in portfolio_data:
                    portfolio_data[sym] = {'qty': decimal.Decimal('0'), 'avg': hist_price_dec, 'invested': decimal.Decimal('0'), 'asset': asset}
                pd = portfolio_data[sym]
                new_qty = pd['qty'] + quantity
                if new_qty > 0:
                    pd['avg'] = (pd['qty'] * pd['avg'] + quantity * hist_price_dec) / new_qty
                pd['qty'] = new_qty
                pd['invested'] += total_value
            else:
                if sym in portfolio_data:
                    pd = portfolio_data[sym]
                    pd['qty'] = max(decimal.Decimal('0'), pd['qty'] - quantity)
                    pd['invested'] = max(decimal.Decimal('0'), pd['invested'] - total_value)

            # Registrar transacción
            Transaction.objects.create(
                user=user,
                transaction_type=trade_type,
                amount=total_value,
                currency='USD',
                fee=fee,
                status='completed',
                description=f'{"Compra" if trade_type == "buy" else "Venta"} {quantity} {sym} @ ${hist_price_dec:.2f}',
                reference=str(trade.id)[:8].upper(),
                created_at=trade_time,
                updated_at=trade_time,
            )

        # ── 3. Guardar portafolio real ────────────────────────────────────
        for sym, pd in portfolio_data.items():
            if pd['qty'] > decimal.Decimal('0.00000001'):
                Portfolio.objects.update_or_create(
                    user=user,
                    asset=pd['asset'],
                    defaults={
                        'quantity': pd['qty'],
                        'average_buy_price': pd['avg'],
                        'total_invested': pd['invested'],
                    }
                )

        # ── 4. Retiros ────────────────────────────────────────────────────
        num_withdrawals = {'basic': 0, 'silver': 1, 'gold': 2, 'platinum': 3, 'vip': 4}.get(user.account_type, 1)
        dest_types = ['bank', 'crypto_btc', 'crypto_eth', 'crypto_usdt', 'wire']
        dest_addresses = [
            'ES91 2100 0418 4502 0005 1332',
            '1A1zP1eP5QGefi2DMPTfTL5SLmv7Divf',
            '0x742d35Cc6634C0532925a3b8D4C9B8A1',
            'TQn9Y2khEsLJW1ChVWFMSMeRDow5KcbLSE',
            'IBAN DE89 3704 0044 0532 0130 00',
        ]

        for i in range(num_withdrawals):
            w_amount = random.choice([500, 1000, 2000, 5000, 10000])
            fee = decimal.Decimal(str(w_amount)) * decimal.Decimal('0.005')
            days_ago = random.randint(5, months * 25)
            w_time = now - timedelta(days=days_ago)

            wr = WithdrawalRequest.objects.create(
                user=user,
                amount=decimal.Decimal(str(w_amount)),
                currency='USD',
                destination_address=random.choice(dest_addresses),
                destination_type=random.choice(dest_types),
                fee=fee,
                status=random.choice(['completed', 'completed', 'completed', 'processing']),
                created_at=w_time,
                updated_at=w_time,
            )
            Transaction.objects.create(
                user=user,
                transaction_type='withdrawal',
                amount=decimal.Decimal(str(w_amount)),
                currency='USD',
                fee=fee,
                status='completed',
                description=f'Retiro a {wr.destination_address[:20]}...',
                reference=str(wr.id)[:8].upper(),
                created_at=w_time,
                updated_at=w_time,
            )

        # ── 5. Bonos de bienvenida ────────────────────────────────────────
        if user.account_type in ('gold', 'platinum', 'vip'):
            bonus = {'gold': 50, 'platinum': 150, 'vip': 500}.get(user.account_type, 0)
            bonus_time = now - timedelta(days=months * 30 - 1)
            Transaction.objects.create(
                user=user,
                transaction_type='bonus',
                amount=decimal.Decimal(str(bonus)),
                currency='USD',
                fee=decimal.Decimal('0'),
                status='completed',
                description=f'Bono de bienvenida cuenta {user.get_account_type_display()}',
                reference='BONUS' + str(random.randint(1000, 9999)),
                created_at=bonus_time,
                updated_at=bonus_time,
            )

        self.stdout.write(f'  ✓ {user.get_full_name()}: {Trade.objects.filter(user=user).count()} trades, '
                          f'{Transaction.objects.filter(user=user).count()} transacciones')
