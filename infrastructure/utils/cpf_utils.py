# src/infrastructure/utils/cpf_utils.py
"""
Utilitários para validar, formatar e limpar CPFs.
"""
import re


def only_digits(cpf: str) -> str:
    """Remove todos os caracteres não numéricos de uma string."""
    return re.sub(r'\D', '', cpf or '')


def format_cpf(cpf: str) -> str:
    """Formata um CPF de 11 dígitos para o formato XXX.XXX.XXX-XX."""
    d = only_digits(cpf)
    if len(d) != 11:
        return cpf
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:11]}"


def is_valid_cpf(cpf: str) -> bool:
    """Valida um CPF pelos seus dígitos verificadores."""
    d = only_digits(cpf)
    if len(d) != 11 or d == d[0] * 11:
        return False

    def calc(digs):
        s = sum(int(digs[i]) * (len(digs) + 1 - i) for i in range(len(digs)))
        r = (s * 10) % 11
        return '0' if r == 10 else str(r)

    v1 = calc(d[:9])
    v2 = calc(d[:9] + v1)
    return d[-2:] == v1 + v2