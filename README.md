Guia do Projeto: Sistema Bancário com Python e MySQL

Bem-vindo! Este guia foi criado para ajudar você a entender e executar este projeto de sistema bancário. Vamos passar por tudo, desde a criação do banco de dados até a explicação de como o código Python funciona.

🎯 O que este projeto faz?

Este é um programa de computador que simula um sistema de banco. Ele tem uma interface gráfica onde você pode:

•
Fazer login como cliente ou funcionário.

•
Verificar saldo e extrato da conta.

•
Realizar depósitos, saques e transferências.

O projeto usa Python para a lógica, CustomTkinter para a interface gráfica e MySQL para guardar todas as informações (dados de usuários, contas, transações, etc.).




1️⃣ Passo 1: Criando o Banco de Dados no MySQL

O "cérebro" que armazena todos os dados do nosso sistema é um banco de dados MySQL. Antes de rodar o código Python, precisamos preparar este banco.

a. O que você precisa?

•
Um servidor MySQL instalado na sua máquina. Se não tiver, você pode baixar o MySQL Community Server no site oficial.

b. Criando o Banco de Dados

1.
Abra o seu terminal ou um cliente de MySQL (como o MySQL Workbench).

2.
Conecte-se ao seu servidor MySQL com seu usuário e senha (geralmente o usuário é root).

3.
Execute o comando abaixo para criar o banco de dados que o projeto vai usar:

c. Criando as Tabelas e Estruturas

Agora que o banco de dados está criado, precisamos criar as "gavetas" (tabelas) onde os dados serão guardados. O arquivo banco_malvader_v4.sql (que acompanha este projeto) já tem todos os comandos para isso.

1.
Use o banco de dados que acabamos de criar:

2.
Execute o script banco_malvader_v4.sql. A forma mais fácil é abrir o arquivo em um cliente MySQL (como o Workbench) e clicar para executar o script inteiro. Isso irá criar automaticamente:

•
Tabelas: usuario, conta, transacao, etc.

•
Views: Consultas salvas para relatórios.

•
Procedures: Funções complexas que rodam no banco.

•
Triggers: Ações automáticas (como registrar logs).

•
Dados Iniciais: Alguns usuários e contas de exemplo.



Pronto! Seu banco de dados está configurado.




2️⃣ Passo 2: Conectando o Python com o Banco de Dados

Agora, precisamos dizer ao nosso código Python como encontrar e acessar o banco de dados que criamos.

a. A Biblioteca de Conexão

Para que o Python possa "conversar" com o MySQL, usamos uma biblioteca chamada mysql-connector-python. Ela já está incluída no arquivo requeriments.txt e será instalada com o comando pip install.

b. O Arquivo de Configuração (src/config.py)

Este é o arquivo mais importante para a conexão. É aqui que você coloca as "credenciais" de acesso ao seu banco de dados.

Abra o arquivo src/config.py e edite as informações:

Python


# src/config.py

DB_CONFIG = {
    'host': 'localhost',       # Mantenha 'localhost' se o MySQL estiver na sua máquina
    'port': 3306,              # Porta padrão do MySQL
    'user': 'root',            # O usuário que você usa para acessar o MySQL
    'password': 'SUA_SENHA',   # << MUDE AQUI para a senha que você definiu
    'database': 'banco_malvader', # O nome do banco que criamos
    'charset': 'utf8mb4',
    'raise_on_warnings': True,
    'autocommit': False
}


Atenção: Substitua 'SUA_SENHA' pela senha correta do seu banco de dados MySQL.

c. Como a Conexão Funciona no Código

O arquivo src/infrastructure/db/connection.py usa as informações do config.py para criar um Pool de Conexões. Pense nisso como um grupo de "funcionários" (conexões) prontos para atender a pedidos do Python. Em vez de contratar e demitir um funcionário para cada tarefa, o sistema reutiliza os que já estão disponíveis, tornando tudo mais rápido e eficiente.




3️⃣ Passo 3: Entendendo os Códigos em Python

O projeto é organizado em pastas para facilitar a manutenção. Aqui está um resumo do que cada parte faz:

•
main.py

•
É o ponto de partida de tudo. Quando você executa este arquivo, ele monta todas as peças do sistema e abre a janela principal da aplicação.



•
src/requeriments.txt

•
Lista de todas as bibliotecas Python que o projeto precisa para funcionar.



•
src/config.py

•
Como vimos, é onde ficam as configurações de conexão com o banco de dados.



•
src/core/

•
É o cérebro da aplicação. Contém a lógica de negócio pura, sem se preocupar com telas ou banco de dados.

•
entities/: Define as estruturas de dados (o que é um Usuario? O que é uma Conta?).

