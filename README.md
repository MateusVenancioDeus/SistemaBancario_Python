# Sistema Bancário com Python e MySQL

Bem-vindo ao projeto de Sistema Bancário, uma aplicação que simula operações bancárias básicas com uma interface gráfica intuitiva. Este guia detalha a configuração do ambiente, a estrutura do código e como executar o projeto.

## 🎯 Funcionalidades

Este sistema oferece as seguintes funcionalidades:

*   **Login:** Autenticação como cliente ou funcionário.
*   **Consulta:** Verificação de saldo e extrato da conta.
*   **Transações:** Realização de depósitos, saques e transferências.

## 🛠️ Tecnologias Utilizadas

*   **Python:** Linguagem de programação para a lógica de negócio.
*   **CustomTkinter:** Framework para a construção da interface gráfica (GUI).
*   **MySQL:** Sistema de gerenciamento de banco de dados para persistência dos dados.

## 🚀 Configuração do Ambiente

Para configurar e executar o projeto, siga os passos abaixo:

### 1. Configuração do Banco de Dados MySQL

O projeto utiliza um banco de dados MySQL para armazenar todas as informações. Certifique-se de ter um servidor MySQL instalado e em execução na sua máquina.

#### a. Criar o Banco de Dados

Abra seu terminal ou cliente MySQL (ex: MySQL Workbench) e execute o seguinte comando para criar o banco de dados:

```sql
CREATE DATABASE banco_malvader;
USE banco_malvader;
```

#### b. Criar Tabelas e Estruturas

O arquivo `banco_malvader_v4.sql` (localizado na raiz do projeto) contém todos os comandos necessários para criar as tabelas, views, procedures, triggers e dados iniciais. Execute este script no seu cliente MySQL para configurar a estrutura completa do banco de dados.

### 2. Conexão Python com o Banco de Dados

#### a. Instalar Dependências

O projeto utiliza a biblioteca `mysql-connector-python` para a comunicação com o MySQL. Todas as dependências estão listadas no arquivo `src/requeriments.txt`. Instale-as usando `pip`:

```bash
pip install -r src/requeriments.txt
```

#### b. Configurar Credenciais do Banco

Edite o arquivo `src/config.py` com as credenciais de acesso ao seu servidor MySQL. **Atenção:** Substitua `'SUA_SENHA'` pela senha correta do seu usuário MySQL.

```python
# src/config.py
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'SUA_SENHA', # << MUDE AQUI para a senha que você definiu
    'database': 'banco_malvader',
    'charset': 'utf8mb4',
    'raise_on_warnings': True,
    'autocommit': False
}
```

## 📂 Estrutura do Projeto

O projeto segue uma **Arquitetura Limpa (Clean Architecture)**, separando as responsabilidades em camadas para facilitar a manutenção e escalabilidade:

```
. 
├── banco_malvader_v4.sql      # Script SQL completo
├── test_connection.py         # Script de teste de conexão
└── src/
    ├── main.py                # Ponto de entrada da aplicação
    ├── config.py              # Configurações do banco de dados
    ├── requeriments.txt       # Dependências do projeto
    ├── core/                  # Lógica de negócio pura
    │   ├── entities/          # Definição de entidades (Usuario, Conta, etc.)
    │   └── use_cases/         # Regras de negócio (AuthService, ContaService)
    ├── infrastructure/        # Detalhes técnicos e interação com o exterior
    │   ├── db/                # Conexão e repositórios MySQL
    │   ├── gui/               # Interface gráfica (CustomTkinter)
    │   └── scripts/           # Scripts utilitários (hash_passwords.py)
```

### Camadas da Arquitetura:

*   **Core (`src/core/`):** Contém a lógica de negócio principal, independente de banco de dados ou interface. Inclui `entities` (estruturas de dados) e `use_cases` (regras de negócio).
*   **Infrastructure (`src/infrastructure/`):** Lida com os detalhes técnicos de interação com o mundo externo, como o banco de dados (`db/`) e a interface gráfica (`gui/`).
*   **Main (`main.py`):** Atua como o 
"maestro" que coordena a inicialização da aplicação, orquestrando as dependências.

