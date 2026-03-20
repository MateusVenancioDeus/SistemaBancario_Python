from src.core.entities.conta import Conta, CaixinhaInvestimento
from src.core.use_cases.interfaces.i_conta_repository import IContaRepository
from src.core.use_cases.interfaces.i_unit_of_work import IUnitOfWork
from src.infrastructure.db.connection import MySQLConnectionPool
from typing import List, Optional, Dict, Any, Tuple, Union
from decimal import Decimal
from mysql.connector import Error  # Importar Error para capturar erros da procedure


class MySQLContaRepository(IContaRepository):
    """Implementação concreta do repositório de Contas para MySQL (v2)."""

    def __init__(self, pool: MySQLConnectionPool):
        self.pool = pool
        # Lista de campos que são Decimal no SQL
        self._decimal_fields = [
            'saldo', 'limite_cc', 'taxa_manutencao',
            'taxa_rendimento', 'valor_minimo_investimento'
        ]

    def _get_connection(self):
        """Obtém uma conexão para operações de leitura."""
        return self.pool.get_connection()

    def _execute_query(self, uow: IUnitOfWork, query: str, params: tuple, fetch: str = 'one'):
        """Helper para executar queries dentro de uma UoW."""
        try:
            with uow.connection.cursor(dictionary=True) as cur:
                cur.execute(query, params)
                if fetch == 'one':
                    return cur.fetchone()
                if fetch == 'all':
                    return cur.fetchall()
                return None  # Para updates/inserts
        except Exception as e:
            print(f"Erro ao executar query (UoW): {e}")
            raise

    def _hydrate_conta(self, row: dict) -> Conta:
        """Converte uma linha do DB (dict) para uma entidade Conta."""
        if 'caixinhas' in row:
            row.pop('caixinhas')

        # Converte todos os campos Decimal que podem ser None ou String
        for key in self._decimal_fields:
            if key in row and row[key] is not None:
                row[key] = Decimal(row[key])

        # Filtra chaves extras que podem ter vindo de um JOIN
        # mas não pertencem à entidade Conta
        known_keys = Conta.__annotations__.keys()
        filtered_row = {k: v for k, v in row.items() if k in known_keys}

        return Conta(**filtered_row)

    # --- Implementação dos Métodos de Leitura ---

    def find_by_cliente_id(self, cliente_id: int) -> List[Conta]:
        conn = self._get_connection()
        if not conn: return []

        contas = []
        try:
            with conn.cursor(dictionary=True) as cur:
                # SELECT * busca todos os novos campos
                query = "SELECT * FROM conta WHERE id_cliente = %s AND status <> 'ENCERRADA'"
                cur.execute(query, (cliente_id,))
                rows = cur.fetchall()

                for row in rows:
                    conta = self._hydrate_conta(row)
                    if conta.tipo_conta == 'CI':
                        conta.caixinhas = self._find_caixinhas_no_pool(conn, conta.id_conta)
                    contas.append(conta)
            return contas
        except Exception as e:
            print(f"Erro em find_by_cliente_id: {e}")
            return []
        finally:
            if conn: conn.close()

    def find_conta_by_numero(self, numero_conta: str) -> Optional[Conta]:
        conn = self._get_connection()
        if not conn: return None
        try:
            with conn.cursor(dictionary=True) as cur:
                query = "SELECT * FROM conta WHERE numero_conta = %s"
                cur.execute(query, (numero_conta,))
                row = cur.fetchone()
                if row:
                    conta = self._hydrate_conta(row)
                    if conta.tipo_conta == 'CI':
                        conta.caixinhas = self._find_caixinhas_no_pool(conn, conta.id_conta)
                    return conta
                return None
        except Exception as e:
            print(f"Erro em find_conta_by_numero: {e}")
            return None
        finally:
            if conn: conn.close()

    def find_caixinhas_by_conta_id(self, conta_id: int) -> List[CaixinhaInvestimento]:
        conn = self._get_connection()
        if not conn: return []
        try:
            return self._find_caixinhas_no_pool(conn, conta_id)
        finally:
            if conn: conn.close()

    # Helper interno para reutilizar a lógica de busca de caixinhas
    def _find_caixinhas_no_pool(self, conn, conta_id: int) -> List[CaixinhaInvestimento]:
        caixinhas = []
        try:
            with conn.cursor(dictionary=True) as cur:
                # Query ATUALIZADA para corresponder ao SQL v4
                query = """
                    SELECT 
                        id_caixinha, 
                        id_conta_investimento, 
                        nome_caixinha AS tipo_investimento, 
                        saldo, 
                        data_criacao 
                    FROM investimento_caixinha 
                    WHERE id_conta_investimento = %s
                """
                cur.execute(query, (conta_id,))
                rows = cur.fetchall()
                for row in rows:
                    row['saldo'] = Decimal(row['saldo'])
                    # Filtra chaves extras (meta_valor, status da caixinha)
                    known_keys = CaixinhaInvestimento.__annotations__.keys()
                    filtered_row = {k: v for k, v in row.items() if k in known_keys}
                    caixinhas.append(CaixinhaInvestimento(**filtered_row))
            return caixinhas
        except Exception as e:
            print(f"Erro em _find_caixinhas_no_pool: {e}")
            return []

    # --- Implementação dos Métodos de Escrita (Transacionais) ---

    def find_by_id_for_update(self, uow: IUnitOfWork, account_id: int) -> Optional[Conta]:
        query = "SELECT * FROM conta WHERE id_conta = %s FOR UPDATE"
        row = self._execute_query(uow, query, (account_id,), fetch='one')
        if row:
            return self._hydrate_conta(row)
        return None

    def find_by_cpf_for_update(self, uow: IUnitOfWork, cpf: str) -> Optional[Conta]:
        query = """
            SELECT c.*
            FROM conta c
            JOIN cliente cl ON c.id_cliente = cl.id_cliente
            JOIN usuario u ON cl.id_usuario = u.id_usuario
            WHERE u.cpf = %s AND c.tipo_conta = 'CC' AND c.status = 'ATIVA'
            LIMIT 1 FOR UPDATE
        """
        row = self._execute_query(uow, query, (cpf,), fetch='one')
        if row:
            return self._hydrate_conta(row)
        return None

    def find_by_number_for_update(self, uow: IUnitOfWork, numero_conta: str) -> Optional[Conta]:
        query = "SELECT * FROM conta WHERE numero_conta = %s AND status = 'ATIVA' LIMIT 1 FOR UPDATE"
        row = self._execute_query(uow, query, (numero_conta,), fetch='one')
        if row:
            return self._hydrate_conta(row)
        return None

    def update_balance(self, uow: IUnitOfWork, conta: Conta):
        if conta.tipo_conta == 'CI':
            return
        query = "UPDATE conta SET saldo = %s WHERE id_conta = %s"
        self._execute_query(uow, query, (conta.saldo, conta.id_conta), fetch=None)

    def save_new_account(self, uow: IUnitOfWork, id_cliente: int, id_agencia: int, numero_conta: str, tipo_conta: str,
                         saldo_inicial: Decimal) -> int:
        """Salva uma nova conta (simples) durante o registro do cliente."""
        query = """
            INSERT INTO conta (id_cliente, id_agencia, numero_conta, tipo_conta, saldo, status)
            VALUES (%s, %s, %s, %s, %s, 'ATIVA')
        """
        params = (id_cliente, id_agencia, numero_conta, tipo_conta, saldo_inicial)
        try:
            cursor = uow.connection.cursor()
            cursor.execute(query, params)
            print(f"Repositório: Conta {numero_conta} (Tipo: {tipo_conta}) inserida.")
            return cursor.lastrowid
        except Exception as e:
            print(f"Erro ao salvar nova conta no repositório: {e}")
            raise

    # --- Métodos de Caixinha ---

    def find_caixinha_by_id_for_update(self, uow: IUnitOfWork, caixinha_id: int) -> Optional[CaixinhaInvestimento]:
        query = """
            SELECT 
                id_caixinha, 
                id_conta_investimento, 
                nome_caixinha AS tipo_investimento, 
                saldo, 
                data_criacao 
            FROM investimento_caixinha 
            WHERE id_caixinha = %s FOR UPDATE
        """
        row = self._execute_query(uow, query, (caixinha_id,), fetch='one')
        if row:
            row['saldo'] = Decimal(row['saldo'])
            known_keys = CaixinhaInvestimento.__annotations__.keys()
            filtered_row = {k: v for k, v in row.items() if k in known_keys}
            return CaixinhaInvestimento(**filtered_row)
        return None

    def update_caixinha_balance(self, uow: IUnitOfWork, caixinha: CaixinhaInvestimento):
        query = "UPDATE investimento_caixinha SET saldo = %s WHERE id_caixinha = %s"
        self._execute_query(uow, query, (caixinha.saldo, caixinha.id_caixinha), fetch=None)

    def save_new_caixinha(self, uow: IUnitOfWork, id_conta_investimento: int, nome_caixinha: str,
                          saldo_inicial: Decimal) -> int:
        query = """
            INSERT INTO investimento_caixinha (id_conta_investimento, nome_caixinha, saldo)
            VALUES (%s, %s, %s)
        """
        params = (id_conta_investimento, nome_caixinha, saldo_inicial)
        cursor = None
        try:
            cursor = uow.connection.cursor()
            cursor.execute(query, params)
            print(f"Caixinha criada: {nome_caixinha} vinculada à conta investimento {id_conta_investimento}.")
            return cursor.lastrowid
        except Exception as e:
            print(f"Erro ao salvar nova caixinha: {e}")
            raise
        finally:
            if cursor:
                cursor.close()

    # ---
    # --- IMPLEMENTAÇÃO DOS NOVOS MÉTODOS (v4.0)
    # ---

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
        """
        cursor = None
        try:
            # 1. Montar a query de inserção dinâmica
            colunas = [
                'id_cliente', 'id_agencia', 'id_funcionario_abertura',
                'numero_conta', 'tipo_conta', 'saldo', 'status'
            ]
            # Placeholders para os valores base
            # Nota: 'ATIVA' não pode ser %s se não for passado como valor, então injetamos
            valores_placeholder = ['%s', '%s', '%s', '%s', '%s', '%s', "'ATIVA'"]
            # Valores base
            valores_tupla = [
                id_cliente, id_agencia, id_funcionario,
                numero_conta, tipo_conta, saldo_inicial
            ]

            # Campos permitidos do 'params'
            campos_permitidos = [
                'limite_cc', 'taxa_manutencao', 'data_vencimento_taxa',
                'taxa_rendimento', 'perfil_risco', 'valor_minimo_investimento'
            ]

            for key, value in params.items():
                if key in campos_permitidos and value is not None:
                    colunas.append(key)
                    valores_placeholder.append('%s')
                    valores_tupla.append(value)

            # 2. Construir e Executar a query final
            query_insert = f"""
                INSERT INTO conta ({', '.join(colunas)})
                VALUES ({', '.join(valores_placeholder)})
            """

            cursor = uow.connection.cursor()
            cursor.execute(query_insert, tuple(valores_tupla))
            new_account_id = cursor.lastrowid

            print(f"Repositório: Conta {numero_conta} (Tipo: {tipo_conta}) criada para cliente {id_cliente}.")
            return new_account_id

        except Exception as e:
            print(f"Erro ao criar conta para cliente no repositório: {e}")
            raise  # Propaga o erro para o UoW fazer rollback
        finally:
            if cursor:
                cursor.close()

    def call_proc_encerrar_conta(
            self,
            uow: IUnitOfWork,
            id_conta: int,
            motivo: str,
            id_funcionario: int
    ):
        """Chama a procedure de encerramento de conta."""
        cursor = None
        try:
            cursor = uow.connection.cursor()
            # Os argumentos DEVEM estar na ordem exata da procedure
            args = (id_conta, motivo, id_funcionario)
            cursor.callproc('proc_encerrar_conta', args)
            print(f"Repositório: Procedure 'proc_encerrar_conta' chamada para conta {id_conta}.")
        except Error as e:
            # Captura o erro SQL (ex: saldo negativo) e o relança como um erro Python
            print(f"Erro da Procedure: {e.msg}")
            raise ValueError(e.msg)
        except Exception as e:
            print(f"Erro ao chamar proc_encerrar_conta: {e}")
            raise
        finally:
            if cursor:
                cursor.close()

    def update_conta_details(
            self,
            uow: IUnitOfWork,
            id_conta: int,
            details: Dict[str, Any]
    ):
        """Atualiza os detalhes de uma conta (limites, taxas)."""
        campos_permitidos = [
            'limite_cc', 'taxa_manutencao', 'data_vencimento_taxa',
            'taxa_rendimento', 'perfil_risco'
        ]

        set_parts = []
        valores_tupla = []

        for key, value in details.items():
            if key in campos_permitidos:
                set_parts.append(f"{key} = %s")
                valores_tupla.append(value)

        if not set_parts:
            print("Repositório: update_conta_details chamado sem campos válidos.")
            return  # Nada a atualizar

        query = f"UPDATE conta SET {', '.join(set_parts)} WHERE id_conta = %s"
        valores_tupla.append(id_conta)

        cursor = None
        try:
            cursor = uow.connection.cursor()
            cursor.execute(query, tuple(valores_tupla))
            print(f"Repositório: Detalhes da conta {id_conta} atualizados.")
        except Exception as e:
            print(f"Erro ao atualizar detalhes da conta: {e}")
            raise
        finally:
            if cursor:
                cursor.close()

    def get_movimentacoes_report(self, start_date: str, end_date: str, tipo_transacao: str,
                                 id_agencia: Optional[int]) -> Tuple[bool, Union[str, List[Dict[str, Any]]]]:
        """Busca o relatório de movimentações filtrado."""
        conn = self._get_connection()
        if not conn: return False, "Falha ao conectar ao banco de dados."

        try:
            with conn.cursor(dictionary=True) as cursor:
                query = "SELECT * FROM V_MOVIMENTACAO_DETALHADA WHERE DATE(data_transacao) BETWEEN %s AND %s"
                params = [start_date, end_date]

                if tipo_transacao and tipo_transacao != "TODOS":
                    query += " AND tipo_transacao = %s"
                    params.append(tipo_transacao)

                if id_agencia:
                    # Filtra por conta de origem ou destino estar na agência
                    query += " AND (id_agencia_origem = %s OR id_agencia_destino = %s)"
                    params.append(id_agencia)
                    params.append(id_agencia)  # Adiciona duas vezes para o OR

                query += " ORDER BY data_transacao DESC"

                cursor.execute(query, tuple(params))
                results = cursor.fetchall()

                # Conversão manual de Decimal (o driver MySQL pode retornar Decimal já)
                for row in results:
                    if 'valor' in row and row['valor'] is not None:
                        row['valor'] = Decimal(row['valor'])

                return True, results
        except Exception as e:
            print(f"Erro ao buscar relatório de movimentações: {e}")
            return False, f"Erro ao buscar relatório: {e}"
        finally:
            if conn:
                conn.close()

    def get_inadimplentes_report(self) -> Tuple[bool, Union[str, List[Dict[str, Any]]]]:
        """
        Implementação do método abstrato para buscar o relatório de inadimplentes.
        Utiliza a VIEW V_CLIENTES_INADIMPLENTES.
        """
        conn = self._get_connection()
        if not conn: return False, "Falha ao conectar ao banco de dados."

        try:
            with conn.cursor(dictionary=True) as cursor:
                # Chama a VIEW que lista clientes com saldo negativo em CC
                cursor.execute("SELECT * FROM V_CLIENTES_INADIMPLENTES ORDER BY saldo ASC;")
                results = cursor.fetchall()

                # Converte saldo para Decimal, se necessário
                for row in results:
                    if 'saldo' in row and row['saldo'] is not None:
                        row['saldo'] = Decimal(row['saldo'])

                return True, results
        except Exception as e:
            print(f"Erro ao buscar relatório de inadimplentes: {e}")
            return False, f"Erro ao buscar relatório: {e}"
        finally:
            if conn:
                conn.close()