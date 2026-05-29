# 🏦 Nova Capital Group

Plataforma profesional de inversión en criptomonedas, acciones y forex.

## 🚀 Inicio Rápido

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Aplicar migraciones
python manage.py migrate

# 3. Cargar datos del mercado (precios reales de CoinGecko)
python manage.py seed_data

# 4. Crear usuarios (admin + demo)
python create_admin.py

# 5. Iniciar servidor
python manage.py runserver
```

Abre **http://127.0.0.1:8000**

## 👤 Credenciales

| Rol | Email | Contraseña |
|-----|-------|------------|
| Admin | admin@novacapital.com | Admin1234! |
| Demo | demo@novacapital.com | Demo1234! |

- Panel Admin: http://127.0.0.1:8000/admin/

## ✨ Funcionalidades

- ✅ Registro e inicio de sesión seguro con verificación por email
- ✅ Autenticación de dos factores (2FA con TOTP)
- ✅ Dashboard completo con gráficos en tiempo real
- ✅ Mercado en vivo: Crypto, Acciones y Forex
- ✅ Gráficos TradingView integrados
- ✅ Sistema de trading (compra/venta)
- ✅ Portafolio con P&L en tiempo real
- ✅ Historial de transacciones
- ✅ Depósitos y retiros ficticios
- ✅ Tipos de cuenta: Basic, Silver, Gold, Platinum, VIP Elite
- ✅ Noticias financieras
- ✅ Watchlist personalizada
- ✅ Panel administrativo completo
- ✅ Protección CSRF, rate limiting, headers de seguridad
- ✅ Diseño responsive (móvil y escritorio)
- ✅ Precios reales via CoinGecko API

## 🔒 Seguridad

- Headers de seguridad (CSP, HSTS, X-Frame-Options)
- Rate limiting en endpoints sensibles
- Bloqueo de cuenta tras 5 intentos fallidos
- Historial de accesos con IP
- Encriptación de sesiones
- Protección CSRF en todos los formularios
# Nova_Capital