## 🚀 Como Executar o Projeto

1.  **Clone este repositório:**

    ```bash
    git clone https://github.com/SEU-USUARIO/nome-do-seu-repositorio.git
    cd nome-do-seu-repositorio
    ```

2.  **Instale as dependências:**

    ```bash
    pip install -r src/requeriments.txt
    ```

3.  **(Opcional, mas recomendado) Atualize as senhas:**

    O script `src/scripts/hash_passwords.py` converte as senhas de exemplo do banco de dados para o formato seguro (bcrypt) utilizado pela aplicação.

    ```bash
    python src/scripts/hash_passwords.py
    ```

4.  **Execute a aplicação:**

    ```bash
    python src/main.py
    ```

    Uma janela gráfica deverá aparecer, e você poderá interagir com o sistema bancário.

## 🔐 Usuários de Teste

O script SQL (`banco_malvader_v4.sql`) cria automaticamente alguns usuários de exemplo para facilitar os testes. Abaixo estão os dados de login:

| Nome            | CPF         | Senha Original | Tipo        |
| :-------------- | :---------- | :------------- | :---------- |
| Lucas Andrade   | 91528476031 | lucas@2025     | CLIENTE     |
| Bianca Ferreira | 38461729508 | bia#7788       | CLIENTE     |
| Thiago Martins  | 57291836450 | thiago!99      | CLIENTE     |
| Fernanda Souza  | 80615394722 | fernanda*55    | CLIENTE     |
| Carlos Lima     | 90716283455 | carlos@123     | FUNCIONARIO |

**Importante:** Se você executou o script `hash_passwords.py`, as senhas acima foram convertidas para um formato seguro. Utilize-as conforme a configuração do seu sistema.

## ❓ Problemas Comuns e Soluções

*   **"Access denied for user 'root'@'localhost'"**
    *   **Causa:** Senha incorreta em `src/config.py`.
    *   **Solução:** Corrija a senha do MySQL no arquivo `src/config.py`.

*   **"Unknown database 'banco_malvader'"**
    *   **Causa:** O banco de dados não foi criado.
    *   **Solução:** Execute `CREATE DATABASE banco_malvader;` no MySQL.

*   **"Can't connect to MySQL server"**
    *   **Causa:** O servidor MySQL não está em execução.
    *   **Solução (Windows):** Inicie o serviço MySQL em "Serviços".
    *   **Solução (Linux/macOS):** Execute `sudo systemctl start mysql` ou `brew services start mysql`.

*   **"ModuleNotFoundError: No module named 'mysql'"**
    *   **Causa:** A biblioteca `mysql-connector-python` não está instalada.
    *   **Solução:** Execute `pip install -r src/requeriments.txt`.

*   **Login não funciona mesmo com a senha correta**
    *   **Causa:** As senhas no banco estão em MD5, mas o código espera bcrypt.
    *   **Solução:** Execute `python src/scripts/hash_passwords.py` para atualizar as senhas.

## 📚 Conceitos Importantes

Este projeto demonstra a aplicação de conceitos fundamentais de desenvolvimento de software:

*   **Pool de Conexões:** Otimiza a comunicação com o banco de dados, reutilizando conexões e melhorando a performance.
*   **Injeção de Dependência:** Facilita a testabilidade e a manutenção do código, permitindo que as classes recebam suas dependências externamente.
*   **Separação de Camadas (Clean Architecture):** Garante que a lógica de negócio seja independente da infraestrutura, tornando o sistema mais flexível e adaptável a mudanças.
*   **Bcrypt para Senhas:** Utiliza um algoritmo robusto para armazenar senhas de forma segura, protegendo os dados dos usuários.

## 📝 Licença

Este projeto foi desenvolvido para fins educacionais.
