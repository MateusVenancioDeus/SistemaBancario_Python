# config.py
"""
Configurações do banco de dados.
"""

import os

# Detalhes da conexão com o banco de dados MySQL
# Usando os valores fornecidos, com fallback para variáveis de ambiente
# se disponíveis (o que é uma boa prática).
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '102030'),
    'database': 'banco_malvader',
    'charset': 'utf8mb4',
    'raise_on_warnings': True,
    'autocommit': False # Importante para a Unit of Work
}