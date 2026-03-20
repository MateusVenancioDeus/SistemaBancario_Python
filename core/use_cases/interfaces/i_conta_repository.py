from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict
from src.core.entities.conta import Conta, CaixinhaInvestimento
from src.core.use_cases.interfaces.i_unit_of_work import IUnitOfWork
from decimal import Decimal


class IContaRepository(ABC):
    """Interface (contrato) para o repositório de Contas."""

    # --- Métodos de Leitura (não transacionais) ---

    @abstractmethod
    def find_by_cliente_id(self, cliente_id: int) -> List[Conta]:
        """Busca contas pelo ID do cliente."""
        raise NotImplementedError

    @abstractmethod
    def find_caixinhas_by_conta_id(self, conta_id: int) -> List[CaixinhaInvestimento]:
        """Busca todas as caixinhas de investimento associadas a uma Conta CI."""
        raise NotImplementedError

    # --- NOVO (Consulta read-only) ---
    @abstractmethod
    def find_conta_by_numero(self, numero_conta: str) -> Optional[Conta]:
        """Busca uma conta (sem lock) para consulta de dados."""
        raise NotImplementedError

    # --- Métodos de Escrita (exigem uma UoW) ---

    @abstractmethod
    def find_by_id_for_update(self, uow: IUnitOfWork, account_id: int) -> Optional[Conta]:
        """Busca uma conta e a bloqueia para update (dentro de uma UoW)."""
        raise NotImplementedError

    @abstractmethod
    def find_by_cpf_for_update(self, uow: IUnitOfWork, cpf: str) -> Optional[Conta]:
        """Busca a conta CC de um CPF e a bloqueia para update."""
        raise NotImplementedError

    @abstractmethod
    def find_by_number_for_update(self, uow: IUnitOfWork, numero_conta: str) -> Optional[Conta]:
        """Busca uma conta pelo número e a bloqueia para update."""
        raise NotImplementedError

    @abstractmethod
    def update_balance(self, uow: IUnitOfWork, conta: Conta):
        """Atualiza o saldo de uma conta (CC ou CP) (dentro de uma UoW)."""
        raise NotImplementedError

    @abstractmethod
    def save_new_account(self, uow: IUnitOfWork, id_cliente: int, id_agencia: int, numero_conta: str, tipo_conta: str,
                         saldo_inicial: Decimal) -> int:
        """Salva uma nova conta bancária (usado pelo registro de cliente)."""
        raise NotImplementedError

    @abstractmethod
    def find_caixinha_by_id_for_update(self, uow: IUnitOfWork, caixinha_id: int) -> Optional[CaixinhaInvestimento]:
        """Busca uma caixinha específica e a bloqueia para update."""
        raise NotImplementedError

    @abstractmethod
    def update_caixinha_balance(self, uow: IUnitOfWork, caixinha: CaixinhaInvestimento):
        """Atualiza o saldo de uma caixinha (dentro de uma UoW)."""
        raise NotImplementedError

    @abstractmethod
    def save_new_caixinha(self, uow: IUnitOfWork, id_conta: int, tipo_investimento: str, saldo_inicial: Decimal) -> int:
        """Salva uma nova caixinha de investimento."""
        raise NotImplementedError

    # ---
    # --- NOVOS MÉTODOS (Requisitos Avançados v4.0)
    # ---

    @abstractmethod
    def create_account_by_employee(
            self,
            uow: IUnitOfWork,
            id_cliente: int,
            id_agencia: int,
            id_funcionario: int,
            tipo_conta: str,
            numero_conta: str,
            saldo_inicial: Decimal,
            params: Dict[str, Any]
    ) -> int:
        """
        Cria uma nova conta (CC, CP ou CI) com detalhes
        para um cliente existente.
        'params' contém os campos extras (ex: limite_cc, taxa_rendimento).
        """
        raise NotImplementedError

    @abstractmethod
    def call_proc_encerrar_conta(
            self,
            uow: IUnitOfWork,
            id_conta: int,
            motivo: str,
            id_funcionario: int
    ):
        """Chama a procedure de encerramento de conta."""
        raise NotImplementedError

    @abstractmethod
    def update_conta_details(
            self,
            uow: IUnitOfWork,
            id_conta: int,
            details: Dict[str, Any]
    ):
        """Atualiza os detalhes de uma conta (limites, taxas)."""
        raise NotImplementedError

    @abstractmethod
    def get_inadimplentes_report(self) -> List[Dict[str, Any]]:
        """Busca o relatório de clientes inadimplentes (usando a VIEW)."""
        raise NotImplementedError