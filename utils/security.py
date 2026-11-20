import hashlib
import hmac
import os


def encriptar_password(password_plana: str) -> str:
    """
    Encripta la contraseña usando PBKDF2-HMAC-SHA256 con salt aleatorio de 16 bytes.
    Retorna una cadena con formato 'salt$hash' (97 caracteres).
    """
    salt = os.urandom(16).hex()
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password_plana.encode("utf-8"),
        bytes.fromhex(salt),
        100_000
    ).hex()
    return f"{salt}${dk}"


def verificar_password(password_plana: str, hash_guardado: str) -> bool:
    """
    Verifica una contraseña en texto plano contra el hash almacenado en MySQL.
    """
    if not hash_guardado or "$" not in hash_guardado:
        return False

    salt, hash_original = hash_guardado.split("$", 1)
    try:
        dk = hashlib.pbkdf2_hmac(
            "sha256",
            password_plana.encode("utf-8"),
            bytes.fromhex(salt),
            100_000
        ).hex()
    except ValueError:
        return False

    return hmac.compare_digest(dk, hash_original)