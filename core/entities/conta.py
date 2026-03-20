from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime
from typing import Optional, List


@dataclass
class CaixinhaInvestimento:
    """
    Representa uma "caixinha" de investimento (CDI ou Bolsa)
    dentro de uma Conta Investimento.
    """
    id_caixinha: Optional[int] = None
    id_conta_investimento: Optional[int] = None
    # No SQL o campo é 'nome_caixinha' (CDI, BOLSA, etc)
    tipo_investimento: str = ""
    saldo: Decimal = Decimal("0.0")
    data_criacao: Optional[datetime] = None

    def aplicar_rendimento_cdi(self) -> Decimal:
        """Calcula e aplica o rendimento de 0.91% (115% DI simulado ao mês)"""
        rendimento = self.saldo * Decimal("0.0091")
        self.saldo += rendimento
        return rendimento

    def aplicar_rendimento_bolsa(self) -> Decimal:
        """Calcula e aplica o rendimento de 0.015% (Bolsa simulado)"""
        rendimento = self.saldo * Decimal("0.00015")
        self.saldo += rendimento
        return rendimento


@dataclass
class Conta:
    """
    Entidade de negócio que representa uma Conta Bancária.
    (Versão 2: Atualizada com todos os novos campos do SQL v4.0)
    """
    # --- Campos Básicos ---
    id_conta: int
    numero_conta: str
    saldo: Decimal
    tipo_conta: str  # 'CC', 'CP', ou 'CI'
    status: str
    id_agencia: Optional[int] = None
    id_cliente: Optional[int] = None
    data_abertura: Optional[datetime] = None

    # --- NOVO: Campo de rastreamento ---
    id_funcionario_abertura: Optional[int] = None

    # --- NOVOS CAMPOS (CC) ---
    limite_cc: Optional[Decimal] = Decimal("0.0")
    taxa_manutencao: Optional[Decimal] = Decimal("0.0")
    data_vencimento_taxa: Optional[int] = 5

    # --- NOVO CAMPO (CP) ---
    taxa_rendimento: Optional[Decimal] = Decimal("0.0050")

    # --- NOVOS CAMPOS (CI) ---
    perfil_risco: Optional[str] = 'BAIXO'
    valor_minimo_investimento: Optional[Decimal] = Decimal("0.0")

    # --- Campo Python (não vem do banco) ---
    caixinhas: List[CaixinhaInvestimento] = field(default_factory=list)

    @property
    def is_ativa(self) -> bool:
        """Regra de negócio: Verifica se a conta está ATIVA."""
        return self.status == 'ATIVA'

    @property
    def saldo_total(self) -> Decimal:
        """
        Calcula o saldo total.
        Se for CI, soma as caixinhas. Senão, retorna o saldo normal.
        """
        if self.tipo_conta == 'CI':
            # Se for CI, o saldo "principal" é a soma das caixinhas para fins de exibição
            if not self.caixinhas:
                return Decimal("0.0")
            return sum(c.saldo for c in self.caixinhas).quantize(Decimal("0.01"))
        return self.saldo

    # --- LÓGICA ATUALIZADA ---
    def tem_saldo_suficiente(self, valor: Decimal) -> bool:
        """
        Regra de negócio: Verifica o saldo.
        Para CC, considera o limite (cheque especial).
        """
        if self.tipo_conta == 'CI':
            # CI não tem saldo "sacável", apenas as caixinhas
            return False

        # Conta Corrente agora considera o limite
        if self.tipo_conta == 'CC':
            limite = self.limite_cc or Decimal("0.0")  # Garante que não é None
            saldo_disponivel = self.saldo + limite
            return saldo_disponivel >= valor

        # Poupança (e outros) usam saldo simples
        return self.saldo >= valor

    def sacar(self, valor: Decimal):
        """Regra de negócio: Executa um saque (para CC ou CP)."""
        if self.tipo_conta == 'CI':
            raise ValueError("Não é possível sacar diretamente de uma Conta Investimento. Resgate uma caixinha.")
        if not self.is_ativa:
            raise ValueError("Conta não está ativa.")
        if valor <= 0:
            raise ValueError("Valor do saque deve ser positivo.")

        if not self.tem_saldo_suficiente(valor):
            # Mensagem de erro mais clara
            if self.tipo_conta == 'CC':
                limite = self.limite_cc or Decimal("0.0")
                disponivel = self.saldo + limite
                raise ValueError(f"Saldo insuficiente. Disponível (saldo + limite): R$ {disponivel:.2f}")
            raise ValueError("Saldo insuficiente.")

        self.saldo -= valor

    def depositar(self, valor: Decimal):
        """Regra de negócio: Executa um depósito (para CC ou CP)."""
        if self.tipo_conta == 'CI':
            raise ValueError("Não é possível depositar diretamente em uma Conta Investimento. Invista em uma caixinha.")
        if not self.is_ativa:
            raise ValueError("Conta não está ativa.")
        if valor <= 0:
            raise ValueError("Valor do depósito deve ser positivo.")
        self.saldo += valor

    # --- LÓGICA ATUALIZADA ---
    def aplicar_rendimento_poupanca(self) -> Decimal:
        """Aplica o rendimento da poupança (usando a taxa_rendimento)."""
        if self.tipo_conta != 'CP':
            raise ValueError("Rendimento só pode ser aplicado em Conta Poupança.")

        # Usa a taxa de rendimento personalizada do objeto
        taxa = self.taxa_rendimento or Decimal("0.0050")  # Fallback para 0.5%
        rendimento = self.saldo * taxa

        self.saldo += rendimento
        return rendimento


@dataclass
class Transacao:
    """
    Entidade de negócio que representa uma Transação.
    """
    id_transacao: Optional[int] = None
    id_conta_origem: Optional[int] = None
    id_conta_destino: Optional[int] = None
    valor: Decimal = Decimal('0.0')
    tipo: str = ""  # <--- CORREÇÃO APLICADA AQUI
    descricao: Optional[str] = ""
    data_transacao: Optional[datetime] = field(default_factory=datetime.now)

    id_caixinha_origem: Optional[int] = None
    id_caixinha_destino: Optional[int] = None

    # Adicionados para exibição na GUI (devem ser populados pelo Repositório)
    conta_origem: Optional[str] = None
    conta_destino: Optional[str] = None
    cpf_cliente_origem: Optional[str] = None
    cpf_cliente_destino: Optional[str] = None
    caixinha_nome: Optional[str] = None  # Nome da caixinha (tipo_investimento)