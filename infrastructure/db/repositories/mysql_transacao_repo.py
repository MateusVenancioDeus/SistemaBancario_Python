from src.core.entities.conta import Transacao
from src.core.use_cases.interfaces.i_transacao_repository import ITransacaoRepository
from src.core.use_cases.interfaces.i_unit_of_work import IUnitOfWork
from src.infrastructure.db.connection import MySQLConnectionPool
from typing import List, Dict, Any, Optional
from decimal import Decimal


class MySQLTransacaoRepository(ITransacaoRepository):
    """Implementação concreta do repositório de Transações para MySQL (v2)."""

    def __init__(self, pool: MySQLConnectionPool):
        self.pool = pool

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

    def get_statement(self, account_id: int) -> List[Transacao]:
        """Busca o extrato de uma conta (CC, CP ou CI), incluindo detalhes para exibição."""
        conn = self._get_connection()
        if not conn: return []

        # Query COMPLETA com LEFT JOINs para buscar todos os dados de referência
        query = """
            SELECT 
                t.id_transacao, t.id_conta_origem, t.id_conta_destino, 
                t.valor, t.tipo_transacao AS tipo, t.descricao, t.data_transacao,
                t.id_caixinha_origem, t.id_caixinha_destino,

                -- Referências de Conta/CPF (Origem)
                c_origem.numero_conta AS conta_origem_num,
                u_origem.cpf AS cpf_origem,

                -- Referências de Conta/CPF (Destino)
                c_destino.numero_conta AS conta_destino_num,
                u_destino.cpf AS cpf_destino,

                -- Nome da Caixinha (se envolvida)
                COALESCE(ci_origem.nome_caixinha, ci_destino.nome_caixinha) AS caixinha_nome 

            FROM transacao t

            -- LEFT JOINS para buscar dados de contas de ORIGEM
            LEFT JOIN conta c_origem ON t.id_conta_origem = c_origem.id_conta
            LEFT JOIN cliente cl_origem ON c_origem.id_cliente = cl_origem.id_cliente
            LEFT JOIN usuario u_origem ON cl_origem.id_usuario = u_origem.id_usuario

            -- LEFT JOINS para buscar dados de contas de DESTINO
            LEFT JOIN conta c_destino ON t.id_conta_destino = c_destino.id_conta
            LEFT JOIN cliente cl_destino ON c_destino.id_cliente = cl_destino.id_cliente
            LEFT JOIN usuario u_destino ON cl_destino.id_usuario = u_destino.id_usuario

            -- LEFT JOINS para Caixinhas (origem/destino)
            LEFT JOIN investimento_caixinha ci_origem ON t.id_caixinha_origem = ci_origem.id_caixinha
            LEFT JOIN investimento_caixinha ci_destino ON t.id_caixinha_destino = ci_destino.id_caixinha

            WHERE 
                t.id_conta_origem = %s OR t.id_conta_destino = %s
                OR ci_origem.id_conta_investimento = %s
                OR ci_destino.id_conta_investimento = %s
            ORDER BY t.data_transacao DESC 
            LIMIT 200
        """
        try:
            with conn.cursor(dictionary=True) as cur:
                # Usa o account_id para todas as 4 checagens
                cur.execute(query, (account_id, account_id, account_id, account_id))
                rows = cur.fetchall()
                transacoes = []
                for row in rows:
                    if 'valor' in row and row['valor'] is not None:
                        row['valor'] = Decimal(row['valor'])

                    # Mapeia os campos da Entidade Transacao (base)
                    known_keys = Transacao.__annotations__.keys()
                    valid_keys = known_keys | {'id_transacao'}
                    filtered_row = {k: v for k, v in row.items() if k in valid_keys}

                    # CORREÇÃO CRÍTICA DE ATRIBUIÇÃO E SINAL DO VALOR
                    tx = Transacao(**filtered_row)

                    # Atribuição dos campos de exibição (que não estão no __annotations__)
                    tx.conta_origem = row.get('conta_origem_num')
                    tx.conta_destino = row.get('conta_destino_num')
                    tx.cpf_cliente_origem = row.get('cpf_origem')
                    tx.cpf_cliente_destino = row.get('cpf_destino')
                    tx.caixinha_nome = row.get('caixinha_nome')

                    # Ajuste do sinal do valor (Débito deve ser Negativo)
                    # Se a transação é débito desta conta (origem) ou caixinha (origem)
                    is_debit = (row.get('id_conta_origem') == account_id or
                                row.get('id_caixinha_origem') is not None)

                    if is_debit and tx.valor > 0:
                        tx.valor = -tx.valor

                    transacoes.append(tx)
                return transacoes
        except Exception as e:
            print(f"Erro em get_statement (com JOINS): {e}")
            return []
        finally:
            if conn: conn.close()

    def save(self, uow: IUnitOfWork, transacao: Transacao):
        """Salva a entidade Transacao no banco de dados."""

        # Mapeia a entidade para um dicionário de dados do SQL
        data = transacao.__dict__.copy()

        # CORREÇÃO AQUI: Renomeia 'tipo' de volta para 'tipo_transacao' (nome da coluna SQL)
        if 'tipo' in data:
            data['tipo_transacao'] = data.pop('tipo')

        # Remove chaves da entidade que não são colunas do banco (as que foram adicionadas para a GUI)
        data.pop('conta_origem', None)
        data.pop('conta_destino', None)
        data.pop('cpf_cliente_origem', None)
        data.pop('cpf_cliente_destino', None)
        data.pop('caixinha_nome', None)

        # Prepara a lista de campos para o INSERT
        campos = [
            'id_conta_origem', 'id_conta_destino', 'valor', 'tipo_transacao',
            'descricao', 'data_transacao', 'id_caixinha_origem', 'id_caixinha_destino'
        ]

        # Filtra e monta a lista de valores na ordem correta
        # Note que estamos usando data.get(campo) para obter o valor que agora usa 'tipo_transacao'
        params = tuple(data.get(campo) for campo in campos)

        placeholders = ', '.join(['%s'] * len(campos))
        column_names = ', '.join(campos)

        # Query FINAL: Usa o nome da coluna correto no SQL
        query = f"""
            INSERT INTO transacao 
            ({column_names})
            VALUES ({placeholders})
        """

        cursor = None
        try:
            cursor = uow.connection.cursor()
            cursor.execute(query, params)
        except Exception as e:
            print(f"Erro ao salvar transação (UoW): {e}")
            raise
        finally:
            if cursor:
                cursor.close()

    # ---
    # --- IMPLEMENTAÇÃO DOS NOVOS MÉTODOS (v4.0)
    # ---

    def get_movimentacoes_report_from_view(
            self,
            start_date: str,
            end_date: str,
            tipo_transacao: Optional[str] = None,
            id_agencia: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca o relatório avançado de movimentações usando a VIEW
        com filtros dinâmicos.
        """
        conn = self._get_connection()
        if not conn: return []

        try:
            # Constrói a query dinâmica
            query_parts = ["SELECT * FROM vw_relatorio_movimentacoes"]
            where_clauses = ["data_transacao >= %s", "data_transacao < DATE_ADD(%s, INTERVAL 1 DAY)"]
            params = [start_date, end_date]

            if tipo_transacao:
                where_clauses.append("tipo_transacao = %s")
                params.append(tipo_transacao)

            if id_agencia:
                where_clauses.append("(agencia_origem = %s OR agencia_destino = %s)")
                params.append(id_agencia)
                params.append(id_agencia)

            query = " ".join(query_parts) + " WHERE " + " AND ".join(where_clauses) + " ORDER BY data_transacao DESC"

            with conn.cursor(dictionary=True) as cur:
                cur.execute(query, tuple(params))
                return cur.fetchall()
        except Exception as e:
            print(f"Erro ao buscar relatório de movimentações: {e}")
            return []
        finally:
            if conn: conn.close()