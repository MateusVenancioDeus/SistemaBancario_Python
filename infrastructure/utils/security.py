# src/infrastructure/utils/security.py
"""
Implementação da lógica de segurança (hash e verificação).
Suporta bcrypt (recomendado) e também comparação contra hashes MD5 legados.
"""

from typing import Optional
import bcrypt
import hashlib


def hash_password(plain_text_password: str) -> str:
    """
    Gera um hash bcrypt a partir da senha em texto puro.
    Retorna a string do hash (ex: '$2b$12$...').
    """
    if plain_text_password is None:
        raise ValueError("Password must not be None")
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(plain_text_password.encode("utf-8"), salt)
    return hashed_bytes.decode("utf-8")


def _is_bcrypt_hash(s: Optional[str]) -> bool:
    """Detecta se a string parece ser um hash bcrypt."""
    if not s:
        return False
    return s.startswith("$2a$") or s.startswith("$2b$") or s.startswith("$2y$")


def _is_md5_hash(s: Optional[str]) -> bool:
    """Detecta se a string parece ser um hash MD5 (32 hex chars)."""
    if not s or not isinstance(s, str):
        return False
    hexchars = "0123456789abcdefABCDEF"
    return len(s) == 32 and all(c in hexchars for c in s)


def verify_password(plain_text_password: str, hashed_password: Optional[str]) -> bool:
    """
    Verifica se a senha em texto puro corresponde ao hash armazenado.

    - Se o hash armazenado estiver no formato bcrypt, usa bcrypt.checkpw.
    - Se o hash armazenado parecer ser um MD5 (legado), compara MD5(plain) == hashed.
    - Retorna False em caso de input inválido ou erro.
    """
    if not plain_text_password or not hashed_password:
        return False

    try:
        # bcrypt
        if _is_bcrypt_hash(hashed_password):
            return bcrypt.checkpw(
                plain_text_password.encode("utf-8"),
                hashed_password.encode("utf-8"),
            )

        # legacy MD5 (compatibilidade com dados antigos)
        if _is_md5_hash(hashed_password):
            md5 = hashlib.md5(plain_text_password.encode("utf-8")).hexdigest()
            return md5 == hashed_password

        # Se não reconhece o formato, tenta bcrypt por segurança (pode lançar)
        try:
            return bcrypt.checkpw(
                plain_text_password.encode("utf-8"),
                hashed_password.encode("utf-8"),
            )
        except Exception:
            # desiste e retorna False
            return False

    except Exception:
        return False


# Mantém compatibilidade com código que chamava `check_password`
def check_password(plain_text_password: str, hashed_password: Optional[str]) -> bool:
    """
    Alias para verify_password — preserva compatibilidade com chamadas antigas.
    """
    return verify_password(plain_text_password, hashed_password)