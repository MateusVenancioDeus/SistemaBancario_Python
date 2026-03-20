from src.core.use_cases.interfaces.i_conta_repository import IContaRepository
from src.core.use_cases.interfaces.i_transacao_repository import ITransacaoRepository
from src.core.use_cases.interfaces.i_usuario_repository import IUsuarioRepository
from src.core.use_cases.interfaces.i_unit_of_work import IUnitOfWork
from src.core.entities.conta import Conta, Transacao, CaixinhaInvestimento
from src.infrastructure.utils.cpf_utils import only_digits
from typing import Callable, Tuple, List, Optional, Dict, Any, Union
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import random
import hashlib  # Para MD5

TWO_PLACES = Decimal('0.01')


class ContaService:
    """
    Casos de Uso: Operações de Conta (v2).
    Implementa a lógica de negócio avançada (Encerramento, Alteração, Relatórios).
    """

    def __init__(self,
                 conta_repo: IContaRepository,
                 transacao_repo: ITransacaoRepository,
                 # Nota: Adicionamos usuario_repo para lógicas de validação
                 usuario_repo: IUsuarioRepository,
                 uow_factory: Callable[[], IUnitOfWork]):
        self.conta_repo = conta_repo
        self.transacao_repo = transacao_repo
        self.usuario_repo = usuario_repo  # Essencial para o novo 'abrir_conta'
        self.uow_factory = uow_factory

    def _gerar_numero_conta(self, tipo_conta: str, id_cliente: int) -> str:
        """
        Gera um número de conta aleatório formatado com dígito verificador.
        Usa o id_cliente para garantir alguma unicidade inicial.
        Ex: 0001-12345-6-CC
        """
        numero_base = random.randint(10000, 99999)
        soma_digitos = sum(int(digito) for digito in str(numero_base))
        digito_verificador = soma_digitos % 10

        return f"{id_cliente:04d}-{numero_base}-{digito_verificador}-{tipo_conta.upper()}"

    # ================================================================
    # MÉTODOS DE OPERAÇÃO (Cliente)
    # ================================================================

    def get_contas_cliente(self, cliente_id: int) -> Tuple[bool, Union[List[Conta], str]]:
        """Caso de Uso: Buscar contas de um cliente."""
        try:
            contas = self.conta_repo.find_by_cliente_id(cliente_id)
            return True, contas
        except Exception as e:
            # Captura a exceção e retorna no formato (False, mensagem de erro)
            return False, f"Erro ao buscar contas no repositório: {e}"

    def get_extrato(self, conta_id: int) -> Tuple[bool, Union[List[Transacao], str]]:
        """Caso de Uso: Buscar extrato de uma conta (CC, CP ou CI)."""
        try:
            extrato = self.transacao_repo.get_statement(conta_id)
            # Nota: O repositório deve retornar a lista de objetos Transacao
            return True, extrato
        except Exception as e:
            return False, f"Erro ao buscar extrato no repositório: {e}"

    def depositar(self, conta_id: int, valor_str: str, descricao_opcional: Optional[str] = None) -> Tuple[bool, str]:
        try:
            valor = Decimal(valor_str.replace(',', '.'))
            if valor <= 0: raise ValueError("Valor deve ser positivo.")
        except (InvalidOperation, ValueError):
            return False, "Valor inválido. Use apenas números (ex: 50.00)."

        try:
            with self.uow_factory() as uow:
                conta = self.conta_repo.find_by_id_for_update(uow, conta_id)
                if not conta: return False, "Conta não encontrada."
                if not conta.is_ativa: return False, "Conta não está ativa."

                conta.depositar(valor)
                self.conta_repo.update_balance(uow, conta)
                desc_final = descricao_opcional or "Depósito em conta"
                # CORREÇÃO AQUI: 'tipo_transacao' mudou para 'tipo'
                tx = Transacao(id_conta_destino=conta_id, valor=valor,
                               tipo='DEPOSITO', descricao=desc_final)
                self.transacao_repo.save(uow, tx)
                uow.commit()
                return True, f"Depósito de R$ {valor:.2f} realizado!"
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Erro operacional: {e}"

    def sacar(self, conta_id: int, valor_str: str) -> Tuple[bool, str]:
        try:
            valor = Decimal(valor_str.replace(',', '.'))
            if valor <= 0: raise ValueError("Valor deve ser positivo.")
        except (InvalidOperation, ValueError):
            return False, "Valor inválido. Use apenas números (ex: 50.00)."

        try:
            with self.uow_factory() as uow:
                conta = self.conta_repo.find_by_id_for_update(uow, conta_id)
                if not conta: return False, "Conta não encontrada."

                # 'sacar' na entidade já valida saldo + limite
                conta.sacar(valor)

                self.conta_repo.update_balance(uow, conta)
                # CORREÇÃO AQUI: 'tipo_transacao' mudou para 'tipo'
                tx = Transacao(id_conta_origem=conta_id, valor=valor,
                               tipo='SAQUE', descricao='Saque de conta')
                self.transacao_repo.save(uow, tx)
                uow.commit()
                return True, f"Saque de R$ {valor:.2f} realizado!"
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Erro operacional: {e}"

    def transferir(self, conta_origem_id: int, target_identifier: str, by: str, valor_str: str,
                   descricao_opcional: Optional[str] = None) -> Tuple[bool, str]:
        try:
            valor = Decimal(valor_str.replace(',', '.'))
            if valor <= 0: raise ValueError("Valor deve ser positivo.")
        except (InvalidOperation, ValueError):
            return False, "Valor inválido. Use apenas números (ex: 50.00)."

        try:
            with self.uow_factory() as uow:
                conta_origem = self.conta_repo.find_by_id_for_update(uow, conta_origem_id)
                if not conta_origem:
                    return False, "Conta de origem não encontrada."

                conta_destino = None
                target_clean = target_identifier
                if by == 'cpf':
                    target_clean = only_digits(target_identifier)
                    if not target_clean: return False, "CPF de destino inválido."
                    conta_destino = self.conta_repo.find_by_cpf_for_update(uow, target_clean)
                elif by == 'account':
                    conta_destino = self.conta_repo.find_by_number_for_update(uow, target_clean)

                if not conta_destino:
                    return False, "Conta de destino não encontrada."
                if conta_origem.id_conta == conta_destino.id_conta:
                    return False, "Não é possível transferir para a mesma conta."

                conta_origem.sacar(valor)
                conta_destino.depositar(valor)
                self.conta_repo.update_balance(uow, conta_origem)
                self.conta_repo.update_balance(uow, conta_destino)
                desc_final = descricao_opcional or f"Transferência para {target_clean}"
                # CORREÇÃO AQUI: 'tipo_transacao' mudou para 'tipo'
                tx = Transacao(
                    id_conta_origem=conta_origem.id_conta,
                    id_conta_destino=conta_destino.id_conta,
                    valor=valor, tipo='TRANSFERENCIA', descricao=desc_final
                )
                self.transacao_repo.save(uow, tx)
                uow.commit()
                return True, f"Transferência de R$ {valor:.2f} realizada!"
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Erro operacional: {e}"

    def aplicar_rendimento_poupanca(self, conta_id: int) -> Tuple[bool, str]:
        try:
            with self.uow_factory() as uow:
                conta = self.conta_repo.find_by_id_for_update(uow, conta_id)
                if not conta: return False, "Conta não encontrada."

                rendimento = conta.aplicar_rendimento_poupanca()
                if rendimento <= 0:
                    return True, "O rendimento calculado foi R$ 0,00. Nenhum valor foi aplicado."

                self.conta_repo.update_balance(uow, conta)
                # CORREÇÃO AQUI: 'tipo_transacao' mudou para 'tipo'
                tx = Transacao(
                    id_conta_destino=conta.id_conta,
                    valor=rendimento,
                    tipo='RENDIMENTO_POUPANCA',
                    descricao="Rendimento da Poupança"
                )
                self.transacao_repo.save(uow, tx)
                uow.commit()
                return True, f"Rendimento de R$ {rendimento:,.2f} aplicado à Poupança!"
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Erro operacional: {e}"

    # --- MÉTODOS DE INVESTIMENTO (CI) ---

    def get_caixinhas_investimento(self, conta_id: int) -> Tuple[bool, Union[List[CaixinhaInvestimento], str]]:
        """
        Caso de Uso: Buscar caixinhas de investimento de uma Conta Investimento.
        """
        try:
            caixinhas = self.conta_repo.find_caixinhas_by_conta_id(conta_id)
            return True, caixinhas
        except Exception as e:
            return False, f"Erro ao buscar caixinhas: {e}"

    def investir(self, conta_origem_id: int, caixinha_destino_id: int, valor_str: str) -> Tuple[bool, str]:
        try:
            valor = Decimal(valor_str.replace(',', '.'))
            if valor <= 0: raise ValueError("Valor do investimento deve ser positivo.")
        except (InvalidOperation, ValueError) as e:
            return False, str(e)

        try:
            with self.uow_factory() as uow:
                caixinha_destino = self.conta_repo.find_caixinha_by_id_for_update(uow, caixinha_destino_id)
                conta_origem = self.conta_repo.find_by_id_for_update(uow, conta_origem_id)

                if not conta_origem or not caixinha_destino:
                    return False, "Conta de origem ou caixinha de destino não encontrada."

                conta_origem.sacar(valor)
                caixinha_destino.saldo += valor
                self.conta_repo.update_balance(uow, conta_origem)
                self.conta_repo.update_caixinha_balance(uow, caixinha_destino)
                # CORREÇÃO AQUI: 'tipo_transacao' mudou para 'tipo'
                tx = Transacao(
                    id_conta_origem=conta_origem.id_conta,
                    id_caixinha_destino=caixinha_destino.id_caixinha,
                    valor=valor, tipo='INVESTIR',
                    descricao=f"Investimento em {caixinha_destino.tipo_investimento}"
                )
                self.transacao_repo.save(uow, tx)
                uow.commit()
                return True, f"Investimento de R$ {valor:,.2f} realizado!"
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Erro operacional ao investir: {e}"

    def resgatar(self, caixinha_origem_id: int, conta_destino_id: int, valor_str: str) -> Tuple[bool, str]:
        try:
            valor = Decimal(valor_str.replace(',', '.'))
            if valor <= 0: raise ValueError("Valor do resgate deve ser positivo.")
        except (InvalidOperation, ValueError) as e:
            return False, str(e)

        try:
            with self.uow_factory() as uow:
                caixinha_origem = self.conta_repo.find_caixinha_by_id_for_update(uow, caixinha_origem_id)
                conta_destino = self.conta_repo.find_by_id_for_update(uow, conta_destino_id)

                if not caixinha_origem or not conta_destino:
                    return False, "Caixinha de origem ou conta de destino não encontrada."
                if caixinha_origem.saldo < valor:
                    raise ValueError("Saldo insuficiente na caixinha.")

                caixinha_origem.saldo -= valor
                conta_destino.depositar(valor)
                self.conta_repo.update_caixinha_balance(uow, caixinha_origem)
                self.conta_repo.update_balance(uow, conta_destino)
                # CORREÇÃO AQUI: 'tipo_transacao' mudou para 'tipo'
                tx = Transacao(
                    id_caixinha_origem=caixinha_origem.id_caixinha,
                    id_conta_destino=conta_destino.id_conta,
                    valor=valor, tipo='RESGATAR',
                    descricao=f"Resgate de {caixinha_origem.tipo_investimento}"
                )
                self.transacao_repo.save(uow, tx)
                uow.commit()
                return True, f"Resgate de R$ {valor:,.2f} realizado!"
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Erro operacional ao resgatar: {e}"

    def aplicar_rendimento_investimento(self, caixinha_id: int) -> Tuple[bool, str]:
        """Aplica rendimento simulado a uma caixinha de investimento (CDI ou BOLSA)."""
        try:
            with self.uow_factory() as uow:
                caixinha = self.conta_repo.find_caixinha_by_id_for_update(uow, caixinha_id)
                if not caixinha: return False, "Caixinha não encontrada."

                rendimento = Decimal('0.0')

                if caixinha.tipo_investimento == 'CDI':
                    # Ex: 0.91% ao mês (115% do CDI)
                    taxa = Decimal('0.0091')
                    rendimento = (caixinha.saldo * taxa).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
                    tx_type = 'RENDIMENTO_CDI'
                elif caixinha.tipo_investimento == 'BOLSA':
                    # Ex: 0.015% ao dia (simulação de alta volatilidade/alto risco)
                    taxa = Decimal('0.00015')
                    rendimento = (caixinha.saldo * taxa).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
                    tx_type = 'RENDIMENTO_BOLSA'
                else:
                    return False, f"Tipo de investimento desconhecido: {caixinha.tipo_investimento}"

                if rendimento <= 0:
                    return True, "Rendimento calculado foi R$ 0,00. Nenhum valor aplicado."

                caixinha.saldo += rendimento
                self.conta_repo.update_caixinha_balance(uow, caixinha)
                # CORREÇÃO AQUI: 'tipo_transacao' mudou para 'tipo'
                tx = Transacao(
                    id_caixinha_destino=caixinha_id,
                    valor=rendimento,
                    tipo=tx_type,
                    descricao=f"Rendimento {caixinha.tipo_investimento}"
                )
                self.transacao_repo.save(uow, tx)
                uow.commit()
                return True, f"Rendimento de R$ {rendimento:,.2f} aplicado à caixinha {caixinha.tipo_investimento}!" # Corrigido .nome_caixinha para .tipo_investimento

        except Exception as e:
            return False, f"Erro operacional ao aplicar rendimento: {e}"

    # ================================================================
    # --- NOVOS MÉTODOS DE GERENCIAMENTO (Funcionário) ---
    # ================================================================

    def abrir_conta_para_cliente(self, data: Dict[str, Any], id_funcionario_logado: int, id_agencia_func: int) -> Tuple[
        bool, str]:
        """
        Caso de Uso: Funcionário abre uma nova conta (CC, CP ou CI) para um cliente.
        Esta versão (v2) cadastra o cliente E as contas.
        """
        try:
            # 1. Validação de dados do NOVO CLIENTE
            cpf_cliente = only_digits(data.get('cpf_cliente', ''))
            nome = data.get('nome')
            senha = data.get('senha')
            data_nasc = data.get('data_nascimento')
            endereco = data.get('endereco')
            telefone = data.get('telefone')
            tipo_conta = data.get('tipo_conta')  # O tipo da *primeira* conta

            if not all([cpf_cliente, nome, senha, data_nasc, endereco, telefone, tipo_conta]):
                return False, "Todos os campos (Nome, CPF, Senha, Data Nasc., Endereço, Telefone, Tipo de Conta) são obrigatórios."
            if tipo_conta not in ('CC', 'CP', 'CI'):
                return False, "Tipo de conta inválido."

            with self.uow_factory() as uow:
                # 2. Verificar se o cliente (CPF) já existe
                if self.usuario_repo.find_client_details_from_view(cpf_cliente):
                    return False, f"Cliente com CPF {cpf_cliente} já existe. Use a outra função para adicionar uma conta."

                # 3. Criar o usuário
                senha_hash = hashlib.md5(senha.encode("utf-8")).hexdigest()
                id_usuario = self.usuario_repo.save_user(
                    uow, nome, cpf_cliente, senha_hash, 'CLIENTE',
                    data_nasc, endereco, telefone
                )
                id_cliente = self.usuario_repo.save_client(uow, id_usuario)

                # 4. Preparar parâmetros específicos para a CONTA
                params_especificos = {}
                try:
                    if tipo_conta == 'CC':
                        params_especificos = {
                            'limite_cc': Decimal(data.get('limite_cc', '0.0')),
                            'taxa_manutencao': Decimal(data.get('taxa_manutencao', '0.0')),
                            'data_vencimento_taxa': int(data.get('data_vencimento_taxa', 5))
                        }
                    elif tipo_conta == 'CP':
                        params_especificos = {
                            'taxa_rendimento': Decimal(data.get('taxa_rendimento', '0.005'))
                        }
                    elif tipo_conta == 'CI':
                        params_especificos = {
                            'perfil_risco': data.get('perfil_risco', 'BAIXO'),
                            'valor_minimo_investimento': Decimal(data.get('valor_minimo_investimento', '0.0'))
                        }
                except (InvalidOperation, ValueError) as e:
                    return False, f"Erro na conversão de parâmetros da conta: {e}"

                # 5. Criar a conta principal solicitada
                numero_conta = self._gerar_numero_conta(tipo_conta, id_cliente)
                id_conta_principal = self.conta_repo.create_account_by_employee(
                    uow=uow,
                    id_cliente=id_cliente,
                    id_agencia=id_agencia_func,
                    id_funcionario=id_funcionario_logado,
                    tipo_conta=tipo_conta,
                    numero_conta=numero_conta,
                    saldo_inicial=Decimal(data.get('saldo_inicial', '0.0')),
                    params=params_especificos
                )

                # 6. Criar as outras 2 contas (padrão)
                if tipo_conta != 'CC':
                    num_cc = self._gerar_numero_conta('CC', id_cliente)
                    self.conta_repo.create_account_by_employee(uow, id_cliente, id_agencia_func, id_funcionario_logado,
                                                               'CC', num_cc, Decimal("0.0"), {})

                if tipo_conta != 'CP':
                    num_cp = self._gerar_numero_conta('CP', id_cliente)
                    self.conta_repo.create_account_by_employee(uow, id_cliente, id_agencia_func, id_funcionario_logado,
                                                               'CP', num_cp, Decimal("0.0"), {})

                if tipo_conta != 'CI':
                    num_ci = self._gerar_numero_conta('CI', id_cliente)
                    id_conta_investimento = self.conta_repo.create_account_by_employee(uow, id_cliente, id_agencia_func,
                                                                                       id_funcionario_logado, 'CI',
                                                                                       num_ci, Decimal("0.0"), {})
                    # Criar caixinhas padrão para a conta CI
                    self.conta_repo.save_new_caixinha(uow, id_conta_investimento, 'CDI', Decimal("0.00"))
                    self.conta_repo.save_new_caixinha(uow, id_conta_investimento, 'BOLSA', Decimal("0.00"))
                elif tipo_conta == 'CI':
                    # Criar caixinhas padrão para a conta CI que acabamos de criar
                    self.conta_repo.save_new_caixinha(uow, id_conta_principal, 'CDI', Decimal("0.00"))
                    self.conta_repo.save_new_caixinha(uow, id_conta_principal, 'BOLSA', Decimal("0.00"))

                uow.commit()
                return True, f"Cliente {nome} (CPF: {cpf_cliente}) criado com sucesso. Contas CC, CP e CI geradas."

        except ValueError as e:  # Erro esperado (ex: CPF não encontrado, ou vindo do repo/procedure)
            return False, str(e)
        except InvalidOperation:
            return False, "Erro ao converter um valor numérico (limite, taxa, etc.). Verifique os valores."
        except Exception as e:
            return False, f"Erro operacional inesperado: {e}"

    def encerrar_conta(self, id_conta: int, motivo: str, id_funcionario: int) -> Tuple[bool, str]:
        """
        Caso de Uso: Funcionário encerra uma conta de cliente.
        """
        if not motivo:
            return False, "O motivo do encerramento é obrigatório."

        try:
            with self.uow_factory() as uow:
                # Chama a procedure do banco de dados
                self.conta_repo.call_proc_encerrar_conta(
                    uow=uow,
                    id_conta=id_conta,
                    motivo=motivo,
                    id_funcionario=id_funcionario
                )
                uow.commit()
            return True, f"Conta {id_conta} encerrada com sucesso."
        except ValueError as e:  # Erro vindo da Procedure (ex: saldo pendente)
            return False, str(e)
        except Exception as e:
            return False, f"Erro inesperado ao encerrar conta: {e}"

    def get_conta_details(self, numero_conta: str) -> Tuple[bool, Union[Conta, str]]:
        """Caso de Uso: Funcionário consulta os detalhes de uma conta."""
        try:
            conta = self.conta_repo.find_conta_by_numero(numero_conta)
            if not conta:
                return False, "Conta não encontrada."
            return True, conta
        except Exception as e:
            return False, f"Erro ao buscar conta: {e}"

    def update_conta_details(self, id_conta: int, id_cliente: int, details: Dict[str, Any]) -> Tuple[bool, str]:
        """Caso de Uso: Funcionário altera detalhes de uma conta (limite, taxas)."""
        try:
            score_cliente = 500  # Score padrão
            # Busca o score do cliente
            with self.uow_factory() as uow:
                # 🔄 CORREÇÃO: Usando o método de procedure do repositório de Usuários para obter o score.
                # Assumindo que o repositório de usuários tem um método para chamar a procedure
                ok_score, score_result = self.usuario_repo.call_proc_calcular_score(uow, id_cliente)

                if ok_score and isinstance(score_result, (int, Decimal)):
                    score_cliente = score_result
                else:
                    # Se falhar, usa o padrão 500 e imprime um aviso
                    print(f"Aviso: Não foi possível obter score. Usando padrão 500. Erro: {score_result}")

                # O commit para salvar o score (se a procedure o fizer) já deve ser feito dentro da UoW.
                uow.commit()

            # Requisito: "Alterar limite (com validação de score de crédito)"
            if 'limite_cc' in details:
                novo_limite = Decimal(details['limite_cc'])
                if novo_limite > 1000 and score_cliente < 700:
                    return False, f"Falha na validação. Score do cliente ({score_cliente}) é muito baixo para um limite de R$ {novo_limite:.2f}."
                if novo_limite > 5000 and score_cliente < 850:
                    return False, f"Falha na validação. Score ({score_cliente}) muito baixo para limite de R$ {novo_limite:.2f}."

            with self.uow_factory() as uow:
                self.conta_repo.update_conta_details(uow, id_conta, details)
                uow.commit()
            return True, "Detalhes da conta atualizados com sucesso."
        except InvalidOperation:
            return False, "Valor inválido para um dos campos numéricos."
        except Exception as e:
            return False, f"Erro ao atualizar detalhes: {e}"

    # ================================================================
    # --- NOVOS MÉTODOS DE RELATÓRIO (Funcionário) ---
    # ================================================================

    # CORREÇÃO: Ajustando o retorno para o padrão (bool, data/msg)
    def get_relatorio_movimentacoes(self, start_date: str, end_date: str, tipo_transacao: Optional[str],
                                    id_agencia: Optional[int]) -> Tuple[bool, Union[List[Dict[str, Any]], str]]:
        """Relatório avançado de movimentações (usa VIEW)."""
        try:
            # Limpa o "Tipo de Transação" se for "Todos"
            tipo_filtro = tipo_transacao if tipo_transacao != "TODOS" else None

            data = self.transacao_repo.get_movimentacoes_report_from_view(
                start_date, end_date, tipo_filtro, id_agencia
            )
            return True, data
        except Exception as e:
            # Retorna o erro como string
            return False, f"Erro ao gerar relatório: {e}"

    # CORREÇÃO: Ajustando o retorno para o padrão (bool, data/msg)
    def get_relatorio_inadimplentes(self) -> Tuple[bool, Union[List[Dict[str, Any]], str]]:
        """Relatório de clientes inadimplentes (usa VIEW)."""
        try:
            data = self.conta_repo.get_inadimplentes_report()
            return True, data
        except Exception as e:
            # Retorna o erro como string
            return False, f"Erro ao gerar relatório: {e}"