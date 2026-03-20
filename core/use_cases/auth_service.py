from src.core.use_cases.interfaces.i_usuario_repository import IUsuarioRepository
from src.core.use_cases.interfaces.i_conta_repository import IContaRepository
from src.core.use_cases.interfaces.i_unit_of_work import IUnitOfWork
from src.infrastructure.utils.cpf_utils import only_digits
from src.infrastructure.utils.security import hash_password, verify_password
import hashlib  # Para MD5
from typing import Tuple, Optional, Callable, List, Dict, Any, Union
from decimal import Decimal, InvalidOperation

from src.core.entities.usuario import Usuario

MAX_LOGIN_ATTEMPTS = 5


class AuthService:
    """
    Caso de Uso: Autenticação e Gerenciamento de Usuários (v2).
    """

    def __init__(
            self,
            usuario_repo: IUsuarioRepository,
            conta_repo: IContaRepository,
            uow_factory: Callable[[], IUnitOfWork]
    ):
        self.usuario_repo = usuario_repo
        self.conta_repo = conta_repo
        self.uow_factory = uow_factory

    # ------------------------------------------------------------------
    ## 🔑 LOGIN
    # ------------------------------------------------------------------
    # Assinatura CORRETA para a GUI é Tuple[bool, Union[Usuario, str]]
    def login(self, cpf_input: str, senha: str) -> Tuple[bool, Union[Usuario, str]]:
        cpf = only_digits(cpf_input)
        if not cpf:
            return False, "CPF inválido."

        with self.uow_factory() as uow:
            # Chama o novo método do repo que busca TODOS os dados
            usuario_data = self.usuario_repo.find_by_cpf_for_login(uow, cpf)

        if not usuario_data:
            return False, "CPF não encontrado."

        # 'from_dict' agora preenche cargo, salario, score, etc.
        try:
            usuario = Usuario.from_dict(usuario_data)
        except Exception as e:
            # Captura erro se o repositório retornar dados inválidos
            print(f"Erro ao criar objeto Usuario: {e}")
            return False, "Erro interno ao processar dados do usuário."

        if not usuario.is_ativo:
            return False, "Usuário inativo. Contate o administrador."

        if usuario.is_bloqueado_por_tentativas:
            with self.uow_factory() as uow:
                self.usuario_repo.block_user(uow, usuario)
                uow.commit()
            return False, f"Usuário bloqueado por {MAX_LOGIN_ATTEMPTS} tentativas."

        # 'verificar_senha' (do security.py) deve lidar com MD5 ou bcrypt
        if not usuario.verificar_senha(senha):
            usuario.tentativas_login = (usuario.tentativas_login or 0) + 1
            with self.uow_factory() as uow:
                self.usuario_repo.update_login_status(uow, usuario)
                uow.commit()
            return False, f"Senha incorreta. Tentativas: {usuario.tentativas_login}/{MAX_LOGIN_ATTEMPTS}"

        usuario.tentativas_login = 0
        with self.uow_factory() as uow:
            self.usuario_repo.update_login_status(uow, usuario)
            uow.commit()

        if usuario.tipo_usuario == 'CLIENTE' and not usuario.id_cliente:
            return False, "Erro: Usuário cliente sem registro de cliente associado."

        if usuario.tipo_usuario == 'FUNCIONARIO' and not usuario.id_funcionario:
            return False, "Erro: Usuário funcionário sem registro de funcionário associado."

        # Retorno de sucesso
        return True, usuario

    # ------------------------------------------------------------------
    ## 📝 REGISTRO DE CLIENTE (Pelo próprio cliente, na tela pública)
    # ------------------------------------------------------------------
    def register_client(self, nome: str, cpf_input: str, senha: str, data_nasc: str, endereco: str, telefone: str) -> \
            Tuple[bool, str]:
        cpf = only_digits(cpf_input)
        if not cpf or len(cpf) != 11:
            return False, "CPF inválido. Deve conter 11 dígitos."
        if len(senha) < 4:
            return False, "Senha muito curta. Use pelo menos 4 caracteres."
        if not data_nasc or not endereco or not telefone:
            return False, "Nome, Data de Nascimento, Endereço e Telefone são obrigatórios."

        with self.uow_factory() as uow:
            if self.usuario_repo.find_by_cpf_for_login(uow, cpf):
                return False, "Este CPF já está cadastrado."

        # Usa MD5 para ser compatível com a procedure de login do SQL
        senha_hash = hashlib.md5(senha.encode("utf-8")).hexdigest()

        try:
            with self.uow_factory() as uow:
                id_usuario = self.usuario_repo.save_user(
                    uow=uow, nome=nome, cpf=cpf,
                    senha_hash=senha_hash, tipo_usuario='CLIENTE',
                    data_nascimento=data_nasc, endereco=endereco, telefone=telefone
                )
                id_cliente = self.usuario_repo.save_client(uow, id_usuario)

                id_agencia = 1  # Agência Padrão

                # Cria as 3 contas padrão
                # (A lógica de 'id_funcionario_abertura' fica nula, pois o cliente se cadastrou)
                num_cc = f"{id_cliente:04d}-CC-001"
                num_cp = f"{id_cliente:04d}-CP-001"
                num_ci = f"{id_cliente:04d}-CI-001"

                self.conta_repo.save_new_account(uow, id_cliente, id_agencia, num_cc, 'CC', Decimal("0.00"))
                self.conta_repo.save_new_account(uow, id_cliente, id_agencia, num_cp, 'CP', Decimal("0.00"))
                id_conta_investimento = self.conta_repo.save_new_account(uow, id_cliente, id_agencia, num_ci, 'CI',
                                                                         Decimal("0.00"))

                self.conta_repo.save_new_caixinha(uow, id_conta_investimento, 'CDI', Decimal("0.00"))
                self.conta_repo.save_new_caixinha(uow, id_conta_investimento, 'BOLSA', Decimal("0.00"))

                uow.commit()
                return True, f"Cliente {nome} cadastrado com sucesso! (CC, CP, CI criadas)"
        except Exception as e:
            print(f"ERRO no registro de cliente: {e}")
            if '1062' in str(e) and 'cpf' in str(e):
                return False, "Este CPF já está cadastrado."
            return False, f"Erro interno ao cadastrar: {e}"

    # ------------------------------------------------------------------
    ## 💼 REGISTRO DE FUNCIONÁRIO (Pelo Gerente)
    # ------------------------------------------------------------------
    def register_employee_completo(self,
                                   # Dados do novo funcionário
                                   nome: str, cpf_input: str, senha: str,
                                   data_nasc: str, telefone: str, endereco: str,
                                   salario_str: str, cargo: str, id_agencia: int,
                                   # Dados do admin que está logado
                                   admin_user: Usuario) -> Tuple[bool, str]:

        # 1. Validação de Permissão (Requisito: "nível gerente ou superior")
        if not admin_user or admin_user.tipo_usuario != 'FUNCIONARIO' or admin_user.cargo != 'GERENTE':
            return False, "Acesso Negado. Apenas GERENTES podem cadastrar novos funcionários."

        # 2. Validação de Dados
        cpf = only_digits(cpf_input)
        if not cpf or len(cpf) != 11:
            return False, "CPF inválido. Deve conter 11 dígitos."
        if len(senha) < 4:
            return False, "Senha muito curta. Use pelo menos 4 caracteres."
        if not all([data_nasc, telefone, endereco, salario_str, cargo]):
            return False, "Todos os campos do funcionário são obrigatórios."

        try:
            salario = Decimal(salario_str.replace(',', '.'))
            if salario <= 0:
                raise InvalidOperation
        except InvalidOperation:
            return False, "Salário inválido. Use apenas números (ex: 3500.00)."

        with self.uow_factory() as uow:
            if self.usuario_repo.find_by_cpf_for_login(uow, cpf):
                return False, "Este CPF já está cadastrado."

        # Usa MD5 para ser compatível com a procedure de login do SQL
        senha_hash = hashlib.md5(senha.encode("utf-8")).hexdigest()

        try:
            with self.uow_factory() as uow:
                # 3. Salva na tabela 'usuario'
                id_usuario = self.usuario_repo.save_user(
                    uow=uow,
                    nome=nome, cpf=cpf, senha_hash=senha_hash,
                    tipo_usuario="FUNCIONARIO",
                    data_nascimento=data_nasc,
                    endereco=endereco,
                    telefone=telefone
                )

                # 4. Salva na tabela 'funcionario'
                self.usuario_repo.save_employee(uow, id_usuario, id_agencia, cargo, salario)

                uow.commit()
                return True, f"Funcionário {nome} (Cargo: {cargo}) cadastrado com sucesso!"
        except ValueError as e:  # Captura erro do Trigger
            return False, str(e)
        except Exception as e:
            print(f"ERRO no registro de funcionário (completo): {e}")
            if '1062' in str(e) and 'cpf' in str(e):
                return False, "Este CPF já está cadastrado."
            return False, f"Erro interno ao cadastrar funcionário: {e}"

    # ------------------------------------------------------------------
    ## 📊 MÉTODOS DE CONSULTA (Views)
    # ------------------------------------------------------------------
    def get_all_clients_from_view(self) -> Tuple[bool, List[dict]]:
        try:
            clients_data = self.usuario_repo.find_all_clients_from_view()
            return True, clients_data
        except Exception as e:
            return False, ([f"Erro de banco de dados: {e}"],)  # Retorna tupla

    def get_client_details_from_view(self, cpf: str) -> Tuple[bool, Union[Dict[str, Any], str]]:
        try:
            cpf_limpo = only_digits(cpf)
            if not cpf_limpo:
                return False, "CPF não informado."

            # CORREÇÃO APLICADA AQUI: Chama o método find_client_details_from_view no repositório.
            client_data = self.usuario_repo.find_client_details_from_view(cpf_limpo)

            if not client_data:
                return False, "Cliente não encontrado."

            return True, client_data
        except Exception as e:
            # Captura a exceção original para depuração
            return False, f"Erro de banco de dados: {e}"

    def get_all_employees_from_view(self) -> Tuple[bool, List[dict]]:
        try:
            emp_data = self.usuario_repo.find_all_employees_from_view()
            return True, emp_data
        except Exception as e:
            return False, (f"Erro de banco de dados: {e}",)

    # ------------------------------------------------------------------
    ## 🔄 MÉTODOS DE ALTERAÇÃO (Updates)
    # ------------------------------------------------------------------
    def update_client_details(self, id_usuario: int, details: Dict[str, Any]) -> Tuple[bool, str]:
        """Altera dados de um cliente (telefone, endereço)."""
        try:
            with self.uow_factory() as uow:
                self.usuario_repo.update_user_details(uow, id_usuario, details)
                uow.commit()
            return True, "Dados do cliente atualizados com sucesso."
        except Exception as e:
            return False, f"Erro ao atualizar dados: {e}"

    def update_employee_details(self, id_funcionario: int, id_usuario: int, details_user: Dict[str, Any],
                                details_func: Dict[str, Any], admin_user: Usuario) -> Tuple[bool, str]:
        """Altera dados de um funcionário (requer permissão)."""

        # Validação de hierarquia (só gerente altera cargo)
        if 'cargo' in details_func:
            if not admin_user or admin_user.tipo_usuario != 'FUNCIONARIO' or admin_user.cargo != 'GERENTE':
                return False, "Acesso Negado. Apenas Gerentes podem alterar cargos."

        try:
            with self.uow_factory() as uow:
                if details_user:
                    self.usuario_repo.update_user_details(uow, id_usuario, details_user)
                if details_func:
                    self.usuario_repo.update_employee_details(uow, id_funcionario, details_func)
                uow.commit()
            return True, "Dados do funcionário atualizados com sucesso."
        except Exception as e:
            return False, f"Erro ao atualizar dados: {e}"

    def change_password(self, id_usuario_alvo: int, old_pass: str, new_pass: str, logged_in_user: Optional[Usuario]) -> \
    Tuple[
        bool, str]:
        """
        Altera a senha de um usuário.
        1. Se logged_in_user=None: É um reset (CPF+DOB), permite a troca.
        2. Se logged_in_user.id == id_usuario_alvo: É o próprio usuário, valida old_pass.
        3. Se logged_in_user é Admin: Permite a troca (validação de cargo).
        """
        try:
            if len(new_pass) < 4:
                return False, "Senha nova é muito curta."

            # --- LÓGICA DE PERMISSÃO CORRIGIDA ---

            # Caso 1: Redefinição de Senha (Fluxo de CPF + Data Nasc.)
            if logged_in_user is None:
                # A validação (CPF + DOB) já foi feita pela GUI antes de chamar este método.
                # Podemos prosseguir para a alteração.
                pass

            # Caso 2: Usuário logado mudando a própria senha
            elif logged_in_user.id_usuario == id_usuario_alvo:
                if not logged_in_user.verificar_senha(old_pass):
                    return False, "Senha antiga não confere."

            # Caso 3: Admin (Funcionário Gerente) mudando a senha de outro
            elif logged_in_user.tipo_usuario == 'FUNCIONARIO' and logged_in_user.cargo == 'GERENTE':
                # Gerente pode alterar, não precisa de senha antiga.
                pass

            # Caso 4: Usuário logado tentando mudar senha de outro sem permissão
            else:
                return False, "Acesso negado para alterar senha de outro usuário."

            # --- FIM DA LÓGICA DE PERMISSÃO ---

            # Cria o novo hash (MD5)
            new_hash = hashlib.md5(new_pass.encode("utf-8")).hexdigest()

            with self.uow_factory() as uow:
                # Salva no banco (o Trigger de log vai disparar)
                self.usuario_repo.update_password(uow, id_usuario_alvo, new_hash)
                uow.commit()
            return True, "Senha alterada com sucesso."
        except Exception as e:
            return False, f"Erro ao alterar senha: {e}"

    # ------------------------------------------------------------------
    ## ⚙️ MÉTODOS DE PROCEDURES
    # ------------------------------------------------------------------
    def get_client_score(self, id_cliente: int) -> Tuple[bool, Union[int, str]]:
        """Calcula e retorna o score de crédito do cliente."""
        try:
            with self.uow_factory() as uow:
                # A procedure atualiza o score no banco E retorna o valor
                score = self.usuario_repo.call_proc_calcular_score(uow, id_cliente)
                uow.commit()  # Commit para salvar o score atualizado no banco
            return True, score
        except Exception as e:
            return False, f"Erro ao calcular score: {e}"

    def get_employee_performance(self, id_funcionario: int) -> Tuple[bool, Union[Dict[str, Any], str]]:
        """Busca o relatório de desempenho do funcionário."""
        try:
            # É uma consulta read-only, não precisa de UoW
            data = self.usuario_repo.call_proc_desempenho_func(id_funcionario)
            return True, data
        except Exception as e:
            return False, f"Erro ao buscar desempenho: {e}"