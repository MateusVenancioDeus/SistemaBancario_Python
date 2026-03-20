import mysql.connector
from mysql.connector import pooling
from contextlib import contextmanager
from config import DB_CONFIG
from src.core.use_cases.interfaces.i_unit_of_work import IUnitOfWork
from typing import Callable


class MySQLConnectionPool:
    """Gerencia o pool de conexões MySQL (Singleton)."""
    _pool = None

    @classmethod
    def get_pool(cls):
        """Retorna a instância do pool, criando-a se não existir."""
        if cls._pool is None:
            try:
                cls._pool = mysql.connector.pooling.MySQLConnectionPool(
                    pool_name="banco_pool",
                    pool_size=5,
                    **DB_CONFIG
                )
                print("Pool de conexões inicializado.")
            except mysql.connector.Error as err:
                print(f"Erro ao inicializar pool: {err}")
                raise  # Propaga o erro para o main.py
        return cls._pool

    @classmethod
    def get_connection(cls):
        """Obtém uma conexão do pool (para leituras não transacionais)."""
        try:
            return cls.get_pool().get_connection()
        except mysql.connector.Error as err:
            print(f"Erro ao obter conexão do pool: {err}")
            raise


# -----------------------------------------------------------------
# Implementação Concreta da Unit of Work
# -----------------------------------------------------------------

class MySQLUnitOfWork(IUnitOfWork):
    """Implementação da Unit of Work para MySQL."""

    def __init__(self, pool):
        self._pool = pool
        self._connection = None

    def __enter__(self):
        """Obtém conexão do pool e inicia a transação."""
        self._connection = self._pool.get_connection()
        self._connection.start_transaction()
        # print("Transação iniciada.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Fecha a transação (commit/rollback) e devolve a conexão ao pool.
        """
        try:
            if exc_type:
                # Se ocorreu um erro, faz rollback
                print(f"Rollback devido a erro: {exc_val}")
                self.rollback()
            elif self._connection and self._connection.in_transaction:
                # Se não houve erro mas o commit não foi chamado, faz rollback
                # print("Rollback automático (commit() não foi chamado).")
                self.rollback()
        finally:
            # Garante que a conexão seja fechada e devolvida ao pool
            if self._connection:
                self._connection.close()
                # print("Conexão devolvida ao pool.")

    def commit(self):
        if self._connection and self._connection.in_transaction:
            self._connection.commit()
            # print("Transação commitada.")

    def rollback(self):
        if self._connection and self._connection.in_transaction:
            self._connection.rollback()
            # print("Transação revertida (rollback).")

    @property
    def connection(self):
        """Retorna a conexão ativa para os repositórios usarem."""
        if self._connection is None:
            raise Exception("Unit of Work não foi iniciada (use 'with ...').")
        return self._connection

# -----------------------------------------------------------------
# Factory (Fábrica)
# -----------------------------------------------------------------

def get_uow_factory() -> Callable[[], IUnitOfWork]:
    """
    Retorna uma *função* (factory) que, quando chamada,
    cria uma nova instância de MySQLUnitOfWork.
    """
    pool = MySQLConnectionPool.get_pool()

    def create_uow():
        return MySQLUnitOfWork(pool)

    return create_uow