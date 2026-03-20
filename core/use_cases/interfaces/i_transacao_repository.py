from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from src.core.entities.conta import Transacao
from src.core.use_cases.interfaces.i_unit_of_work import IUnitOfWork


class ITransacaoRepository(ABC):
    """Interface (contrato) para o repositório de Transações (v2)."""

    @abstractmethod
    def get_statement(self, account_id: int) -> List[Transacao]:
        """Busca o extrato de uma conta."""
        raise NotImplementedError

    @abstractmethod
    def save(self, uow: IUnitOfWork, transacao: Transacao):
        """Salva uma nova transação (dentro de uma UoW)."""
        raise NotImplementedError

    # ---
    # --- NOVOS MÉTODOS (Requisitos Avançados v4.0)
    # ---

    @abstractmethod
    def get_movimentacoes_report_from_view(
        self,
        start_date: str,
        end_date: str,
        tipo_transacao: Optional[str] = None,
        id_agencia: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca o relatório avançado de movimentações usando a VIEW
        vw_relatorio_movimentacoes, com filtros.
        """
        raise NotImplementedError