•
use_cases/: Contém as regras de negócio (como funciona um login, como se faz uma transferência, etc.).



•
src/infrastructure/

•
São as partes técnicas que interagem com o mundo exterior.

•
db/: Contém o código que efetivamente se conecta e executa comandos no banco de dados MySQL.

•
gui/: Contém todo o código da interface gráfica, definindo as telas, botões e campos que o usuário vê.



•
src/scripts/hash_passwords.py

•
Um script de utilidade. Os dados de exemplo no SQL usam senhas simples. Este script as atualiza para um formato criptografado e seguro (bcrypt), que é o que a aplicação usa de verdade.






🚀 Como Executar o Projeto

1.
Instale as dependências:

2.
(Opcional, mas recomendado) Atualize as senhas:

3.
Execute a aplicação:

Uma janela gráfica deverá aparecer, e você poderá usar o sistema!




🔐 Usuários de Teste

O script SQL cria automaticamente alguns usuários de exemplo para você testar o sistema. Aqui estão os dados de login:

Nome
CPF
Senha Original
Tipo
Lucas Andrade
91528476031
lucas@2025
CLIENTE
Bianca Ferreira
38461729508
bia#7788
CLIENTE
Thiago Martins
57291836450
thiago!99
CLIENTE
Fernanda Souza
80615394722
fernanda*55
CLIENTE
Carlos Lima (Gerente)
90716283455
carlos@123
FUNCIONARIO


Importante: Se você executou o script hash_passwords.py, as senhas foram convertidas para o formato seguro. Caso contrário, o sistema pode não aceitar o login (dependendo de como o código de autenticação está configurado).




🧠 Entendendo o Código Python em Detalhes

Vamos mergulhar um pouco mais fundo em como o código Python está estruturado e como ele funciona.

Arquitetura Limpa (Clean Architecture)

O projeto segue um padrão chamado Arquitetura Limpa, que separa as responsabilidades em camadas. Isso torna o código mais organizado e fácil de manter.

Camada 1: Core (Núcleo)

Esta é a camada mais interna, onde fica a lógica de negócio pura. Ela não sabe nada sobre banco de dados ou interface gráfica.

•
Entities (src/core/entities/): São as classes que representam os conceitos do sistema. Por exemplo, a classe Usuario define o que é um usuário (tem nome, CPF, senha, tipo, etc.). A classe Conta define o que é uma conta bancária (tem saldo, tipo, limite, etc.).

•
Use Cases (src/core/use_cases/): São os serviços que implementam as regras de negócio. Por exemplo, o AuthService cuida da lógica de login (verificar CPF, validar senha, controlar tentativas de login). O ContaService cuida das operações de conta (depósito, saque, transferência).

Camada 2: Infrastructure (Infraestrutura)

Esta camada contém os detalhes técnicos de como o sistema interage com o mundo externo.

•
Database (src/infrastructure/db/): Aqui estão os Repositórios, que são classes responsáveis por executar comandos SQL no banco de dados. Por exemplo, MySQLUsuarioRepository tem métodos como find_by_cpf() para buscar um usuário pelo CPF, ou save_user() para salvar um novo usuário no banco.

•
GUI (src/infrastructure/gui/): Aqui está todo o código da interface gráfica. O arquivo app_tk.py define as janelas, botões, campos de texto e como eles se comunicam com os serviços do Core.

Camada 3: Main (main.py)

Este arquivo é o "maestro" que coordena tudo. Ele:

1.
Cria o pool de conexões com o banco de dados.

2.
Instancia os repositórios (passando o pool para eles).

3.
Instancia os serviços (passando os repositórios para eles).

4.Instancia a interface gráfica (passando os serviços para ela).

5.Inicia a aplicação.

Essa técnica é chamada de Injeção de Dependência, e garante que cada parte do código receba exatamente o que precisa para funcionar.




🔌 Como o Python se Conecta ao MySQL: Passo a Passo

Vamos ver o que acontece "por baixo dos panos" quando o Python precisa buscar dados no banco:

1.O código chama um método do serviço:

2.O serviço chama um método do repositório:

3.O repositório pega uma conexão do pool:

4.O repositório executa uma query SQL:

5.O resultado é devolvido camada por camada:

6.A conexão é devolvida ao pool:




🛠️ Testando a Conexão com o Banco

Incluímos um script de teste para verificar se tudo está configurado corretamente. Execute:

Bash


python test_connection.py


Se tudo estiver certo, você verá uma mensagem de sucesso e a lista de tabelas do banco. Se houver erro, o script mostrará dicas de como resolver.




❓ Problemas Comuns e Soluções

Problema 1: "Access denied for user 'root'@'localhost'"

