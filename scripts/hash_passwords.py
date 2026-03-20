# scripts/hash_passwords.py
"""
Script para atualizar as senhas MD5/texto-plano do banco para bcrypt.
Execute este script DEPOIS de rodar seu SQL inicial.
"""
import sys
import os

# Adiciona a raiz do projeto (PythonBD) ao path do Python
# Isso permite que o script importe de 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.infrastructure.db.connection import MySQLConnectionPool
    from src.infrastructure.utils.security import hash_password
    from config import DB_CONFIG  # Importa a config da raiz
except ImportError as e:
    print(f"Erro de importação: {e}")
    print("Certifique-se de que o script está na pasta 'scripts' e que 'src' existe.")
    sys.exit(1)

# Mapeia CPF para a senha em texto plano (do seu script SQL)
users_to_update = {
    '12345678901': 'rafael123',
    '23456789012': 'mateus123',
    '34567890123': 'leticia123',
    '45678901234': 'joao123',
}


def update_hashes():
    conn = None
    try:
        # Pega uma conexão direta, sem ser da UoW
        conn = MySQLConnectionPool.get_connection()
        if not conn:
            print("Erro: Não foi possível conectar ao banco.")
            return

        print("Conectado. Atualizando senhas para bcrypt...")

        with conn.cursor() as cur:
            for cpf, plain_password in users_to_update.items():
                print(f"Atualizando senha para o CPF: {cpf}...")

                # Gera o novo hash bcrypt
                new_hash = hash_password(plain_password)

                query = "UPDATE usuario SET senha_hash = %s WHERE cpf = %s"
                cur.execute(query, (new_hash, cpf))

                if cur.rowcount > 0:
                    print(f" -> Sucesso! Senha de {cpf} atualizada.")
                else:
                    print(f" -> Aviso: CPF {cpf} não encontrado no banco.")

            conn.commit()
            print("\nAtualização de senhas concluída com sucesso!")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"\nErro durante a atualização: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    update_hashes()