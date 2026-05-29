from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from trading.models import Asset, NewsArticle


def home(request):
    """Landing page"""
    featured_assets = Asset.objects.filter(is_featured=True, is_active=True)[:8]
    latest_news = NewsArticle.objects.filter(is_featured=True)[:3]
    
    context = {
        'featured_assets': featured_assets,
        'latest_news': latest_news,
    }
    return render(request, 'core/home.html', context)


def about(request):
    return render(request, 'core/about.html')


def markets(request):
    """Public markets page"""
    crypto_assets = Asset.objects.filter(asset_type='crypto', is_active=True)[:20]
    stock_assets = Asset.objects.filter(asset_type='stock', is_active=True)[:20]
    forex_assets = Asset.objects.filter(asset_type='forex', is_active=True)[:20]
    
    context = {
        'crypto_assets': crypto_assets,
        'stock_assets': stock_assets,
        'forex_assets': forex_assets,
    }
    return render(request, 'core/markets.html', context)


def contact(request):
    return render(request, 'core/contact.html')


def legal(request):
    return render(request, 'core/legal.html')


def faq(request):
    cuenta_faqs = [
        ('¿Cómo creo una cuenta en Nova Capital Group?', 'Haz clic en "Registrarse", completa el formulario con tu nombre, email y contraseña. Recibirás un email de verificación. Una vez verificado, podrás acceder a tu cuenta.'),
        ('¿Cuánto tiempo tarda la verificación de identidad (KYC)?', 'La verificación de identidad generalmente tarda entre 24 y 48 horas hábiles. Necesitarás subir una foto de tu documento de identidad y un comprobante de domicilio.'),
        ('¿Puedo tener múltiples cuentas?', 'No, cada persona solo puede tener una cuenta en Nova Capital Group. Tener múltiples cuentas viola nuestros términos de servicio.'),
        ('¿Cómo cambio mi contraseña?', 'Ve a Configuración > Seguridad > Cambiar Contraseña. También puedes usar la opción "¿Olvidaste tu contraseña?" en la página de login.'),
        ('¿Qué tipos de cuenta existen?', 'Ofrecemos 5 niveles: Basic (desde $100), Silver (desde $1,000), Gold (desde $5,000), Platinum (desde $20,000) y VIP Elite (desde $50,000). Cada nivel ofrece beneficios adicionales.'),
    ]
    deposito_faqs = [
        ('¿Cuál es el depósito mínimo?', 'El depósito mínimo es de $100 USD para cuentas Basic. Los métodos disponibles incluyen transferencia bancaria, tarjeta de crédito, criptomonedas y wire transfer.'),
        ('¿Cuánto tarda en acreditarse mi depósito?', 'Los depósitos via criptomoneda se acreditan en 1-2 horas. Las transferencias bancarias tardan 1-3 días hábiles. Las tarjetas de crédito se procesan en 24 horas.'),
        ('¿Cuál es el retiro mínimo?', 'El retiro mínimo es de $50 USD. Se aplica una comisión del 0.5% sobre el monto retirado.'),
        ('¿Cuánto tarda un retiro?', 'Los retiros son procesados en 2-5 días hábiles dependiendo del método. Los retiros en criptomoneda suelen ser más rápidos (24-48 horas).'),
        ('¿Qué métodos de pago aceptan?', 'Aceptamos transferencia bancaria (SEPA/SWIFT), tarjetas Visa/Mastercard, Bitcoin, Ethereum, USDT (TRC20/ERC20) y PayPal.'),
    ]
    trading_faqs = [
        ('¿Cómo ejecuto una operación de compra?', 'Ve al Mercado, selecciona el activo que deseas comprar, ingresa la cantidad en la pestaña "Comprar" y haz clic en "Comprar". La orden se ejecuta al precio de mercado actual.'),
        ('¿Qué es una orden límite?', 'Una orden límite te permite comprar o vender a un precio específico. La orden se ejecutará automáticamente cuando el mercado alcance ese precio.'),
        ('¿Cuál es la comisión por trading?', 'Cobramos una comisión del 0.1% por operación. Los usuarios VIP Elite tienen comisiones del 0%.'),
        ('¿Puedo operar las 24 horas?', 'Sí, los mercados de criptomonedas están disponibles 24/7. Las acciones y forex tienen horarios de mercado específicos.'),
        ('¿Cómo funciona el portafolio?', 'Tu portafolio muestra todos los activos que posees, su valor actual, precio promedio de compra y ganancia/pérdida en tiempo real.'),
    ]
    seguridad_faqs = [
        ('¿Qué es la autenticación de dos factores (2FA)?', 'El 2FA añade una capa extra de seguridad. Además de tu contraseña, necesitarás un código de 6 dígitos generado por una app como Google Authenticator o Authy.'),
        ('¿Cómo activo el 2FA?', 'Ve a Configuración > Seguridad > Activar 2FA. Escanea el código QR con tu app autenticadora y verifica con el código generado.'),
        ('¿Qué hago si sospecho que mi cuenta fue comprometida?', 'Cambia tu contraseña inmediatamente, activa el 2FA si no lo tienes, y contacta a nuestro soporte en support@novacapitalgroup.com.'),
        ('¿Cómo protegen mis fondos?', 'Utilizamos encriptación AES-256, almacenamiento en frío para el 95% de los activos digitales, y seguros contra hackeos. Los fondos de clientes están segregados de los fondos operativos.'),
        ('¿Qué información debo mantener confidencial?', 'Nunca compartas tu contraseña, códigos 2FA, ni claves privadas. Nova Capital Group nunca te pedirá esta información por email o chat.'),
    ]
    return render(request, 'core/faq.html', {
        'cuenta_faqs': cuenta_faqs,
        'deposito_faqs': deposito_faqs,
        'trading_faqs': trading_faqs,
        'seguridad_faqs': seguridad_faqs,
    })