•Causa: A senha no arquivo config.py está incorreta.

•Solução: Abra src/config.py e corrija a senha do MySQL.

Problema 2: "Unknown database 'banco_malvader'"

•Causa: O banco de dados não foi criado.

•Solução: Execute o comando CREATE DATABASE banco_malvader; no MySQL.

Problema 3: "Can't connect to MySQL server"

•Causa: O servidor MySQL não está rodando.

•Solução (Windows): Abra "Serviços" e inicie o serviço MySQL.

•Solução (Linux/macOS): Execute sudo systemctl start mysql ou brew services start mysql.

Problema 4: "ModuleNotFoundError: No module named 'mysql'"

•Causa: A biblioteca mysql-connector-python não está instalada.

•Solução: Execute pip install -r src/requeriments.txt.

Problema 5: Login não funciona mesmo com a senha correta

•Causa: As senhas no banco estão em MD5, mas o código espera bcrypt.

•Solução: Execute python src/scripts/hash_passwords.py para atualizar as senhas.




📚 Recursos Avançados do Banco de Dados

O script SQL cria não apenas tabelas, mas também recursos avançados do MySQL:

Views (Consultas Salvas):

Views são como "atalhos" para consultas complexas. Por exemplo, a view vw_consulta_cliente já junta os dados de usuario e cliente para você.

SQL


SELECT * FROM vw_consulta_cliente WHERE cpf = '91528476031';


Stored Procedures (Funções no Banco):

São funções que rodam diretamente no banco de dados. Por exemplo, proc_calcular_score_cliente calcula o score de crédito de um cliente com base em vários fatores.

SQL


CALL proc_calcular_score_cliente(1, @score);
SELECT @score;


Triggers (Ações Automáticas):

Triggers são "gatilhos" que disparam automaticamente quando algo acontece. Por exemplo, o trigger trg_log_mudanca_senha registra automaticamente no log sempre que uma senha é alterada.




📂 Estrutura Completa do Projeto

Plain Text


.
├── banco_malvader_v4.sql           # Script SQL completo
├── test_connection.py              # Script de teste de conexão
├── .venv/                          # Ambiente virtual (criado por você)
└── src/
    ├── main.py                     # Ponto de entrada da aplicação
    ├── config.py                   # Configurações do banco de dados
    ├── requeriments.txt            # Dependências do projeto
    ├── core/
    │   ├── entities/
    │   │   ├── usuario.py          # Classe Usuario
    │   │   └── conta.py            # Classes Conta, Transacao, etc.
    │   └── use_cases/
    │       ├── auth_service.py     # Serviço de autenticação
    │       ├── conta_service.py    # Serviço de operações de conta
    │       └── interfaces/         # Contratos (interfaces)
    ├── infrastructure/
    │   ├── db/
    │   │   ├── connection.py       # Pool de conexões
    │   │   └── repositories/       # Repositórios (acesso ao banco)
    │   ├── gui/
    │   │   └── app_tk.py           # Interface gráfica
    │   └── utils/
    │       ├── security.py         # Funções de criptografia
    │       └── cpf_utils.py        # Validação de CPF
    └── scripts/
        └── hash_passwords.py       # Script para atualizar senhas





🎓 Conceitos Importantes para Entender o Projeto

1. Pool de Conexões:

Imagine que cada vez que você quer falar com o banco de dados, você precisa fazer uma ligação telefônica. Fazer e desligar chamadas o tempo todo é lento. O pool de conexões mantém várias "linhas abertas" e reutiliza elas, tornando tudo mais rápido.

2. Injeção de Dependência:

Em vez de cada classe criar suas próprias ferramentas, elas recebem as ferramentas prontas de fora. Isso facilita testar e modificar o código.

3. Separação de Camadas:

A lógica de negócio (Core) não sabe nada sobre MySQL ou Tkinter. Isso significa que você poderia trocar o MySQL por PostgreSQL, ou a interface gráfica por uma web, sem mexer na lógica principal.

4. Bcrypt para Senhas:

Nunca guarde senhas em texto puro! O bcrypt é um algoritmo que transforma a senha em um código irreversível. Mesmo se alguém roubar o banco de dados, não conseguirá descobrir as senhas originais.




🚀 Próximos Passos

Agora que você entende como tudo funciona, aqui estão algumas ideias para expandir o projeto:

•Adicionar mais tipos de transações (pagamento de contas, PIX, etc.).

•Criar relatórios gráficos com bibliotecas como matplotlib.

•Implementar autenticação de dois fatores (2FA).

•Migrar a interface para web usando Flask ou Django.

•Adicionar testes automatizados com pytest.




📝 Licença

Este projeto foi desenvolvido para fins educacionais.

