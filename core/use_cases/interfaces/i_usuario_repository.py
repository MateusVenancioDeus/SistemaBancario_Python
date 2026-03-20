# Arquivo: src/core/use_cases/interfaces/i_usuario_repository.py (CONTRATO)

from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict, Union  # Importar Union
from src.core.use_cases.interfaces.i_unit_of_work import IUnitOfWork
from src.core.entities.usuario import Usuario
from decimal import Decimal


class IUsuarioRepository(ABC):
    """Interface (contrato) para o repositório de Usuários (v2)."""

    @abstractmethod
    def find_by_cpf_for_login(self, uow: IUnitOfWork, cpf: str) -> Optional[dict]:
        """Busca um usuário (cliente ou func) pelo CPF para login."""
        raise NotImplementedError
        # ... (todos os outros métodos abstratos) ...

    # ---
    # --- NOVOS MÉTODOS (Requisitos Avançados v4.0)
    # ---

    @abstractmethod
    def find_client_details_from_view(self, cpf: str) -> Optional[Dict[str, Any]]:
        """Busca dados de um cliente pela VIEW vw_consulta_cliente."""
        raise NotImplementedError

    # ... (outros métodos) ...

    @abstractmethod
    def update_password(self, uow: IUnitOfWork, id_usuario: int, new_hash: str):
        """Altera a senha de um usuário."""
        raise NotImplementedError

    @abstractmethod
    def call_proc_calcular_score(self, uow: IUnitOfWork, id_cliente: int) -> Union[
        int, Decimal]:  # Alterei o retorno para ser mais flexível
        """Chama a procedure de score e retorna o novo score."""
        raise NotImplementedError

    @abstractmethod
    def call_proc_desempenho_func(self, id_funcionario: int) -> Dict[str, Any]:
        """Chama a procedure de desempenho (read-only)."""
        raise NotImplementedError

    # 🆕 NOVO MÉTODO PARA REDEFINIÇÃO DE SENHA (A SER IMPLEMENTADO NA CLASSE CONCRETA)
    @abstractmethod
    def find_user_by_cpf_and_dob(self, cpf: str, data_nasc: str) -> Optional[Usuario]:
        """Busca o usuário cliente pelo CPF e Data de Nascimento para redefinição de senha."""
        pass

        # 🆕 NOVO MÉTODO PARA ALTERAÇÃO DE SENHA NA CONSULTA DE CONTA

    @abstractmethod
    def get_user_id_by_client_id(self, id_cliente: int) -> Optional[int]:
        """Busca o id_usuario a partir do id_cliente (necessário para alteração de senha por funcionário)."""
        pass