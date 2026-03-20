import os
import sys
from typing import Optional, List, Dict, Any, Union
from decimal import Decimal
from mysql.connector import Error

# Ajuste automático de path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from src.core.use_cases.interfaces.i_usuario_repository import IUsuarioRepository
from src.core.use_cases.interfaces.i_unit_of_work import IUnitOfWork
from src.core.entities.usuario import Usuario


class MySQLUsuarioRepository(IUsuarioRepository):
    """
    Implementação CONCRETA do repositório de Usuário (MySQL) (v2).
    """

    def __init__(self, pool) -> None:
        """Inicializa o repositório com o pool de conexões."""
        # Corrigido: _pool deve ser acessado via self.pool
        self.pool = pool

    def _get_connection(self):
        """Obtém uma conexão para operações de leitura."""
        return self.pool.get_connection()

    def find_by_cpf_for_login(self, uow: IUnitOfWork, cpf: str) -> Optional[dict]:
        """
        Busca um usuário pelo CPF e traz todos os dados necessários
        para login (cliente ou funcionário).
        """
        query = """
            SELECT 
                u.id_usuario, u.nome, u.cpf, u.senha_hash, u.tipo_usuario,
                u.status, u.tentativas_login, u.data_nascimento, u.endereco, 
                u.telefone, u.score_credito,
                c.id_cliente,
                f.id_funcionario, f.id_agencia, f.cargo, f.salario 
            FROM usuario u
            LEFT JOIN cliente c ON c.id_usuario = u.id_usuario
            LEFT JOIN funcionario f ON f.id_usuario = u.id_usuario 
            WHERE u.cpf = %s
        """
        cursor = None
        try:
            cursor = uow.connection.cursor(dictionary=True)
            cursor.execute(query, (cpf,))
            usuario = cursor.fetchone()
            return usuario
        except Exception as e:
            print(f"Erro ao buscar usuário por CPF: {e}")
            raise
        finally:
            if cursor:
                cursor.close()

    def save_user(self, uow: IUnitOfWork, nome: str, cpf: str, senha_hash: str, tipo_usuario: str,
                  data_nascimento: Optional[str], endereco: Optional[str], telefone: Optional[str]) -> int:
        """Salva um novo usuário na tabela 'usuario' e retorna o id gerado."""
        query = """
            INSERT INTO usuario (nome, cpf, senha_hash, tipo_usuario, status, data_nascimento, endereco, telefone)
            VALUES (%s, %s, %s, %s, 'ATIVO', %s, %s, %s)
        """
        data_nasc_sql = data_nascimento if data_nascimento else None
        endereco_sql = endereco if endereco else None
        telefone_sql = telefone if telefone else None

        params = (nome, cpf, senha_hash, tipo_usuario, data_nasc_sql, endereco_sql, telefone_sql)

        cursor = None
        try:
            cursor = uow.connection.cursor()
            cursor.execute(query, params)
            id_usuario_gerado = cursor.lastrowid
            return id_usuario_gerado
        except Error as e:
            print(f"Erro ao salvar usuário: {e}")
            raise
        finally:
            if cursor:
                cursor.close()

    def save_client(self, uow: IUnitOfWork, id_usuario: int) -> int:
        """Cria um registro na tabela 'cliente'."""
        query = "INSERT INTO cliente (id_usuario) VALUES (%s)"
        cursor = None
        try:
            cursor = uow.connection.cursor()
            cursor.execute(query, (id_usuario,))
            return cursor.lastrowid
        except Exception as e:
            print(f"Erro ao salvar cliente: {e}")
            raise
        finally:
            if cursor:
                cursor.close()

    def save_employee(self, uow: IUnitOfWork, id_usuario: int, id_agencia: int, cargo: Optional[str],
                      salario: Optional[Decimal]) -> int:
        """Salva um novo funcionário na tabela 'funcionario'."""
        query = "INSERT INTO funcionario (id_usuario, id_agencia, cargo, salario) VALUES (%s, %s, %s, %s)"
        cursor = None
        try:
            cursor = uow.connection.cursor()
            cursor.execute(query, (id_usuario, id_agencia, cargo, salario))
            id_funcionario_gerado = cursor.lastrowid
            return id_funcionario_gerado
        except Error as e:
            print(f"Erro ao salvar funcionário: {e}")
            # Verifica se o erro é do Trigger de limite
            if '45000' in str(e):  # Código de erro para SIGNAL SQLSTATE
                raise ValueError("Limite de funcionários para esta agência foi atingido.")
            raise
        finally:
            if cursor:
                cursor.close()

    def update_login_status(self, uow, usuario: Usuario):
        """
        Atualiza o status de login do usuário no banco (tentativas, status, último login).
        """
        query = """
            UPDATE usuario
            SET tentativas_login = %s,
                status = %s,
                data_ultimo_login = NOW()
            WHERE id_usuario = %s
        """
        params = (usuario.tentativas_login, usuario.status, usuario.id_usuario)
        cursor = None
        try:
            cursor = uow.connection.cursor()
            cursor.execute(query, params)
        except Exception as e:
            print(f"Erro ao atualizar status de login do usuário: {e}")
            raise
        finally:
            if cursor:
                cursor.close()

    def block_user(self, uow: IUnitOfWork, usuario: Usuario):
        """Marca um usuário como INATIVO e atualiza o banco."""
        usuario.status = 'INATIVO'
        self.update_login_status(uow, usuario)

    def delete_user(self, uow: IUnitOfWork, id_usuario: int) -> bool:
        """Executa a exclusão física do usuário. (Usado pela funcionalidade antiga)."""
        query = "DELETE FROM usuario WHERE id_usuario = %s"
        cursor = None
        try:
            cursor = uow.connection.cursor()
            cursor.execute(query, (id_usuario,))
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Erro no repositório ao deletar usuário: {e}")
            raise
        finally:
            if cursor:
                cursor.close()

    # ---
    # --- IMPLEMENTAÇÃO DOS NOVOS MÉTODOS (v4.0)
    # ---

    def _exec_read_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Helper genérico para consultas de leitura (usando VIEWs)."""
        conn = self._get_connection()
        if not conn: return []
        try:
            with conn.cursor(dictionary=True) as cur:
                cur.execute(query, params)
                return cur.fetchall()
        except Exception as e:
            print(f"Erro ao executar consulta de leitura: {e}")
            return []
        finally:
            if conn: conn.close()

    def find_client_details_from_view(self, cpf: str) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM vw_consulta_cliente WHERE cpf = %s"
        results = self._exec_read_query(query, (cpf,))
        return results[0] if results else None

    def find_all_clients_from_view(self) -> List[Dict[str, Any]]:
        query = "SELECT * FROM vw_consulta_cliente ORDER BY nome"
        return self._exec_read_query(query)

    def find_employee_details_from_view(self, cpf: str) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM vw_consulta_funcionario WHERE cpf = %s"
        results = self._exec_read_query(query, (cpf,))
        return results[0] if results else None

    def find_all_employees_from_view(self) -> List[Dict[str, Any]]:
        query = "SELECT * FROM vw_consulta_funcionario ORDER BY nome"
        return self._exec_read_query(query)

    def _exec_update_query(self, uow: IUnitOfWork, query: str, params: tuple):
        """Helper genérico para queries de atualização (UPDATE)."""
        cursor = None
        try:
            cursor = uow.connection.cursor()
            cursor.execute(query, params)
        except Exception as e:
            print(f"Erro ao executar update: {e}")
            raise
        finally:
            if cursor:
                cursor.close()

    def update_user_details(self, uow: IUnitOfWork, id_usuario: int, details: Dict[str, Any]):
        """Altera dados de um usuário (telefone, endereço)."""
        campos_permitidos = ['nome', 'data_nascimento', 'endereco', 'telefone']
        set_parts = []
        valores_tupla = []

        for key, value in details.items():
            if key in campos_permitidos:
                set_parts.append(f"{key} = %s")
                valores_tupla.append(value)

        if not set_parts: return  # Nada a fazer

        query = f"UPDATE usuario SET {', '.join(set_parts)} WHERE id_usuario = %s"
        valores_tupla.append(id_usuario)

        self._exec_update_query(uow, query, tuple(valores_tupla))

    def update_employee_details(self, uow: IUnitOfWork, id_funcionario: int, details: Dict[str, Any]):
        """Altera dados de um funcionário (cargo, salario, id_agencia)."""
        campos_permitidos = ['cargo', 'salario', 'id_agencia']
        set_parts = []
        valores_tupla = []

        for key, value in details.items():
            if key in campos_permitidos:
                set_parts.append(f"{key} = %s")
                valores_tupla.append(value)

        if not set_parts: return  # Nada a fazer

        query = f"UPDATE funcionario SET {', '.join(set_parts)} WHERE id_funcionario = %s"
        valores_tupla.append(id_funcionario)

        self._exec_update_query(uow, query, tuple(valores_tupla))

    def update_password(self, uow: IUnitOfWork, id_usuario: int, new_hash: str):
        """Altera a senha de um usuário."""
        # O trigger 'trg_log_mudanca_senha' registrará isso.
        query = "UPDATE usuario SET senha_hash = %s WHERE id_usuario = %s"
        self._exec_update_query(uow, query, (new_hash, id_usuario))

    def call_proc_calcular_score(self, uow: IUnitOfWork, id_cliente: int) -> Union[int, Decimal]:
        """Chama a procedure de score e retorna o novo score."""
        cursor = None
        try:
            cursor = uow.connection.cursor()
            args = (id_cliente, 0)  # (p_id_cliente IN, p_score OUT)
            result_args = cursor.callproc('proc_calcular_score_cliente', args)
            new_score = result_args[1]  # Pega o valor do parâmetro OUT
            print(f"Repositório: Score do cliente {id_cliente} recalculado para {new_score}.")
            return new_score
        except Error as e:
            print(f"Erro ao chamar proc_calcular_score_cliente: {e}")
            raise ValueError(f"Erro na Procedure de Score: {e.msg}")
        finally:
            if cursor:
                cursor.close()

    def call_proc_desempenho_func(self, id_funcionario: int) -> Dict[str, Any]:
        """Chama a procedure de desempenho (read-only)."""
        conn = self._get_connection()
        if not conn: return {}
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.callproc('proc_relatorio_desempenho_func', (id_funcionario,))

            # Recupera o SELECT retornado pela procedure
            result = {}
            for res in cursor.stored_results():
                result = res.fetchone()

            print(f"Repositório: Desempenho do func {id_funcionario} buscado.")
            return result
        except Error as e:
            print(f"Erro ao chamar proc_relatorio_desempenho_func: {e}")
            raise ValueError(f"Erro na Procedure de Desempenho: {e.msg}")
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    # ---
    # --- MÉTODOS FALTANTES IMPLEMENTADOS (NECESSÁRIOS PARA A GUI)
    # ---

    def find_user_by_cpf_and_dob(self, cpf: str, data_nasc: str) -> Optional[Usuario]:
        """Implementação da busca do usuário pelo CPF e Data de Nascimento."""
        conn = self._get_connection()
        if not conn: return None

        # A data_nasc deve estar no formato 'AAAA-MM-DD'
        query = """
            SELECT * FROM usuario 
            WHERE cpf = %s AND data_nascimento = %s AND tipo_usuario = 'CLIENTE'
        """
        try:
            with conn.cursor(dictionary=True) as cur:
                cur.execute(query, (cpf, data_nasc))
                row = cur.fetchone()

                if row:
                    # Converte o resultado da linha (row) em um objeto Usuario
                    return Usuario.from_dict(row)
                return None
        except Exception as e:
            print(f"Erro em find_user_by_cpf_and_dob: {e}")
            return None
        finally:
            if conn: conn.close()

    def get_user_id_by_client_id(self, id_cliente: int) -> Optional[int]:
        """Busca o id_usuario a partir do id_cliente."""
        conn = self._get_connection()
        if not conn: return None

        query = "SELECT id_usuario FROM cliente WHERE id_cliente = %s"

        try:
            with conn.cursor(dictionary=True) as cur:
                cur.execute(query, (id_cliente,))
                row = cur.fetchone()

                if row:
                    return row['id_usuario']
                return None
        except Exception as e:
            print(f"Erro em get_user_id_by_client_id: {e}")
            return None
        finally:
            if conn: conn.close()