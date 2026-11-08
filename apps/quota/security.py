
import hashlib
import hmac

from django.conf import settings


def get_client_ip(request):
    """
    Obtiene la IP de la conexión directa.
    No confía en cabeceras enviadas por el cliente.
    """
    return request.META.get('REMOTE_ADDR', '')


def hash_ip(ip_address):
    """
    Convierte la IP en una huella HMAC-SHA256.
    No devuelve ni almacena la IP original.
    """
    if not ip_address:
        return ''

    secret = settings.SECRET_KEY.encode('utf-8')
    message = ip_address.encode('utf-8')

    return hmac.new(
        secret,
        message,
        hashlib.sha256
    ).hexdigest()


def get_request_ip_hash(request):
    ip_address = get_client_ip(request)
    return hash_ip(ip_address)
