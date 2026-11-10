"""Sesión web de evaluación SOLO para API DEMO; ninguna clave se envía al bundle React.

La autenticación de técnicos por FASE8_DEMO_TOKEN sigue siendo independiente.
No importar este módulo desde app.main (producción FULL).
"""
import hashlib
import hmac
import os
import secrets
import time

COOKIE = "__Host-bodegas_eval"
DURACION_SEGUNDOS = 2 * 60 * 60
FALLOS_MAX = 8
VENTANA_SEGUNDOS = 15 * 60
_fallos: dict[str, list[float]] = {}


def habilitado() -> bool:
    return os.getenv("FASE8_EVAL_ENABLED") == "1"


def configuracion_segura() -> bool:
    if not habilitado():
        return False
    clave = os.getenv("FASE8_EVAL_PASSWORD", "")
    firma = os.getenv("FASE8_EVAL_SIGNING_KEY", "")
    tecnico = os.getenv("FASE8_DEMO_TOKEN", "")
    if (len(clave) < 20 or len(firma) < 48 or
            clave == tecnico or firma == tecnico or clave == firma):
        raise ValueError("Configuracion web DEMO incompleta o insegura")
    return True


def comprobar_clave(clave: str, origen: str) -> tuple[bool, bool]:
    """Devuelve (correcta, limite_superado); sin loguear clave u origen."""
    configuracion_segura()
    ahora = time.monotonic()
    # Limitar memoria en un servicio gratuito expuesto a internet.
    if len(_fallos) > 512:
        _fallos.clear()
    fallos = [t for t in _fallos.get(origen, []) if ahora - t < VENTANA_SEGUNDOS]
    if len(fallos) >= FALLOS_MAX:
        _fallos[origen] = fallos
        return False, True
    esperado = os.environ["FASE8_EVAL_PASSWORD"]
    correcta = hmac.compare_digest(
        hashlib.sha256(clave.encode("utf-8")).digest(),
        hashlib.sha256(esperado.encode("utf-8")).digest(),
    )
    if correcta:
        _fallos.pop(origen, None)
    else:
        fallos.append(ahora)
        _fallos[origen] = fallos
    return correcta, False


def _firmar(texto: str) -> str:
    clave = os.environ["FASE8_EVAL_SIGNING_KEY"].encode("utf-8")
    return hmac.new(clave, texto.encode("ascii"), hashlib.sha256).hexdigest()


def crear_sesion() -> str:
    configuracion_segura()
    contenido = f"{int(time.time()) + DURACION_SEGUNDOS}.{secrets.token_hex(24)}"
    return contenido + "." + _firmar("sesion:" + contenido)


def validar_sesion(cookie: str | None) -> bool:
    if not habilitado() or not cookie or len(cookie) > 256:
        return False
    try:
        vencimiento, nonce, firma = cookie.split(".")
        exp = int(vencimiento)
        ahora = int(time.time())
        if (not vencimiento.isdecimal() or len(nonce) != 48 or
                not all(c in "0123456789abcdef" for c in nonce) or
                len(firma) != 64 or
                exp <= ahora or exp > ahora + DURACION_SEGUNDOS):
            return False
        return hmac.compare_digest(
            firma, _firmar("sesion:" + vencimiento + "." + nonce),
        )
    except (ValueError, UnicodeError):
        return False


def token_csrf(cookie: str) -> str:
    if not validar_sesion(cookie):
        raise ValueError("Sesion de evaluador invalida")
    return _firmar("csrf:" + cookie)


def csrf_valido(cookie: str, recibido: str | None) -> bool:
    return bool(recibido and len(recibido) == 64 and
                validar_sesion(cookie) and
                hmac.compare_digest(recibido, token_csrf(cookie)))
