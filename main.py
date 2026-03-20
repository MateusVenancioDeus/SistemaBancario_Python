"""
Ponto de entrada principal da aplicação.
Configura a Injeção de Dependência (DI) e inicia a aplicação.
Esta é a versão de "Produção", que se conecta ao banco de dados real.
"""
import sys

# 1. Importar a GUI (Camada mais externa)
from src.infrastructure.gui.app_tk import App

# 2. Importar os componentes de infraestrutura (Adaptadores)
from src.infrastructure.db.connection import MySQLConnectionPool, get_uow_factory
from src.infrastructure.db.repositories.mysql_usuario_repo import MySQLUsuarioRepository
from src.infrastructure.db.repositories.mysql_conta_repo import MySQLContaRepository
from src.infrastructure.db.repositories.mysql_transacao_repo import MySQLTransacaoRepository

# 3. Importar os Serviços (Casos de Uso / Lógica de Negócio)
from src.core.use_cases.auth_service import AuthService
from src.core.use_cases.conta_service import ContaService

def main():
    """
    Função principal que monta e executa a aplicação.
    """
    print("Iniciando a aplicação em modo de PRODUÇÃO (MySQL)...")

    # --- ETAPA 1: Inicializar a Camada de Infraestrutura (Banco de Dados) ---
    try:
        # Inicializa o pool de conexões com o MySQL
        db_pool = MySQLConnectionPool.get_pool()

        # Obtém a "fábrica" que cria Unidades de Trabalho (para transações)
        uow_factory = get_uow_factory()

        print("✅ Pool de Conexão e Fábrica de UoW criados com sucesso.")

    except Exception as e:
        print("\n" + "=" * 50)
        print("🚨 ERRO FATAL: Não foi possível conectar ao Banco de Dados.")
        print(f"Erro: {e}")
        print("\nPor favor, verifique:")
        print(" 1. O serviço do MySQL está rodando na sua máquina.")
        print(" 2. As credenciais (usuário, senha, database) no arquivo 'config.py' estão corretas.")
        print(" 3. Você executou o script SQL v4.0 para criar o banco 'banco_malvader'.")
        print("=" * 50)
        sys.exit(1)  # Encerra a aplicação se não puder conectar

    # --- ETAPA 2: Montar os Repositórios (Adaptadores de Dados) ---
    usuario_repo_impl = MySQLUsuarioRepository(pool=db_pool)
    conta_repo_impl = MySQLContaRepository(pool=db_pool)
    transacao_repo_impl = MySQLTransacaoRepository(pool=db_pool)

    print("✅ Repositórios (Adaptadores de Dados) instanciados.")

    # --- ETAPA 3: Montar os Serviços (Casos de Uso) ---
    # Injetamos as dependências corretas em CADA serviço.

    auth_service_use_case = AuthService(
        usuario_repo=usuario_repo_impl,
        conta_repo=conta_repo_impl,
        uow_factory=uow_factory
    )

    # --- CORREÇÃO AQUI ---
    # O ContaService (v2) agora também precisa do usuario_repo.
    conta_service_use_case = ContaService(
        conta_repo=conta_repo_impl,
        transacao_repo=transacao_repo_impl,
        usuario_repo=usuario_repo_impl, # <-- Nova dependência adicionada
        uow_factory=uow_factory
    )
    # --- FIM DA CORREÇÃO ---

    print("✅ Casos de Uso (Serviços) instanciados.")

    # --- ETAPA 4: Montar a GUI (Framework) ---
    print("🚀 Instanciando a GUI...")
    app = App(
        auth_service=auth_service_use_case,
        conta_service=conta_service_use_case
    )
    print("✨ GUI instanciada. Iniciando mainloop...")

    # --- ETAPA 5: Executar a Aplicação ---
    app.mainloop()


if __name__ == "__main__":
    main()