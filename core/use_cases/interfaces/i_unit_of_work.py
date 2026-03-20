# src/core/use_cases/interfaces/i_unit_of_work.py
from abc import ABC, abstractmethod


class IUnitOfWork(ABC):
    """
    Define uma interface (contrato) para a Unidade de Trabalho.
    Os Casos de Uso dependem desta abstração, não da implementação do MySQL.
    """

    @abstractmethod
    def __enter__(self):
        """Inicia a transação."""
        raise NotImplementedError

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Fecha a transação (commit/rollback)."""
        raise NotImplementedError

    @abstractmethod
    def commit(self):
        """Confirma a transação."""
        raise NotImplementedError

    @abstractmethod
    def rollback(self):
        """Reverte a transação."""
        raise NotImplementedError

    @property
    @abstractmethod
    def connection(self):
        """Fornece a conexão ativa para os repositórios."""
        raise NotImplementedError