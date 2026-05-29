"""
Script para crear cuentas de demostración en Nova Capital Group.
Ejecutar en Render Shell: python create_users.py
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nova_capital.settings')
django.setup()

from accounts.models import User, UserWallet

users = [
    # (username, email, password, first_name, last_name, account_type, balance, is_staff)
    ('admin',     'admin@novacapital.com',   'Admin1234!',    'Admin',    'Nova Capital', 'vip',      100000, True),
    ('carlos',    'carlos@novacapital.com',  'Carlos1234!',   'Carlos',   'Mendoza',      'platinum',  75000, False),
    ('sofia',     'sofia@novacapital.com',   'Sofia1234!',    'Sofía',    'Ramírez',      'gold',      50000, False),
    ('miguel',    'miguel@novacapital.com',  'Miguel1234!',   'Miguel',   'Torres',       'silver',    20000, False),
    ('ana',       'ana@novacapital.com',     'Ana12345!',     'Ana',      'García',       'basic',      5000, False),
    ('demo',      'demo@novacapital.com',    'Demo1234!',     'Demo',     'Usuario',      'gold',      25000, False),
]

print("\n🚀 Creando cuentas en Nova Capital Group...\n")

for username, email, password, first_name, last_name, account_type, balance, is_staff in users:
    if User.objects.filter(email=email).exists():
        print(f"⚠️  Ya existe: {email}")
        continue

    if is_staff:
        u = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
    else:
        u = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

    u.account_type = account_type
    u.verification_status = 'verified'
    u.save()

    UserWallet.objects.get_or_create(
        user=u,
        currency='USD',
        defaults={'balance': balance}
    )

    print(f"✅ {first_name} {last_name} | {email} | {password} | {account_type.upper()} | ${balance:,}")

print("\n📋 Resumen de cuentas:\n")
print(f"{'Email':<35} {'Contraseña':<15} {'Tipo':<12} {'Saldo'}")
print("-" * 75)
for username, email, password, first_name, last_name, account_type, balance, is_staff in users:
    rol = "ADMIN" if is_staff else account_type.upper()
    print(f"{email:<35} {password:<15} {rol:<12} ${balance:,}")

print("\n✅ Listo. Entra en /accounts/login/ o /admin/\n")
