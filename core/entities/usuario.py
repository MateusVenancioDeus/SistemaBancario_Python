from dataclasses import dataclass
from typing import Optional
from src.infrastructure.utils.security import verify_password
from datetime import date
from decimal import Decimal  # <-- ADICIONE ESTA IMPORTAÇÃO


@dataclass
class Usuario:
    """
    Entidade de domínio que representa um usuário do sistema (cliente ou funcionário).
    (Versão 2: Atualizada com todos os novos campos do SQL v4.0)
    """
    id_usuario: int
    nome: str
    cpf: str
    senha_hash: str
    tipo_usuario: str  # 'CLIENTE' ou 'FUNCIONARIO'

    # Campos que podem vir do banco
    status: str = "ATIVO"
    tentativas_login: Optional[int] = 0
    id_cliente: Optional[int] = None
    data_nascimento: Optional[date] = None
    endereco: Optional[str] = None
    telefone: Optional[str] = None  # NOVO CAMPO ADICIONADO
    score_credito: Optional[int] = 500  # NOVO CAMPO ADICIONADO

    # --- Campos específicos de FUNCIONARIO ---
    cargo: Optional[str] = None
    salario: Optional[Decimal] = None
    id_funcionario: Optional[int] = None  # NOVO CAMPO ADICIONADO
    id_agencia: Optional[int] = None  # NOVO CAMPO ADICIONADO

    @staticmethod
    def from_dict(data: dict) -> "Usuario":
        """
        Constrói uma instância de Usuario a partir de um dicionário (linha do banco).
        """
        # Converte salário para Decimal, se existir
        salario_val = data.get("salario")
        salario_decimal = Decimal(salario_val) if salario_val is not None else None

        return Usuario(
            id_usuario=data.get("id_usuario"),
            nome=data.get("nome"),
            cpf=data.get("cpf"),
            senha_hash=data.get("senha_hash"),
            tipo_usuario=data.get("tipo_usuario"),
            status=data.get("status", "ATIVO"),
            tentativas_login=data.get("tentativas_login", 0),
            data_nascimento=data.get("data_nascimento"),
            endereco=data.get("endereco"),
            telefone=data.get("telefone"),

            # --- Campos de Cliente ---
            id_cliente=data.get("id_cliente"),
            score_credito=data.get("score_credito", 500),

            # --- Campos de Funcionário ---
            id_funcionario=data.get("id_funcionario"),
            id_agencia=data.get("id_agencia"),
            cargo=data.get("cargo"),
            salario=salario_decimal
        )

    @property
    def is_ativo(self) -> bool:
        return self.status.upper() == "ATIVO"

    def verificar_senha(self, senha: str) -> bool:
        """
        Verifica se a senha informada confere com o hash armazenado (MD5 ou bcrypt).
        """
        return verify_password(senha, self.senha_hash)

    @property
    def is_bloqueado_por_tentativas(self, limite: int = 5) -> bool:
        return (self.tentativas_login or 0) >= limite