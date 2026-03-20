"""
Implementação da Interface Gráfica (GUI) com CustomTkinter.
Versão 2 (v4.0 do Projeto) - Implementa todos os requisitos avançados
de consulta, alteração, procedures e views.
"""
import customtkinter as ctk
from tkinter import messagebox, simpledialog
from decimal import Decimal, InvalidOperation
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable, Union

# Importa os SERVIÇOS (Casos de Uso)
from src.core.use_cases.auth_service import AuthService
from src.core.use_cases.conta_service import ContaService
# Importa as Entidades
from src.core.entities.usuario import Usuario
from src.core.entities.conta import Conta, Transacao, CaixinhaInvestimento
# Importa Helpers
from src.infrastructure.utils.cpf_utils import format_cpf, only_digits

# --- Definição de Cores ---
COR_FUNDO = "#242424"
COR_FUNDO_FRAME = "#2D2D2D"
COR_FUNDO_FORM = "#343638"
COR_TEXTO_BRANCO = "#FFFFFF"
COR_TEXTO_CINZA = "#AAAAAA"
COR_TEXTO_TITULO = "#00BFFF"
COR_BOTAO_AZUL = "#1F6AA5"
COR_BOTAO_VERDE = "#2DBC7B"
COR_BOTAO_LARANJA = "#F39C12"
COR_BOTAO_AZUL_CLARO = "#3498DB"
COR_BOTAO_ROXO = "#8E44AD"
COR_TEXTO_VERDE = "#2DBC7B"
COR_TEXTO_VERMELHO = "#E74C3C"
COR_BOTAO_VERDE_HOVER = "#28A46C"
COR_BOTAO_LARANJA_HOVER = "#D1800B"


# --- CLASSE DE DIÁLOGO (Investimento) ---
class SourceAccountDialog(ctk.CTkToplevel):
    def __init__(self, parent, source_accounts):
        super().__init__(parent)
        self.title("Selecionar Conta de Origem")
        self.geometry("350x180")
        self.result = None
        self.source_accounts = source_accounts
        self.label = ctk.CTkLabel(self, text="De qual conta deseja investir?", font=ctk.CTkFont(size=14))
        self.label.pack(pady=15, padx=15)
        account_names = list(self.source_accounts.keys())
        self.option_var = ctk.StringVar(value=account_names[0])
        self.option_menu = ctk.CTkOptionMenu(
            self, variable=self.option_var, values=account_names,
            font=ctk.CTkFont(size=14), height=40
        )
        self.option_menu.pack(pady=10, padx=20, fill="x")
        self.ok_button = ctk.CTkButton(
            self, text="Confirmar", command=self.on_ok,
            height=40, font=ctk.CTkFont(size=14, weight="bold")
        )
        self.ok_button.pack(pady=15, padx=20, fill="x")
        self.transient(parent)
        self.grab_set()
        self.wait_window()

    def on_ok(self):
        self.result = self.source_accounts[self.option_var.get()]
        self.destroy()

    def get_choice(self):
        return self.result

# --- CLASSE DE DIÁLOGO (Redefinir Senha) ---
class ResetPasswordDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Redefinir Senha")
        self.geometry("350x380")
        self.transient(parent)
        self.grab_set()

        self.result = None

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Campos
        self.entries = {}

        ctk.CTkLabel(frame, text="CPF:", anchor="w").pack(fill="x", pady=(10, 0))
        self.entries['cpf'] = ctk.CTkEntry(frame, height=35)
        self.entries['cpf'].pack(fill="x", pady=(5, 10))

        ctk.CTkLabel(frame, text="Data Nasc. (AAAA-MM-DD):", anchor="w").pack(fill="x", pady=(10, 0))
        self.entries['data_nasc'] = ctk.CTkEntry(frame, height=35)
        self.entries['data_nasc'].pack(fill="x", pady=(5, 10))

        ctk.CTkLabel(frame, text="Nova Senha:", anchor="w").pack(fill="x", pady=(10, 0))
        self.entries['new_pass'] = ctk.CTkEntry(frame, height=35, show="*")
        self.entries['new_pass'].pack(fill="x", pady=(5, 10))

        ctk.CTkLabel(frame, text="Confirmar Nova Senha:", anchor="w").pack(fill="x", pady=(10, 0))
        self.entries['confirm_pass'] = ctk.CTkEntry(frame, height=35, show="*")
        self.entries['confirm_pass'].pack(fill="x", pady=(5, 20))

        ctk.CTkButton(frame, text="REDEFINIR", command=self.on_reset, height=40, fg_color=COR_BOTAO_LARANJA).pack(fill="x", pady=10)

        self.wait_window()

    def on_reset(self):
        cpf = self.entries['cpf'].get()
        data_nasc = self.entries['data_nasc'].get()
        new_pass = self.entries['new_pass'].get()
        confirm_pass = self.entries['confirm_pass'].get()

        if new_pass != confirm_pass:
            messagebox.showerror("Erro", "As novas senhas não coincidem.", parent=self)
            return

        if not all([cpf, data_nasc, new_pass]):
            messagebox.showwarning("Aviso", "Preencha todos os campos.", parent=self)
            return

        self.result = {'cpf': cpf, 'data_nasc': data_nasc, 'new_pass': new_pass}
        self.destroy()

# ---
# --- NOVAS CLASSES DE DIÁLOGO (Para Alterações)
# ---

class EditClientDialog(ctk.CTkToplevel):
    """Pop-up para funcionário alterar dados de um Cliente."""
    def __init__(self, parent, app_instance, client_data: Dict[str, Any]):
        super().__init__(parent)
        self.app = app_instance
        self.client_data = client_data
        self.id_usuario = client_data.get('id_usuario')

        self.title(f"Alterar Cliente: {client_data.get('nome')}")
        self.geometry("450x450")
        self.configure(fg_color=COR_FUNDO_FRAME)

        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.entries: Dict[str, ctk.CTkEntry] = {}

        # Campos Editáveis
        self._add_entry("telefone", "Telefone", client_data.get('telefone'))
        self._add_entry("endereco", "Endereço", client_data.get('endereco'))

        # Alteração de Senha
        ctk.CTkLabel(self.main_frame, text="Nova Senha (Opcional)", anchor="w", font=ctk.CTkFont(size=12, weight="bold")).pack(fill="x", padx=10, pady=(15, 0))
        self._add_entry("new_password", "Nova Senha", "", show="*")

        # Botão de Salvar
        self.btn_save = ctk.CTkButton(
            self.main_frame, text="Salvar Alterações",
            command=self.do_save_changes,
            height=40, font=ctk.CTkFont(size=14, weight="bold")
        )
        self.btn_save.pack(pady=20, padx=10, fill="x")

        self.transient(parent)
        self.grab_set()

    def _add_entry(self, key: str, label: str, default_value: str, show: str = ""):
        ctk.CTkLabel(self.main_frame, text=label, anchor="w", font=ctk.CTkFont(size=12)).pack(fill="x", padx=10, pady=(10, 0))
        entry = ctk.CTkEntry(self.main_frame, height=35)
        entry.pack(fill="x", padx=10, pady=5)
        if default_value:
            entry.insert(0, default_value)
        if show:
            entry.configure(show=show)
        self.entries[key] = entry

    def do_save_changes(self):
        if not self.id_usuario:
            messagebox.showerror("Erro", "ID do usuário não encontrado.", parent=self)
            return

        # 1. Atualizar Detalhes
        details_user = {
            'telefone': self.entries['telefone'].get(),
            'endereco': self.entries['endereco'].get()
        }
        ok, msg = self.app.auth_service.update_client_details(self.id_usuario, details_user)

        if not ok:
            messagebox.showerror("Erro ao Salvar Dados", msg, parent=self)
            return

        # 2. Atualizar Senha (se preenchida)
        new_pass = self.entries['new_password'].get()
        if new_pass:
            # Gerente altera sem senha antiga
            ok_pass, msg_pass = self.app.auth_service.change_password(
                id_usuario_alvo=self.id_usuario,
                old_pass="",
                new_pass=new_pass,
                logged_in_user=self.app.user_entity
            )
            if not ok_pass:
                messagebox.showerror("Erro ao Alterar Senha", msg_pass, parent=self)
                return

        messagebox.showinfo("Sucesso", "Dados do cliente atualizados.", parent=self)
        self.destroy()

class EditAccountDialog(ctk.CTkToplevel):
    """Pop-up para funcionário alterar dados de uma Conta."""
    def __init__(self, parent, app_instance, conta: Conta):
        super().__init__(parent)
        self.app = app_instance
        self.conta = conta

        self.title(f"Alterar Conta: {conta.numero_conta}")
        self.geometry("450x500")
        self.configure(fg_color=COR_FUNDO_FRAME)

        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.entries: Dict[str, ctk.CTkEntry] = {}
        self.option_vars: Dict[str, ctk.StringVar] = {}

        # Mostra campos dinâmicos baseados no tipo de conta
        if self.conta.tipo_conta == 'CC':
            self._add_entry("limite_cc", "Limite CC (R$)", f"{conta.limite_cc or '0.00'}")
            self._add_entry("taxa_manutencao", "Taxa Manutenção (R$)", f"{conta.taxa_manutencao or '0.00'}")
            self._add_entry("data_vencimento_taxa", "Dia Venc. Taxa", f"{conta.data_vencimento_taxa or 5}")

        elif self.conta.tipo_conta == 'CP':
            self._add_entry("taxa_rendimento", "Taxa Rend. (Ex: 0.0050)", f"{conta.taxa_rendimento or '0.0050'}")

        elif self.conta.tipo_conta == 'CI':
            self.option_vars['perfil_risco'] = ctk.StringVar(value=conta.perfil_risco)
            ctk.CTkLabel(self.main_frame, text="Perfil de Risco", anchor="w", font=ctk.CTkFont(size=12)).pack(fill="x", padx=10, pady=(10, 0))
            menu_ci = ctk.CTkOptionMenu(
                self.main_frame,
                variable=self.option_vars['perfil_risco'],
                values=["BAIXO", "MEDIO", "ALTO"]
            )
            menu_ci.pack(fill="x", padx=10, pady=5)
        else:
              ctk.CTkLabel(self.main_frame, text="Nenhum campo editável para este tipo de conta.").pack(pady=20)

        # Botão de Salvar
        self.btn_save = ctk.CTkButton(
            self.main_frame, text="Salvar Alterações",
            command=self.do_save_changes,
            height=40, font=ctk.CTkFont(size=14, weight="bold")
        )
        self.btn_save.pack(pady=20, padx=10, fill="x")

        self.transient(parent)
        self.grab_set()

    def _add_entry(self, key: str, label: str, default_value: str):
        ctk.CTkLabel(self.main_frame, text=label, anchor="w", font=ctk.CTkFont(size=12)).pack(fill="x", padx=10, pady=(10, 0))
        entry = ctk.CTkEntry(self.main_frame, height=35)
        entry.pack(fill="x", padx=10, pady=5)
        if default_value:
            entry.insert(0, default_value)
        self.entries[key] = entry

    def do_save_changes(self):
        details = {}
        try:
            # Coleta dados baseados no tipo de conta
            if self.conta.tipo_conta == 'CC':
                details['limite_cc'] = Decimal(self.entries['limite_cc'].get())
                details['taxa_manutencao'] = Decimal(self.entries['taxa_manutencao'].get())
                details['data_vencimento_taxa'] = int(self.entries['data_vencimento_taxa'].get())
            elif self.conta.tipo_conta == 'CP':
                details['taxa_rendimento'] = Decimal(self.entries['taxa_rendimento'].get())
            elif self.conta.tipo_conta == 'CI':
                details['perfil_risco'] = self.option_vars['perfil_risco'].get()

            if not details:
                messagebox.showwarning("Aviso", "Nenhum campo para alterar.", parent=self)
                return

            # Chama o serviço (que tem a lógica de validação do score)
            ok, msg = self.app.conta_service.update_conta_details(
                id_conta=self.conta.id_conta,
                id_cliente=self.conta.id_cliente,
                details=details
            )

            if ok:
                messagebox.showinfo("Sucesso", msg, parent=self)
                self.destroy()
            else:
                messagebox.showerror("Erro na Alteração", msg, parent=self)

        except InvalidOperation:
            messagebox.showerror("Erro de Formato", "Valor inválido para um campo numérico (taxa, limite, etc.).", parent=self)
        except Exception as e:
            messagebox.showerror("Erro de Formulário", f"Erro ao processar dados: {e}", parent=self)


# --- CLASSE DA APLICAÇÃO PRINCIPAL ---
class App(ctk.CTk):

    def __init__(self, auth_service: AuthService, conta_service: ContaService):
        super().__init__()
        self.auth_service = auth_service
        self.conta_service = conta_service
        ctk.set_appearance_mode("Dark")
        self.configure(fg_color=COR_FUNDO)
        self.title("Banco Malvader")
        self.geometry("900x600")
        self.minsize(800, 500)

        # Estado da Aplicação
        self.user_entity: Optional[Usuario] = None
        self.accounts: List[Conta] = []
        self.active_account: Optional[Conta] = None

        # Mapas de UI
        self.display_name_map = {
            "CC": "Conta Corrente", "CP": "Poupança", "CI": "Investimento",
            "DEPOSITO": "Depósito", "SAQUE": "Saque", "TRANSFERENCIA": "Transferência",
            "RENDIMENTO_POUPANCA": "Rend. Poupança", "INVESTIR": "Investimento", "RESGATAR": "Resgate",
            "RENDIMENTO_CDI": "Rend. CDI", "RENDIMENTO_BOLSA": "Rend. Bolsa"
        }
        self.account_name_map = {
            "Conta Corrente": "CC", "Poupança": "CP", "Investimento": "CI"
        }

        # Frame principal que hospeda as telas
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True)

        # Dados em cache para consulta
        self.cached_client_data: Optional[Dict[str, Any]] = None
        self.cached_account_data: Optional[Conta] = None
        self.cached_employee_data: Optional[Dict[str, Any]] = None

        # Acessa o uow_factory (necessário para redefinição de senha e alteração de senha de funcionário)
        # Assumindo que auth_service tem acesso a ele.
        if hasattr(auth_service, 'uow_factory'):
            self.uow_factory = auth_service.uow_factory
        else:
             print("AVISO: AuthService não possui uow_factory. Redefinição de senha falhará.")
             self.uow_factory = lambda: None

        self.show_login_screen()

    # -----------------------------------------------------------------
    # 🔄 MÉTODOS DE NAVEGAÇÃO E UTILIDADE
    # -----------------------------------------------------------------

    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def format_currency(self, value: Decimal) -> str:
        if value is None: value = Decimal("0.0")
        # Correção para formato monetário brasileiro
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def get_display_name(self, tipo: str) -> str:
        return self.display_name_map.get(tipo, tipo)

    def show_login_screen(self):
        self.clear_frame()
        self.geometry("900x600")
        self.title("Banco Malvader - Login")

        ctk.CTkLabel(self.main_frame, text="BANCO MALVADER",
                     font=ctk.CTkFont(size=32, weight="bold"),
                     text_color=COR_TEXTO_TITULO
        ).pack(pady=(80, 10))
        ctk.CTkLabel(self.main_frame, text="Sistema Bancário Digital",
                     font=ctk.CTkFont(size=16), text_color=COR_TEXTO_CINZA
        ).pack(pady=(0, 40))

        login_frame = ctk.CTkFrame(self.main_frame, fg_color=COR_FUNDO_FRAME, corner_radius=16)
        login_frame.pack(padx=20, pady=20)

        ctk.CTkLabel(login_frame, text="Entrar na sua conta",
                     font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(30, 20), padx=100)

        ctk.CTkLabel(login_frame, text="CPF", font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA
        ).pack(anchor="w", padx=30, pady=(10, 0))
        self.login_cpf_entry = ctk.CTkEntry(
            login_frame, placeholder_text="Digite seu CPF",
            width=300, height=40, font=ctk.CTkFont(size=14), corner_radius=8
        )
        self.login_cpf_entry.pack(padx=30, pady=(5, 10))
        self.login_cpf_entry.focus()

        ctk.CTkLabel(login_frame, text="Senha", font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA
        ).pack(anchor="w", padx=30, pady=(10, 0))
        pw_frame = ctk.CTkFrame(login_frame, fg_color="transparent")
        pw_frame.pack(padx=30, pady=(5, 20))
        self.login_pw_entry = ctk.CTkEntry(
            pw_frame, placeholder_text="Digite sua senha",
            width=260, height=40, font=ctk.CTkFont(size=14), corner_radius=8, show="*"
        )
        self.login_pw_entry.pack(side="left", fill="x", expand=True)
        self.show_pw_button = ctk.CTkButton(
            pw_frame, text="👁️", width=30, height=40, command=self.toggle_password_visibility,
            fg_color="#4A4A4A", hover_color="#555555", corner_radius=8
        )
        self.show_pw_button.pack(side="right", padx=(5,0))

        ctk.CTkButton(
            login_frame, text="ENTRAR", command=self.do_login,
            width=300, height=40, font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=8, fg_color=COR_BOTAO_AZUL_CLARO, hover_color="#40A8E0"
        ).pack(padx=30, pady=(20, 10))

        # --- BOTÃO ALTERAR SENHA (USUÁRIO) ---
        ctk.CTkButton(
            login_frame, text="Alterar Senha", command=self.show_reset_password_dialog,
            width=300, height=40, font=ctk.CTkFont(size=14),
            fg_color="#555555", hover_color="#666666"
        ).pack(padx=30, pady=(5, 10))

        register_frame = ctk.CTkFrame(login_frame, fg_color="transparent")
        register_frame.pack(pady=(0, 10))
        ctk.CTkLabel(
            register_frame, text="Não tem uma conta?", font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA
        ).pack(side="left")
        ctk.CTkButton(
            register_frame, text="Cadastre-se", font=ctk.CTkFont(size=12, weight="bold", underline=True),
            fg_color="transparent", text_color=COR_BOTAO_AZUL_CLARO, hover_color=COR_FUNDO_FRAME,
            command=self.show_create_account_screen
        ).pack(side="left", padx=5)

    def toggle_password_visibility(self):
        current_show = self.login_pw_entry.cget("show")
        new_show = "" if current_show == "*" else "*"
        self.login_pw_entry.configure(show=new_show)
        self.show_pw_button.configure(text="🔒" if new_show == "*" else "🔓")

    def do_login(self):
        cpf = self.login_cpf_entry.get()
        senha = self.login_pw_entry.get()

        self.config(cursor="watch")
        self.update_idletasks()

        ok, user_or_msg = self.auth_service.login(cpf, senha)

        self.config(cursor="")

        if ok:
            # ✅ SUCESSO: user_or_msg deve ser o objeto Usuario.

            # --- VERIFICAÇÃO DE ROBUSTEZ ADICIONAL ---
            if not isinstance(user_or_msg, Usuario):
                # Se for True (ok) mas o objeto não for um Usuario
                error_msg = f"Erro interno: Objeto de usuário inválido. Tipo: {type(user_or_msg)}"
                self.user_entity = None
                messagebox.showerror("Erro de Login", error_msg, parent=self)
                return
            # -------------------------------------------------------------------------

            self.user_entity = user_or_msg

            # A linha que causava o erro agora é segura porque user_entity é garantidamente Usuario.
            if self.user_entity.tipo_usuario == 'CLIENTE':
                self.load_accounts()
                if self.accounts:
                    # Define a conta corrente como ativa por padrão, ou a primeira se não houver CC
                    self.active_account = next((acc for acc in self.accounts if acc.tipo_conta == 'CC'),
                                               self.accounts[0])
                    self.show_dashboard_screen()
                else:
                    messagebox.showerror("Erro de Conta", "Nenhuma conta ativa encontrada para este cliente.",
                                         parent=self)
                    self.logout()
            else:  # FUNCIONARIO, GERENTE
                self.show_employee_dashboard_screen()
        else:
            # 🛑 FALHA: user_or_msg é a mensagem de erro (string).
            self.user_entity = None
            messagebox.showerror("Erro de Login", user_or_msg, parent=self)

    # -----------------------------------------------------------------
    # 🔒 REDEFINIR SENHA (TELA DE LOGIN)
    # -----------------------------------------------------------------

    def show_reset_password_dialog(self):
        """Abre o diálogo de redefinição de senha e processa a requisição."""
        dialog = ResetPasswordDialog(self)
        reset_data = dialog.result

        if not reset_data:
            return

        cpf = only_digits(reset_data['cpf'])
        data_nasc_input = reset_data['data_nasc']
        new_pass = reset_data['new_pass']

        if len(new_pass) < 4:
            messagebox.showerror("Erro", "A nova senha deve ter pelo menos 4 caracteres.")
            return

        try:
            # 1. Validação de formato de Data de Nascimento (AAAA-MM-DD)
            datetime.strptime(data_nasc_input, "%Y-%m-%d")

            # 2. Busca o usuário para obter o ID e verificar a data de nascimento
            # Nota: Usamos o repositório diretamente (leitura)
            user_info = self.auth_service.usuario_repo.find_user_by_cpf_and_dob(cpf, data_nasc_input)

            if not user_info:
                messagebox.showerror("Erro", "CPF ou Data de Nascimento não conferem.", parent=self)
                return

            id_usuario_alvo = user_info.id_usuario

            # 3. Chama o serviço para alterar a senha
            self.config(cursor="watch"); self.update_idletasks()

            # logged_in_user=None, pois não há admin logado, apenas redefinição via dados cadastrais.
            ok_pass, msg_pass = self.auth_service.change_password(
                id_usuario_alvo=id_usuario_alvo,
                old_pass="",
                new_pass=new_pass,
                logged_in_user=None
            )
            self.config(cursor="")

            if ok_pass:
                messagebox.showinfo("Sucesso", "Senha redefinida com sucesso! Faça login.", parent=self)
            else:
                messagebox.showerror("Erro", msg_pass, parent=self)

        except ValueError:
            messagebox.showerror("Erro", "Data de Nascimento inválida. Use o formato AAAA-MM-DD.", parent=self)
        except AttributeError as e:
            # Captura o erro 'find_user_by_cpf_and_dob'
            messagebox.showerror("Erro de Repositório", f"O método {e.name} está faltando no repositório de usuários.")
        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Ocorreu um erro inesperado: {e}", parent=self)


    # -----------------------------------------------------------------
    # 👤 PAINEL DO CLIENTE (Dashboard e Operações)
    # -----------------------------------------------------------------

    def show_dashboard_screen(self):
        """Constrói o Dashboard principal (para CLIENTES)."""
        self.clear_frame()
        self.title("Banco Malvader - Dashboard Cliente")
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(10, 20))
        ctk.CTkLabel(header_frame, text="BANCO MALVADER",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=COR_TEXTO_TITULO
        ).pack(side="left")
        user_info_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        user_info_frame.pack(side="right", anchor="ne")

        if not self.user_entity:
            self.logout()
            return

        ctk.CTkLabel(user_info_frame, text=self.user_entity.nome,
                     font=ctk.CTkFont(size=16, weight="bold"), anchor="e"
        ).pack(anchor="e")
        ctk.CTkLabel(user_info_frame, text=f"Cliente • {format_cpf(self.user_entity.cpf)}",
                     font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA, anchor="e"
        ).pack(anchor="e")

        data_nasc_str = "Data não informada"
        if self.user_entity.data_nascimento:
            try:
                data_nasc_str = self.user_entity.data_nascimento.strftime("%d/%m/%Y")
            except (AttributeError, ValueError):
                data_nasc_str = str(self.user_entity.data_nascimento)

        ctk.CTkLabel(user_info_frame, text=f"Nasc: {data_nasc_str}",
                     font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA, anchor="e"
        ).pack(anchor="e", pady=(5,0))

        endereco_str = self.user_entity.endereco or "Endereço não informado"
        ctk.CTkLabel(user_info_frame, text=endereco_str,
                     font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA, anchor="e",
                     wraplength=250
        ).pack(anchor="e")

        ctk.CTkButton(
            user_info_frame, text="Sair", command=self.logout,
            font=ctk.CTkFont(size=12, underline=True), text_color=COR_TEXTO_VERMELHO,
            fg_color="transparent", hover_color=COR_FUNDO, width=30
        ).pack(anchor="e", pady=(5,0))

        self.balance_frame = ctk.CTkFrame(self.main_frame, fg_color=COR_FUNDO_FRAME, corner_radius=10)
        self.balance_frame.pack(fill="x", padx=20, pady=10)

        account_names = list(self.account_name_map.keys())
        user_account_types = [acc.tipo_conta for acc in self.accounts if acc.status == 'ATIVA']
        account_names_to_show = [name for name in account_names if self.account_name_map[name] in user_account_types]

        if len(account_names_to_show) > 1:
            self.account_switcher = ctk.CTkSegmentedButton(
                self.balance_frame,
                values=account_names_to_show,
                command=self.switch_active_account,
                font=ctk.CTkFont(size=14, weight="bold")
            )
            self.account_switcher.pack(pady=(20, 10), padx=30, fill="x")
            if self.active_account and self.active_account.status == 'ATIVA':
                self.account_switcher.set(self.get_display_name(self.active_account.tipo_conta))
            elif account_names_to_show:
                self.account_switcher.set(account_names_to_show[0])


        self.dashboard_balance_title_label = ctk.CTkLabel(self.balance_frame, text="Saldo Disponível",
                     font=ctk.CTkFont(size=14), text_color=COR_TEXTO_CINZA)
        self.dashboard_balance_title_label.pack(pady=(10, 0), padx=30, anchor="w")
        self.dashboard_balance_label = ctk.CTkLabel(
            self.balance_frame, text="R$ 0,00",
            font=ctk.CTkFont(size=40, weight="bold"), text_color=COR_TEXTO_VERDE
        )
        self.dashboard_balance_label.pack(pady=(0, 10), padx=30, anchor="w")
        self.dashboard_account_label = ctk.CTkLabel(
            self.balance_frame, text="Conta: 0000-000000",
            font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA
        )
        self.dashboard_account_label.pack(pady=(0, 20), padx=30, anchor="w")

        self.action_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        action_grid_frame = ctk.CTkFrame(self.action_frame, fg_color="transparent")
        action_grid_frame.pack(fill="both", expand=True)
        action_grid_frame.grid_columnconfigure((0, 1), weight=1)
        action_grid_frame.grid_rowconfigure((0, 1, 2), weight=1)

        btn_height = 80
        btn_font = ctk.CTkFont(size=18, weight="bold")

        ctk.CTkButton(action_grid_frame, text="💰 Depositar", command=self.show_deposito_screen,
            height=btn_height, font=btn_font, fg_color=COR_BOTAO_VERDE, hover_color=COR_BOTAO_VERDE_HOVER
        ).grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        ctk.CTkButton(action_grid_frame, text="💸 Sacar", command=self.show_saque_screen,
            height=btn_height, font=btn_font, fg_color=COR_BOTAO_LARANJA, hover_color=COR_BOTAO_LARANJA_HOVER
        ).grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        ctk.CTkButton(action_grid_frame, text="🔄 Transferir", command=self.show_transferencia_screen,
            height=btn_height, font=btn_font, fg_color=COR_BOTAO_AZUL_CLARO, hover_color="#2C81B0"
        ).grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        ctk.CTkButton(action_grid_frame, text="🧾 Extrato", command=self.show_extrato_screen,
            height=btn_height, font=btn_font, fg_color=COR_BOTAO_AZUL_CLARO, hover_color="#2C81B0"
        ).grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        self.btn_rendimento = ctk.CTkButton(
            action_grid_frame, text="✨ Aplicar Rendimento (Poupança)",
            command=self.do_aplicar_rendimento_poupanca,
            height=btn_height, font=btn_font,
            fg_color=COR_BOTAO_ROXO, hover_color="#7B249C"
        )
        self.btn_rendimento.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.investment_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        self.action_frame.pack(fill="x", padx=20, pady=10)
        self.investment_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.update_dashboard_display()
        self.update_dashboard_layout()

    def switch_active_account(self, selected_name: str):
        """Muda a conta ativa com base na seleção do SegmentedButton."""
        selected_type = self.account_name_map.get(selected_name)
        if not selected_type: return

        for acc in self.accounts:
            if acc.tipo_conta == selected_type and acc.status == 'ATIVA':
                self.active_account = acc
                self.update_dashboard_display()
                self.update_dashboard_layout()
                return

    def update_dashboard_display(self):
        """Atualiza Saldo e Número da Conta na UI."""

        # VERIFICAÇÃO DE EXISTÊNCIA (CORREÇÃO DE TIMING)
        if not self.active_account or not hasattr(self, 'dashboard_balance_label') or not self.dashboard_balance_label.winfo_exists():
            return

        # CORREÇÃO: Usa saldo_total para CI, caso contrário, saldo normal.
        balance = self.active_account.saldo_total if self.active_account.tipo_conta == 'CI' else self.active_account.saldo
        account_num = self.active_account.numero_conta

        self.dashboard_balance_label.configure(text=self.format_currency(balance))
        self.dashboard_account_label.configure(text=f"Conta: {account_num} ({self.get_display_name(self.active_account.tipo_conta)})")

        if hasattr(self, 'account_switcher') and self.account_switcher.winfo_exists():
            self.account_switcher.set(self.get_display_name(self.active_account.tipo_conta))

    def update_dashboard_layout(self):
        """Atualiza a visibilidade do botão de rendimento e caixinhas."""

        # VERIFICAÇÃO DE EXISTÊNCIA (CORREÇÃO DE TIMING)
        if not self.active_account or not hasattr(self, 'action_frame') or not self.action_frame.winfo_exists():
            return

        # 1. Botão de Rendimento da Poupança
        if hasattr(self, 'btn_rendimento') and self.btn_rendimento.winfo_exists():
            if self.active_account.tipo_conta == 'CP':
                self.btn_rendimento.grid()
            else:
                self.btn_rendimento.grid_remove()

        # 2. Caixinhas de Investimento (Apenas para Conta Investimento - CI)
        for widget in self.investment_frame.winfo_children():
            widget.destroy()

        if self.active_account.tipo_conta == 'CI':
            # 2.1. Oculta os botões de transação principal para CI
            self.action_frame.pack_forget()

            ctk.CTkLabel(self.investment_frame, text="Caixinhas de Investimento",
                         font=ctk.CTkFont(size=18, weight="bold"),
                         text_color=COR_TEXTO_TITULO
            ).pack(pady=(10, 10))

            ok, caixinhas = self.conta_service.get_caixinhas_investimento(self.active_account.id_conta)

            if ok and caixinhas:
                for caixinha in caixinhas:
                    self._render_caixinha_widget(caixinha)
            else:
                ctk.CTkLabel(self.investment_frame, text="Nenhuma caixinha de investimento disponível.",
                             text_color=COR_TEXTO_CINZA).pack(pady=20)

            self.investment_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        else:
            # 2.2. Mostra os botões de transação principal para CC/CP
            self.investment_frame.pack_forget()
            self.action_frame.pack(fill="both", expand=True, padx=20, pady=10)

    def _render_caixinha_widget(self, caixinha: CaixinhaInvestimento):
        """Renderiza um card para uma caixinha de investimento."""
        card_frame = ctk.CTkFrame(self.investment_frame, fg_color=COR_FUNDO_FORM, corner_radius=10)
        card_frame.pack(fill="x", padx=10, pady=8)

        # Info Column
        info_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        info_frame.pack(side="left", padx=10, pady=10, fill="y")

        # CORREÇÃO: Usa tipo_investimento, conforme a entidade
        ctk.CTkLabel(info_frame, text=f"Caixinha: {caixinha.tipo_investimento}",
                     font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")

        ctk.CTkLabel(info_frame, text=f"Tipo: {caixinha.tipo_investimento}",
                     font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkLabel(info_frame, text=f"Saldo: {self.format_currency(caixinha.saldo)}",
                     font=ctk.CTkFont(size=16, weight="bold"), text_color=COR_TEXTO_VERDE
        ).pack(anchor="w", pady=(5, 0))

        # Buttons Column
        button_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        button_frame.pack(side="right", padx=10, pady=10)

        ctk.CTkButton(button_frame, text="➕ Investir", command=lambda c=caixinha: self.do_investir(c),
                      height=30, fg_color=COR_BOTAO_VERDE, hover_color=COR_BOTAO_VERDE_HOVER,
                      font=ctk.CTkFont(size=12, weight="bold")
        ).pack(pady=3, fill="x")

        ctk.CTkButton(button_frame, text="↩️ Resgatar", command=lambda c=caixinha: self.do_resgatar(c),
                      height=30, fg_color=COR_BOTAO_LARANJA, hover_color=COR_BOTAO_LARANJA_HOVER,
                      font=ctk.CTkFont(size=12, weight="bold")
        ).pack(pady=3, fill="x")

        ctk.CTkButton(button_frame, text="✨ Rendimento", command=lambda c=caixinha: self.do_aplicar_rendimento_investimento(c),
                      height=30, fg_color=COR_BOTAO_ROXO, hover_color="#7B249C",
                      font=ctk.CTkFont(size=12, weight="bold")
        ).pack(pady=3, fill="x")

    # -----------------------------------------------------------------
    # 🛠️ PAINEL DO FUNCIONÁRIO (Menu Principal e Telas)
    # -----------------------------------------------------------------

    def show_employee_dashboard_screen(self):
        """Constrói o Dashboard principal (para FUNCIONÁRIOS)."""
        self.clear_frame()
        self.title("Banco Malvader - Painel Funcionário")

        if not self.user_entity:
            self.logout()
            return

        # --- Frame do Cabeçalho ---
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(10, 5))

        ctk.CTkLabel(header_frame, text="PAINEL DO FUNCIONÁRIO",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=COR_TEXTO_TITULO
        ).pack(side="left")

        user_info_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        user_info_frame.pack(side="right", anchor="ne")

        ctk.CTkLabel(user_info_frame, text=self.user_entity.nome,
                     font=ctk.CTkFont(size=16, weight="bold"), anchor="e"
        ).pack(anchor="e")

        cargo_str = self.user_entity.cargo or "Funcionário"
        ctk.CTkLabel(user_info_frame, text=f"{cargo_str} • {format_cpf(self.user_entity.cpf)}",
                     font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA, anchor="e"
        ).pack(anchor="e")

        if self.user_entity.salario:
            salario_str = self.format_currency(self.user_entity.salario)
            ctk.CTkLabel(user_info_frame, text=f"Salário: {salario_str}",
                         font=ctk.CTkFont(size=12, weight="bold"), text_color=COR_TEXTO_VERDE, anchor="e"
            ).pack(anchor="e", pady=(0,0))

        ctk.CTkButton(
            user_info_frame, text="Sair", command=self.logout,
            font=ctk.CTkFont(size=12, underline=True), text_color=COR_TEXTO_VERMELHO,
            fg_color="transparent", hover_color=COR_FUNDO, width=30
        ).pack(anchor="e", pady=(5,0))

        # --- Sistema de Abas ---
        self.tab_view = ctk.CTkTabview(self.main_frame, fg_color=COR_FUNDO_FRAME)
        self.tab_view.pack(fill="both", expand=True, padx=20, pady=10)

        self.tab_view.add("Consultas")
        self.tab_view.add("Cadastros")
        self.tab_view.add("Alterações e Operações")
        self.tab_view.add("Relatórios")

        self.tab_view.set("Consultas") # Aba padrão

        self._create_tab_consultas(self.tab_view.tab("Consultas"))
        self._create_tab_cadastros(self.tab_view.tab("Cadastros"))
        self._create_tab_alteracoes(self.tab_view.tab("Alterações e Operações"))
        self._create_tab_relatorios(self.tab_view.tab("Relatórios"))

    def _create_tab_consultas(self, tab):
        """Cria os botões da aba de Consultas."""
        tab.grid_columnconfigure(0, weight=1)
        btn_font = ctk.CTkFont(size=16, weight="bold")

        ctk.CTkLabel(tab, text="Consultar Dados (usando Views)", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)

        ctk.CTkButton(
            tab, text="🔍 Consultar Cliente",
            command=self.show_consulta_cliente_screen,
            height=50, font=btn_font, fg_color=COR_BOTAO_AZUL_CLARO, hover_color="#2C81B0"
        ).pack(fill="x", padx=30, pady=10)

        ctk.CTkButton(
            tab, text="💳 Consultar Conta",
            command=self.show_consulta_conta_screen,
            height=50, font=btn_font, fg_color=COR_BOTAO_AZUL_CLARO, hover_color="#2C81B0"
        ).pack(fill="x", padx=30, pady=10)

        ctk.CTkButton(
            tab, text="👔 Consultar Funcionário",
            command=self.show_consulta_funcionario_screen,
            height=50, font=btn_font, fg_color=COR_BOTAO_AZUL_CLARO, hover_color="#2C81B0"
        ).pack(fill="x", padx=30, pady=10)

    def _create_tab_cadastros(self, tab):
        """Cria os botões da aba de Cadastros."""
        tab.grid_columnconfigure(0, weight=1)
        btn_font = ctk.CTkFont(size=16, weight="bold")

        ctk.CTkLabel(tab, text="Gerenciamento de Contas", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)

        ctk.CTkButton(
            tab, text="🏦 Abrir Conta para Novo Cliente",
            command=self.show_employee_create_client_screen,
            height=50, font=btn_font, fg_color=COR_BOTAO_VERDE, hover_color=COR_BOTAO_VERDE_HOVER
        ).pack(fill="x", padx=30, pady=10)

        ctk.CTkButton(
            tab, text="👤 Cadastrar Novo Funcionário",
            command=self.show_register_employee_screen,
            height=50, font=btn_font, fg_color=COR_BOTAO_AZUL_CLARO, hover_color="#2C81B0"
        ).pack(fill="x", padx=30, pady=10)

    def _create_tab_alteracoes(self, tab):
        """Cria os botões da aba de Alterações e Operações."""
        tab.grid_columnconfigure(0, weight=1)
        btn_font = ctk.CTkFont(size=16, weight="bold")

        ctk.CTkLabel(tab, text="Alterações Manuais e Operações Críticas", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)

        # A lógica será: 1. Consultar, 2. Clicar em Alterar.
        ctk.CTkLabel(tab, text="Para alterar dados, use as telas da aba 'Consultas'\ne clique no botão 'Alterar' desejado.",
                     font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA).pack(pady=10)

        ctk.CTkButton(
            tab, text="❌ Encerrar Conta de Cliente",
            command=self.show_encerrar_conta_dialog,
            height=50, font=btn_font, fg_color=COR_BOTAO_LARANJA, hover_color=COR_BOTAO_LARANJA_HOVER
        ).pack(fill="x", padx=30, pady=20)

    def _create_tab_relatorios(self, tab):
        """Cria os botões da aba de Relatórios."""
        tab.grid_columnconfigure(0, weight=1)
        btn_font = ctk.CTkFont(size=16, weight="bold")

        ctk.CTkLabel(tab, text="Relatórios Gerenciais", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)

        ctk.CTkButton(
            tab, text="📊 Relatório de Movimentações",
            command=self.show_relatorio_movimentacoes_screen,
            height=50, font=btn_font, fg_color=COR_FUNDO_FORM, hover_color="#444444"
        ).pack(fill="x", padx=30, pady=10)

        ctk.CTkButton(
            tab, text="📉 Relatório de Inadimplentes",
            command=self.show_relatorio_inadimplentes_screen,
            height=50, font=btn_font, fg_color=COR_FUNDO_FORM, hover_color="#444444"
        ).pack(fill="x", padx=30, pady=10)

        ctk.CTkLabel(tab, text="O Relatório de Desempenho de Funcionário\nestá disponível na aba 'Consultas' -> 'Consultar Funcionário'.",
                     font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA).pack(pady=20)

    # -----------------------------------------------------------------
    # 👤 MÉTODOS DE CADASTRO (Público e Funcionário)
    # -----------------------------------------------------------------

    def show_create_account_screen(self):
        """Tela de cadastro PÚBLICA (para o próprio cliente se cadastrar)."""
        self.clear_frame()
        self.title("Banco Malvader - Criar Nova Conta")

        ctk.CTkLabel(self.main_frame, text="Criar Nova Conta",
                     font=ctk.CTkFont(size=32, weight="bold"),
                     text_color=COR_TEXTO_TITULO
        ).pack(pady=(40, 30))
        form_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color=COR_FUNDO_FRAME, corner_radius=16)
        form_frame.pack(padx=20, pady=20, fill="both", expand=True)

        ctk.CTkLabel(form_frame, text="Nome Completo", font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA
        ).pack(anchor="w", padx=30, pady=(20, 0))
        self.reg_nome_entry = ctk.CTkEntry(form_frame, width=350, height=40)
        self.reg_nome_entry.pack(padx=30, pady=(5, 10))

        ctk.CTkLabel(form_frame, text="CPF", font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA
        ).pack(anchor="w", padx=30, pady=(10, 0))
        self.reg_cpf_entry = ctk.CTkEntry(form_frame, width=350, height=40)
        self.reg_cpf_entry.pack(padx=30, pady=(5, 10))

        ctk.CTkLabel(form_frame, text="Senha", font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA
        ).pack(anchor="w", padx=30, pady=(10, 0))
        self.reg_pw_entry = ctk.CTkEntry(form_frame, width=350, height=40, show="*")
        self.reg_pw_entry.pack(padx=30, pady=(5, 10))

        ctk.CTkLabel(form_frame, text="Confirmar Senha",
                     font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA
        ).pack(anchor="w", padx=30, pady=(10, 0))
        self.reg_pw_confirm_entry = ctk.CTkEntry(form_frame, width=350, height=40, show="*")
        self.reg_pw_confirm_entry.pack(padx=30, pady=(5, 10))

        ctk.CTkLabel(form_frame, text="Data de Nascimento (AAAA-MM-DD)", font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA
        ).pack(anchor="w", padx=30, pady=(10, 0))
        self.reg_data_nasc_entry = ctk.CTkEntry(form_frame, width=350, height=40)
        self.reg_data_nasc_entry.pack(padx=30, pady=(5, 10))

        ctk.CTkLabel(form_frame, text="Endereço (Rua, N°, Bairro)", font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA
        ).pack(anchor="w", padx=30, pady=(10, 0))
        self.reg_endereco_entry = ctk.CTkEntry(form_frame, width=350, height=40)
        self.reg_endereco_entry.pack(padx=30, pady=(5, 10))

        ctk.CTkLabel(form_frame, text="Telefone (Ex: 11987654321)", font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA
        ).pack(anchor="w", padx=30, pady=(10, 0))
        self.reg_telefone_entry = ctk.CTkEntry(form_frame, width=350, height=40)
        self.reg_telefone_entry.pack(padx=30, pady=(5, 20))

        btn_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_frame.pack(padx=30, pady=30, fill="x", expand=True)
        ctk.CTkButton(
            btn_frame, text="CADASTRAR", command=self.do_register_user,
            height=40, font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COR_BOTAO_AZUL_CLARO, hover_color="#40A8E0"
        ).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(
            btn_frame, text="VOLTAR", command=self.show_login_screen,
            height=40, font=ctk.CTkFont(size=14),
            fg_color="#555555", hover_color="#666666"
        ).pack(side="right", fill="x", expand=True, padx=(5, 0))

    def do_register_user(self):
        """Handler para a tela de cadastro PÚBLICA."""
        nome = self.reg_nome_entry.get()
        cpf = self.reg_cpf_entry.get()
        pw1 = self.reg_pw_entry.get()
        pw2 = self.reg_pw_confirm_entry.get()
        data_nasc = self.reg_data_nasc_entry.get()
        endereco = self.reg_endereco_entry.get()
        telefone = self.reg_telefone_entry.get()

        if not all([nome, cpf, pw1, pw2, data_nasc, endereco, telefone]):
            messagebox.showwarning("Campos Vazios", "Por favor, preencha todos os campos.", parent=self)
            return
        if pw1 != pw2:
            messagebox.showerror("Senhas Diferentes", "As senhas não coincidem.", parent=self)
            return

        try:
            datetime.strptime(data_nasc, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Data Inválida", "Formato de Data de Nascimento inválido. Use AAAA-MM-DD.", parent=self)
            return

        try:
            self.config(cursor="watch"); self.update_idletasks()
            ok, msg = self.auth_service.register_client(nome, cpf, pw1, data_nasc, endereco, telefone)
            self.config(cursor="")

            if ok:
                messagebox.showinfo("Sucesso!", msg, parent=self)
                self.show_login_screen()
            else:
                messagebox.showerror("Erro no Cadastro", msg, parent=self)
        except Exception as e:
            self.config(cursor="")
            messagebox.showerror("Erro Crítico", f"Ocorreu um erro inesperado: {e}", parent=self)

    # -----------------------------------------------------------------
    # 🛠️ MÉTODOS DO PAINEL DE FUNCIONÁRIO (Cadastros)
    # -----------------------------------------------------------------

    def show_employee_create_client_screen(self):
        """Tela de cadastro de CLIENTE (acessada pelo funcionário logado)."""
        self.clear_frame()
        self.title("Banco Malvader - Abrir Conta para Cliente")

        ctk.CTkButton(
            self.main_frame, text="← Voltar", command=self.show_employee_dashboard_screen,
            fg_color="transparent", text_color=COR_BOTAO_AZUL_CLARO,
            hover_color=COR_FUNDO, font=ctk.CTkFont(size=14)
        ).pack(anchor="w", padx=20, pady=(10, 0))

        ctk.CTkLabel(self.main_frame, text="Abrir Contas para Novo Cliente",
                     font=ctk.CTkFont(size=32, weight="bold"),
                     text_color=COR_TEXTO_TITULO
        ).pack(pady=(10, 30))

        form_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color=COR_FUNDO_FRAME, corner_radius=16)
        form_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # --- CAMPOS DO NOVO CLIENTE ---
        ctk.CTkLabel(form_frame, text="Nome Completo", font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA
        ).pack(anchor="w", padx=30, pady=(20, 0))
        self.emp_reg_nome_entry = ctk.CTkEntry(form_frame, width=350, height=40)
        self.emp_reg_nome_entry.pack(padx=30, pady=(5, 10))

        ctk.CTkLabel(form_frame, text="CPF", font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA
        ).pack(anchor="w", padx=30, pady=(10, 0))
        self.emp_reg_cpf_entry = ctk.CTkEntry(form_frame, width=350, height=40)
        self.emp_reg_cpf_entry.pack(padx=30, pady=(5, 10))

        ctk.CTkLabel(form_frame, text="Senha (Provisória)", font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA
        ).pack(anchor="w", padx=30, pady=(10, 0))
        self.emp_reg_pw_entry = ctk.CTkEntry(form_frame, width=350, height=40, show="*")
        self.emp_reg_pw_entry.pack(padx=30, pady=(5, 10))

        ctk.CTkLabel(form_frame, text="Confirmar Senha",
                     font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA
        ).pack(anchor="w", padx=30, pady=(10, 0))
        self.emp_reg_pw_confirm_entry = ctk.CTkEntry(form_frame, width=350, height=40, show="*")
        self.emp_reg_pw_confirm_entry.pack(padx=30, pady=(5, 10))

        ctk.CTkLabel(form_frame, text="Data de Nascimento (AAAA-MM-DD)", font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA
        ).pack(anchor="w", padx=30, pady=(10, 0))
        self.emp_reg_data_nasc_entry = ctk.CTkEntry(form_frame, width=350, height=40)
        self.emp_reg_data_nasc_entry.pack(padx=30, pady=(5, 10))

        ctk.CTkLabel(form_frame, text="Endereço (Rua, N°, Bairro)", font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA
        ).pack(anchor="w", padx=30, pady=(10, 0))
        self.emp_reg_endereco_entry = ctk.CTkEntry(form_frame, width=350, height=40)
        self.emp_reg_endereco_entry.pack(padx=30, pady=(5, 10))

        ctk.CTkLabel(form_frame, text="Telefone (Ex: 11987654321)", font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA
        ).pack(anchor="w", padx=30, pady=(10, 0))
        self.emp_reg_telefone_entry = ctk.CTkEntry(form_frame, width=350, height=40)
        self.emp_reg_telefone_entry.pack(padx=30, pady=(5, 20))

        btn_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_frame.pack(padx=30, pady=(20, 30), fill="x", expand=True)
        ctk.CTkButton(
            btn_frame, text="CADASTRAR CLIENTE E ABRIR CONTAS", command=self.do_register_user_by_employee,
            height=40, font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COR_BOTAO_VERDE, hover_color=COR_BOTAO_VERDE_HOVER
        ).pack(fill="x")

    def do_register_user_by_employee(self):
        """Handler para a tela de cadastro INTERNA (do funcionário)."""
        nome = self.emp_reg_nome_entry.get()
        cpf = self.emp_reg_cpf_entry.get()
        pw1 = self.emp_reg_pw_entry.get()
        pw2 = self.emp_reg_pw_confirm_entry.get()
        data_nasc = self.emp_reg_data_nasc_entry.get()
        endereco = self.emp_reg_endereco_entry.get()
        telefone = self.emp_reg_telefone_entry.get()

        if not all([nome, cpf, pw1, pw2, data_nasc, endereco, telefone]):
            messagebox.showwarning("Campos Vazios", "Por favor, preencha todos os campos.", parent=self)
            return
        if pw1 != pw2:
            messagebox.showerror("Senhas Diferentes", "As senhas não coincidem.", parent=self)
            return

        try:
            datetime.strptime(data_nasc, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Data Inválida", "Formato de Data de Nascimento inválido. Use AAAA-MM-DD.", parent=self)
            return

        try:
            self.config(cursor="watch"); self.update_idletasks()
            # Usa o mesmo serviço de registro de cliente
            ok, msg = self.auth_service.register_client(nome, cpf, pw1, data_nasc, endereco, telefone)
            self.config(cursor="")

            if ok:
                messagebox.showinfo("Sucesso!", msg, parent=self)
                self.show_employee_dashboard_screen() # Volta pro painel
            else:
                messagebox.showerror("Erro no Cadastro", msg, parent=self)
        except Exception as e:
            self.config(cursor="")
            messagebox.showerror("Erro Crítico", f"Ocorreu um erro inesperado: {e}", parent=self)

    def show_register_employee_screen(self):
        """Tela de cadastro de FUNCIONÁRIO (acessada pelo funcionário logado)."""
        self.clear_frame()
        self.title("Banco Malvader - Cadastrar Novo Funcionário")

        ctk.CTkButton(
            self.main_frame, text="← Voltar", command=self.show_employee_dashboard_screen,
            fg_color="transparent", text_color=COR_BOTAO_AZUL_CLARO,
            hover_color=COR_FUNDO, font=ctk.CTkFont(size=14)
        ).pack(anchor="w", padx=20, pady=(10, 0))
        ctk.CTkLabel(self.main_frame, text="Cadastrar Novo Funcionário",
                     font=ctk.CTkFont(size=32, weight="bold"),
                     text_color=COR_TEXTO_TITULO
        ).pack(pady=(10, 30))
        scroll_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color=COR_FUNDO_FRAME, corner_radius=16)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
        form_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        form_frame.pack(padx=30, pady=20)

        labels = ["Nome Completo", "CPF", "Data de Nascimento (AAAA-MM-DD)", "Telefone", "Endereço", "Salário (Ex: 3500.00)", "Senha", "Confirmar Senha"]
        self.emp_reg_entries = {}
        row_idx = 0
        for label_text in labels:
            ctk.CTkLabel(form_frame, text=label_text, font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA
            ).grid(row=row_idx, column=0, columnspan=2, sticky="w", pady=(10, 0))
            row_idx += 1
            show_char = "*" if "Senha" in label_text else ""
            entry = ctk.CTkEntry(
                form_frame, width=350, height=40,
                corner_radius=8, show=show_char, font=ctk.CTkFont(size=14)
            )
            entry.grid(row=row_idx, column=0, columnspan=2, sticky="ew", pady=(5, 10))
            self.emp_reg_entries[label_text] = entry
            row_idx += 1

        # Agência (NOVO CAMPO)
        ctk.CTkLabel(form_frame, text="Agência", font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA
        ).grid(row=row_idx, column=0, sticky="w", pady=(10, 0))
        self.emp_reg_agencia_var = ctk.StringVar(value="1") # Padrão '1'
        agencia_menu = ctk.CTkOptionMenu(
            form_frame, variable=self.emp_reg_agencia_var,
            values=["1"], # Só temos a agência 1 por enquanto
            height=40, font=ctk.CTkFont(size=14), corner_radius=8,
            fg_color=COR_FUNDO_FORM, button_color="#555555", button_hover_color="#666666"
        )
        agencia_menu.grid(row=row_idx, column=1, sticky="ew", pady=(5, 10), padx=(5,0))
        row_idx += 1

        # Cargo
        ctk.CTkLabel(form_frame, text="Cargo (Hierarquia)", font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA
        ).grid(row=row_idx, column=0, sticky="w", pady=(10, 0))
        self.emp_reg_cargo_var = ctk.StringVar(value="ATENDENTE")
        cargo_menu = ctk.CTkOptionMenu(
            form_frame, variable=self.emp_reg_cargo_var,
            values=["ESTAGIARIO", "ATENDENTE", "GERENTE"],
            height=40, font=ctk.CTkFont(size=14), corner_radius=8,
            fg_color=COR_FUNDO_FORM, button_color="#555555", button_hover_color="#666666"
        )
        cargo_menu.grid(row=row_idx, column=1, sticky="ew", pady=(5, 20), padx=(5,0))
        row_idx += 1

        ctk.CTkButton(
            form_frame, text="CADASTRAR FUNCIONÁRIO", command=self.do_register_employee,
            height=40, font=ctk.CTkFont(size=14, weight="bold"), corner_radius=8,
            fg_color=COR_BOTAO_AZUL_CLARO, hover_color="#40A8E0"
        ).grid(row=row_idx, column=0, columnspan=2, sticky="ew", pady=(20, 10))

    def do_register_employee(self):
        try:
            nome = self.emp_reg_entries["Nome Completo"].get()
            cpf = self.emp_reg_entries["CPF"].get()
            data_nasc = self.emp_reg_entries["Data de Nascimento (AAAA-MM-DD)"].get()
            telefone = self.emp_reg_entries["Telefone"].get()
            endereco = self.emp_reg_entries["Endereço"].get()
            salario_str = self.emp_reg_entries["Salário (Ex: 3500.00)"].get()
            pw1 = self.emp_reg_entries["Senha"].get()
            pw2 = self.emp_reg_entries["Confirmar Senha"].get()
            cargo = self.emp_reg_cargo_var.get()
            id_agencia = int(self.emp_reg_agencia_var.get())

            if not all([nome, cpf, pw1, pw2, cargo, salario_str, data_nasc, telefone, endereco]):
                messagebox.showwarning("Campos Vazios", "Por favor, preencha todos os campos.", parent=self)
                return
            if pw1 != pw2:
                messagebox.showerror("Senhas Diferentes", "As senhas não coincidem.", parent=self)
                return
            try:
                datetime.strptime(data_nasc, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Data Inválida", "Formato de Data de Nascimento inválido. Use AAAA-MM-DD.", parent=self)
                return

            if not self.user_entity:
                messagebox.showerror("Erro", "Usuário não logado.", parent=self)
                return

            self.config(cursor="watch"); self.update_idletasks()

            ok, msg = self.auth_service.register_employee_completo(
                nome=nome, cpf_input=cpf, senha=pw1,
                data_nasc=data_nasc, telefone=telefone, endereco=endereco,
                salario_str=salario_str, cargo=cargo, id_agencia=id_agencia,
                admin_user=self.user_entity # Passa o admin logado para validação
            )

            self.config(cursor="")
            if ok:
                messagebox.showinfo("Sucesso!", msg, parent=self)
                self.show_employee_dashboard_screen()
            else:
                messagebox.showerror("Erro no Cadastro", msg, parent=self)
        except Exception as e:
            self.config(cursor="")
            messagebox.showerror("Erro de Formulário", f"Ocorreu um erro ao processar os dados: {e}", parent=self)

    # -----------------------------------------------------------------
    # 🛠️ MÉTODOS DO PAINEL DE FUNCIONÁRIO (Consultas)
    # -----------------------------------------------------------------

    def _render_key_value_frame(self, parent_frame, title: str, data: Dict[str, Any], data_to_cache: Optional[Any] = None, edit_command: Optional[Callable] = None):
        """Helper para renderizar os quadros de consulta."""
        for widget in parent_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(parent_frame, text=title, font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(5, 10))

        # Cache dos dados para o botão "Alterar"
        self.cached_client_data = None
        self.cached_account_data = None
        self.cached_employee_data = None
        if data_to_cache:
            if title == "Dados do Cliente": self.cached_client_data = data_to_cache
            elif title == "Dados da Conta": self.cached_account_data = data_to_cache
            elif title == "Dados do Funcionário": self.cached_employee_data = data_to_cache

        font_label = ctk.CTkFont(size=12)
        font_value = ctk.CTkFont(size=12, weight="bold")

        for key, value in data.items():
            row = ctk.CTkFrame(parent_frame, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(row, text=key, font=font_label, text_color=COR_TEXTO_CINZA, anchor="e", width=150).pack(side="left", padx=(0, 10))
            ctk.CTkLabel(row, text=value, font=font_value, anchor="w", wraplength=300).pack(side="left", fill="x", expand=True)

        if edit_command:
            ctk.CTkButton(
                parent_frame, text="Alterar Dados",
                command=edit_command,
                fg_color=COR_BOTAO_LARANJA, hover_color=COR_BOTAO_LARANJA_HOVER
            ).pack(pady=10, padx=10, fill="x")

    def show_consulta_cliente_screen(self):
        self.clear_frame()
        self.title("Banco Malvader - Consultar Cliente")
        self.cached_client_data = None

        ctk.CTkButton(self.main_frame, text="← Voltar", command=self.show_employee_dashboard_screen,
                      fg_color="transparent", text_color=COR_BOTAO_AZUL_CLARO,
                      hover_color=COR_FUNDO, font=ctk.CTkFont(size=14)
        ).pack(anchor="w", padx=20, pady=(10, 0))

        ctk.CTkLabel(self.main_frame, text="Consultar Cliente",
                      font=ctk.CTkFont(size=32, weight="bold"),
                      text_color=COR_TEXTO_TITULO
        ).pack(pady=(10, 20))

        # --- Barra de Busca ---
        search_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(search_frame, text="CPF do Cliente:").pack(side="left", padx=(10, 5))
        self.consulta_cpf_entry = ctk.CTkEntry(search_frame, width=300)
        self.consulta_cpf_entry.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(search_frame, text="Buscar", command=self.do_consultar_cliente).pack(side="left", padx=5)

        # --- Frame de Resultados ---
        self.consulta_results_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color=COR_FUNDO_FRAME)
        self.consulta_results_frame.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(self.consulta_results_frame, text="Digite um CPF para buscar.", text_color=COR_TEXTO_CINZA).pack(pady=30)

    def do_consultar_cliente(self):
        cpf = self.consulta_cpf_entry.get()
        self.config(cursor="watch"); self.update_idletasks()
        ok, data = self.auth_service.get_client_details_from_view(cpf)
        self.config(cursor="")

        frame = self.consulta_results_frame
        for widget in frame.winfo_children(): widget.destroy()

        if not ok or not data:
            ctk.CTkLabel(frame, text=f"Cliente não encontrado: {data}", text_color=COR_TEXTO_VERMELHO).pack(pady=30)
            return

        # Formata os dados para exibição
        display_data = {
            "ID Cliente": data.get('id_cliente'),
            "Nome": data.get('nome'),
            "CPF": format_cpf(data.get('cpf')),
            "Data Nasc.": (data.get('data_nascimento').strftime('%d/%m/%Y') if data.get('data_nascimento') else "N/A"),
            "Telefone": data.get('telefone') or "N/A",
            "Endereço": data.get('endereco') or "N/A",
            "Status": data.get('status_usuario'),
            "Score Crédito": data.get('score_credito', 'N/A')
        }

        # Renderiza o quadro de dados principais
        main_data_frame = ctk.CTkFrame(frame, fg_color=COR_FUNDO_FORM)
        main_data_frame.pack(fill="x", padx=10, pady=10)
        self._render_key_value_frame(
            main_data_frame, "Dados do Cliente", display_data,
            data_to_cache=data, # Cache dos dados brutos
            edit_command=self.open_edit_client_dialog
        )

        # Botões de Ação
        action_frame = ctk.CTkFrame(frame, fg_color="transparent")
        action_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(action_frame, text="Recalcular Score (Procedure)", command=self.do_recalcular_score).pack(side="left", padx=5)

        # Lista de Contas
        ctk.CTkLabel(frame, text="Contas do Cliente", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
        ok_contas, contas = self.conta_service.get_contas_cliente(data.get('id_cliente'))

        if not ok_contas or not contas:
            ctk.CTkLabel(frame, text="Nenhuma conta encontrada.", text_color=COR_TEXTO_CINZA).pack(pady=10)
            return

        for conta in contas:
            cor_status = COR_TEXTO_VERDE if conta.status == 'ATIVA' else COR_TEXTO_VERMELHO
            conta_frame = ctk.CTkFrame(frame, fg_color=COR_FUNDO_FORM)
            conta_frame.pack(fill="x", padx=10, pady=5)

            ctk.CTkLabel(conta_frame, text=f"{self.get_display_name(conta.tipo_conta)} ({conta.numero_conta})", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(5,0))
            ctk.CTkLabel(conta_frame, text=f"Saldo: {self.format_currency(conta.saldo)}", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=10)
            ctk.CTkLabel(conta_frame, text=f"Status: {conta.status}", font=ctk.CTkFont(size=12, weight="bold"), text_color=cor_status).pack(anchor="w", padx=10, pady=(0,5))

    def do_recalcular_score(self):
        if not self.cached_client_data:
            messagebox.showerror("Erro", "Busque um cliente primeiro.")
            return

        id_cliente = self.cached_client_data.get('id_cliente')
        self.config(cursor="watch"); self.update_idletasks()
        ok, data = self.auth_service.get_client_score(id_cliente)
        self.config(cursor="")

        if ok:
            messagebox.showinfo("Sucesso", f"Novo score do cliente recalculado: {data}")
            self.do_consultar_cliente() # Recarrega a tela
        else:
            messagebox.showerror("Erro na Procedure", str(data))

    def open_edit_client_dialog(self):
        if not self.cached_client_data: return
        dialog = EditClientDialog(self, self, self.cached_client_data)
        dialog.wait_window()
        self.do_consultar_cliente() # Recarrega os dados após fechar

    def show_consulta_conta_screen(self):
        self.clear_frame()
        self.title("Banco Malvader - Consultar Conta")
        self.cached_account_data = None

        ctk.CTkButton(self.main_frame, text="← Voltar", command=self.show_employee_dashboard_screen,
                      fg_color="transparent", text_color=COR_BOTAO_AZUL_CLARO,
                      hover_color=COR_FUNDO, font=ctk.CTkFont(size=14)
        ).pack(anchor="w", padx=20, pady=(10, 0))

        ctk.CTkLabel(self.main_frame, text="Consultar Conta",
                      font=ctk.CTkFont(size=32, weight="bold"),
                      text_color=COR_TEXTO_TITULO
        ).pack(pady=(10, 20))

        search_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(search_frame, text="Número da Conta:").pack(side="left", padx=(10, 5))
        self.consulta_conta_entry = ctk.CTkEntry(search_frame, width=300, placeholder_text="Ex: 0001-12345-6-CC")
        self.consulta_conta_entry.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(search_frame, text="Buscar", command=self.do_consultar_conta).pack(side="left", padx=5)

        self.consulta_results_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color=COR_FUNDO_FRAME)
        self.consulta_results_frame.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(self.consulta_results_frame, text="Digite um número de conta para buscar.", text_color=COR_TEXTO_CINZA).pack(pady=30)

    def do_consultar_conta(self):
        num_conta = self.consulta_conta_entry.get()
        self.config(cursor="watch"); self.update_idletasks()
        ok, conta_obj = self.conta_service.get_conta_details(num_conta)
        self.config(cursor="")

        frame = self.consulta_results_frame
        for widget in frame.winfo_children(): widget.destroy()

        if not ok or not conta_obj:
            ctk.CTkLabel(frame, text=f"Conta não encontrada: {conta_obj}", text_color=COR_TEXTO_VERMELHO).pack(pady=30)
            return

        display_data = {
            "ID Conta": conta_obj.id_conta,
            "Número": conta_obj.numero_conta,
            "Tipo": self.get_display_name(conta_obj.tipo_conta),
            "Status": conta_obj.status,
            "Saldo": self.format_currency(conta_obj.saldo),
            "ID Cliente": conta_obj.id_cliente
        }

        if conta_obj.tipo_conta == 'CC':
            display_data["Limite CC"] = self.format_currency(conta_obj.limite_cc)
            display_data["Taxa Manut."] = self.format_currency(conta_obj.taxa_manutencao)
            display_data["Dia Venc. Taxa"] = conta_obj.data_vencimento_taxa
        elif conta_obj.tipo_conta == 'CP':
            display_data["Taxa Rendimento"] = f"{conta_obj.taxa_rendimento * 100:.2f}%"
        elif conta_obj.tipo_conta == 'CI':
            display_data["Perfil de Risco"] = conta_obj.perfil_risco
            display_data["Valor Mínimo"] = self.format_currency(conta_obj.valor_minimo_investimento)

        main_data_frame = ctk.CTkFrame(frame, fg_color=COR_FUNDO_FORM)
        main_data_frame.pack(fill="x", padx=10, pady=10)
        self._render_key_value_frame(
            main_data_frame, "Dados da Conta", display_data,
            data_to_cache=conta_obj, # Cache do objeto Conta
            edit_command=self.open_edit_account_dialog
        )

        # --- BOTÕES DE AÇÃO NA CONSULTA DE CONTA ---
        action_frame = ctk.CTkFrame(frame, fg_color="transparent")
        action_frame.pack(fill="x", padx=10, pady=5)

        # Botão para Alterar Senha do Cliente (Novo)
        # O ID do Usuário é necessário para alterar a senha
        id_cliente = conta_obj.id_cliente
        if id_cliente:
             ctk.CTkButton(
                action_frame,
                text="🔓 Alterar Senha do Cliente",
                command=lambda id_c=id_cliente: self.open_change_client_password_dialog(id_c),
                fg_color=COR_BOTAO_ROXO,
                hover_color="#6F358C"
            ).pack(side="left", padx=5, fill="x", expand=True)

        ctk.CTkButton(action_frame, text="Ver Extrato Desta Conta", command=lambda c=conta_obj: self.show_extrato_para_conta(c)).pack(side="right", padx=5)


    # --- NOVO MÉTODO PARA ALTERAR SENHA (FUNCIONÁRIO) ---
    def open_change_client_password_dialog(self, id_cliente: int):
        """Abre um diálogo para o funcionário alterar a senha de um cliente."""
        if not self.user_entity or self.user_entity.tipo_usuario != 'FUNCIONARIO':
            messagebox.showerror("Acesso Negado", "Apenas funcionários podem realizar esta ação.")
            return

        try:
            # 1. Obter o ID do Usuário (id_usuario) a partir do ID do Cliente
            # O repositório de usuários deve ter um método para buscar o id_usuario
            client_user_id = self.auth_service.usuario_repo.get_user_id_by_client_id(id_cliente)

        except AttributeError:
             messagebox.showerror("Erro de Repositório", "Método 'get_user_id_by_client_id' não encontrado no repositório de usuários. Implemente-o.")
             return
        except Exception as e:
             messagebox.showerror("Erro de Busca", f"Não foi possível buscar ID do usuário: {e}")
             return

        if not client_user_id:
             messagebox.showerror("Erro", "ID de usuário do cliente não encontrado.")
             return

        new_pass = simpledialog.askstring("Alterar Senha do Cliente",
                                          f"Digite a NOVA SENHA para o cliente com ID do Usuário {client_user_id}:",
                                          parent=self, show="*")

        if not new_pass:
            return

        # 2. Chama o serviço para alterar a senha (sem exigir a senha antiga, pois é um administrador)
        self.config(cursor="watch"); self.update_idletasks()

        # O self.user_entity é o funcionário logado (admin)
        ok_pass, msg_pass = self.auth_service.change_password(
            id_usuario_alvo=client_user_id,
            old_pass="",  # Admin não precisa da senha antiga (AuthService trata a permissão)
            new_pass=new_pass,
            logged_in_user=self.user_entity
        )
        self.config(cursor="")

        if ok_pass:
            messagebox.showinfo("Sucesso", "Senha do cliente alterada com sucesso!", parent=self)
        else:
            messagebox.showerror("Erro", msg_pass, parent=self)


    def open_edit_account_dialog(self):
        if not self.cached_account_data: return
        dialog = EditAccountDialog(self, self, self.cached_account_data)
        dialog.wait_window()
        self.do_consultar_conta() # Recarrega os dados

    def show_extrato_para_conta(self, conta: Conta):
        """Versão do extrato para o funcionário."""
        # Define a conta ativa temporariamente para o método de extrato
        self.active_account = conta
        self.show_extrato_screen(go_back_command=self.show_consulta_conta_screen)

    def show_consulta_funcionario_screen(self):
        self.clear_frame()
        self.title("Banco Malvader - Consultar Funcionário")
        self.cached_employee_data = None

        ctk.CTkButton(self.main_frame, text="← Voltar", command=self.show_employee_dashboard_screen,
                      fg_color="transparent", text_color=COR_BOTAO_AZUL_CLARO,
                      hover_color=COR_FUNDO, font=ctk.CTkFont(size=14)
        ).pack(anchor="w", padx=20, pady=(10, 0))

        ctk.CTkLabel(self.main_frame, text="Consultar Funcionário",
                      font=ctk.CTkFont(size=32, weight="bold"),
                      text_color=COR_TEXTO_TITULO
        ).pack(pady=(10, 20))

        search_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(search_frame, text="CPF do Funcionário:").pack(side="left", padx=(10, 5))
        self.consulta_func_cpf_entry = ctk.CTkEntry(search_frame, width=300)
        self.consulta_func_cpf_entry.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(search_frame, text="Buscar", command=self.do_consultar_funcionario).pack(side="left", padx=5)

        self.consulta_results_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color=COR_FUNDO_FRAME)
        self.consulta_results_frame.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(self.consulta_results_frame, text="Digite um CPF para buscar.", text_color=COR_TEXTO_CINZA).pack(pady=30)

    def do_consultar_funcionario(self):
        cpf = self.consulta_func_cpf_entry.get()
        self.config(cursor="watch"); self.update_idletasks()
        ok, data = self.auth_service.get_employee_details_from_view(cpf)
        self.config(cursor="")

        frame = self.consulta_results_frame
        for widget in frame.winfo_children(): widget.destroy()

        if not ok or not data:
            ctk.CTkLabel(frame, text=f"Funcionário não encontrado: {data}", text_color=COR_TEXTO_VERMELHO).pack(pady=30)
            return

        display_data = {
            "ID Func.": data.get('id_funcionario'),
            "ID Usuário": data.get('id_usuario'),
            "Nome": data.get('nome'),
            "CPF": format_cpf(data.get('cpf')),
            "Cargo": data.get('cargo'),
            "Salário": self.format_currency(Decimal(data.get('salario', '0.0'))),
            "Agência": data.get('nome_agencia'),
            "Telefone": data.get('telefone') or "N/A",
            "Endereço": data.get('endereco') or "N/A",
        }

        main_data_frame = ctk.CTkFrame(frame, fg_color=COR_FUNDO_FORM)
        main_data_frame.pack(fill="x", padx=10, pady=10)

        # Não implementamos alteração de funcionário ainda
        self._render_key_value_frame(
            main_data_frame, "Dados do Funcionário", display_data,
            data_to_cache=data # Cache dos dados brutos
            # edit_command=self.open_edit_employee_dialog # <-- A ser implementado
        )

        ctk.CTkButton(frame, text="Ver Relatório de Desempenho (Procedure)",
                      command=self.do_consultar_desempenho
        ).pack(fill="x", padx=10, pady=5)

        self.desempenho_frame = ctk.CTkFrame(frame, fg_color=COR_FUNDO_FORM)
        self.desempenho_frame.pack(fill="x", padx=10, pady=10)

    def do_consultar_desempenho(self):
        if not self.cached_employee_data:
            messagebox.showerror("Erro", "Busque um funcionário primeiro.")
            return

        id_funcionario = self.cached_employee_data.get('id_funcionario')
        self.config(cursor="watch"); self.update_idletasks()
        ok, data = self.auth_service.get_employee_performance(id_funcionario)
        self.config(cursor="")

        frame = self.desempenho_frame
        for widget in frame.winfo_children(): widget.destroy()

        if not ok:
            ctk.CTkLabel(frame, text=f"Erro ao buscar desempenho: {data}", text_color=COR_TEXTO_VERMELHO).pack(pady=10)
            return

        display_data = {
            "Contas Abiertas": data.get('contas_abertas', 0),
            "Total Movimentado": self.format_currency(Decimal(data.get('total_movimentado', '0.0'))),
            "Média por Conta": self.format_currency(Decimal(data.get('media_por_conta', '0.0')))
        }
        self._render_key_value_frame(frame, "Desempenho (Procedure)", display_data)

    # -----------------------------------------------------------------
    # 🛠️ MÉTODOS DO PAINEL DE FUNCIONÁRIO (Operações)
    # -----------------------------------------------------------------

    def show_encerrar_conta_dialog(self):
        """Handler para o botão de encerrar conta."""
        numero_conta = simpledialog.askstring("Encerrar Conta", "Digite o NÚMERO da conta a ser encerrada:", parent=self)
        if not numero_conta:
            return

        motivo = simpledialog.askstring("Motivo", "Digite o MOTIVO do encerramento (Ex: Solicitação do cliente):", parent=self)
        if not motivo:
            messagebox.showwarning("Obrigatório", "O motivo é obrigatório para o log.", parent=self)
            return

        # 1. Busca a conta para garantir que ela existe
        ok, conta = self.conta_service.get_conta_details(numero_conta)
        if not ok or not conta:
            messagebox.showerror("Erro", f"Conta '{numero_conta}' não encontrada.", parent=self)
            return

        if conta.status == 'ENCERRADA':
            messagebox.showinfo("Aviso", "Esta conta já está encerrada.", parent=self)
            return

        # 2. Confirmação
        if not messagebox.askyesno("Confirmar Encerramento",
                                   f"Deseja encerrar a conta {conta.numero_conta} (Tipo: {conta.tipo_conta})?\n\n"
                                   f"Saldo Atual: {self.format_currency(conta.saldo)}\n"
                                   f"Motivo: {motivo}\n\n"
                                   "A conta deve ter saldo R$ 0,00.",
                                   parent=self, icon='warning'):
            return

        # 3. Chama o serviço (que chama a procedure)
        self.config(cursor="watch"); self.update_idletasks()
        ok_proc, msg_proc = self.conta_service.encerrar_conta(
            id_conta=conta.id_conta,
            motivo=motivo,
            id_funcionario=self.user_entity.id_funcionario
        )
        self.config(cursor="")

        if ok_proc:
            messagebox.showinfo("Sucesso", msg_proc, parent=self)
        else:
            # Mostra o erro vindo da Procedure (ex: "Saldo pendente")
            messagebox.showerror("Erro na Procedure", msg_proc, parent=self)

    # -----------------------------------------------------------------
    # 🛠️ MÉTODOS DO PAINEL DE FUNCIONÁRIO (Relatórios)
    # -----------------------------------------------------------------

    def show_relatorio_movimentacoes_screen(self):
        """Relatório Avançado de Movimentações (usa VIEW)."""
        self.clear_frame()
        self.title("Banco Malvader - Relatório de Movimentações")

        ctk.CTkButton(self.main_frame, text="← Voltar", command=self.show_employee_dashboard_screen,
                      fg_color="transparent", text_color=COR_BOTAO_AZUL_CLARO,
                      hover_color=COR_FUNDO, font=ctk.CTkFont(size=14)
        ).pack(anchor="w", padx=20, pady=(10, 0))

        ctk.CTkLabel(self.main_frame, text="Relatório de Movimentações",
                      font=ctk.CTkFont(size=32, weight="bold"),
                      text_color=COR_TEXTO_TITULO
        ).pack(pady=(10, 20))

        filter_frame = ctk.CTkFrame(self.main_frame, fg_color=COR_FUNDO_FRAME)
        filter_frame.pack(padx=20, pady=10, fill="x")

        today = datetime.now().strftime("%Y-%m-%d")

        # Filtros de Data
        ctk.CTkLabel(filter_frame, text="Data Início:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.report_start_entry = ctk.CTkEntry(filter_frame, placeholder_text="AAAA-MM-DD")
        self.report_start_entry.insert(0, today)
        self.report_start_entry.grid(row=0, column=1, padx=10, pady=10)

        ctk.CTkLabel(filter_frame, text="Data Fim:").grid(row=0, column=2, padx=10, pady=10, sticky="e")
        self.report_end_entry = ctk.CTkEntry(filter_frame, placeholder_text="AAAA-MM-DD")
        self.report_end_entry.insert(0, today)
        self.report_end_entry.grid(row=0, column=3, padx=10, pady=10)

        # --- NOVOS FILTROS ---
        ctk.CTkLabel(filter_frame, text="Tipo Transação:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.report_tipo_var = ctk.StringVar(value="TODOS")
        tipo_menu = ctk.CTkOptionMenu(
            filter_frame, variable=self.report_tipo_var,
            values=["TODOS", "DEPOSITO", "SAQUE", "TRANSFERENCIA", "INVESTIR", "RESGATAR"]
        )
        tipo_menu.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(filter_frame, text="Agência:").grid(row=1, column=2, padx=10, pady=10, sticky="e")
        self.report_agencia_var = ctk.StringVar(value="TODAS")
        agencia_menu = ctk.CTkOptionMenu(
            filter_frame, variable=self.report_agencia_var,
            values=["TODAS", "1"] # Só temos agência 1
        )
        agencia_menu.grid(row=1, column=3, padx=10, pady=10, sticky="ew")
        # --- FIM DOS NOVOS FILTROS ---

        ctk.CTkButton(
            filter_frame, text="🔎 Buscar Relatório",
            command=self.do_get_movimentacoes_report,
            fg_color=COR_BOTAO_AZUL_CLARO, hover_color="#2C81B0"
        ).grid(row=0, column=4, rowspan=2, padx=20, pady=10, sticky="ns")

        self.report_results_frame = ctk.CTkScrollableFrame(
            self.main_frame, fg_color=COR_FUNDO_FRAME, corner_radius=16
        )
        self.report_results_frame.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(self.report_results_frame, text="Insira os filtros e clique em 'Buscar'.", text_color=COR_TEXTO_CINZA).pack(pady=30)

    def do_get_movimentacoes_report(self):
        start_date = self.report_start_entry.get()
        end_date = self.report_end_entry.get()
        tipo_transacao = self.report_tipo_var.get()
        id_agencia = self.report_agencia_var.get()

        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Data Inválida", "Use o formato AAAA-MM-DD para as datas.", parent=self)
            return

        agencia_filtro = None
        if id_agencia != "TODAS":
            agencia_filtro = int(id_agencia)

        frame = self.report_results_frame
        for widget in frame.winfo_children(): widget.destroy()

        try:
            self.config(cursor="watch"); self.update_idletasks()
            ok, data = self.conta_service.get_relatorio_movimentacoes(
                start_date, end_date, tipo_transacao, agencia_filtro
            )
            self.config(cursor="")

            if not ok: raise Exception(data[0])
            if not data:
                ctk.CTkLabel(frame, text="Nenhuma transação encontrada para estes filtros.", text_color=COR_TEXTO_CINZA).pack(pady=30)
                return

            header_frame = ctk.CTkFrame(frame, fg_color="#333333", height=30)
            header_frame.pack(fill="x", padx=10, pady=(5, 5), anchor="n")
            header_font = ctk.CTkFont(size=12, weight="bold")

            headers = ["Data", "Tipo", "Valor", "Origem", "Destino", "Agência(s)"]
            col_weights = [20, 15, 15, 20, 20, 10]

            for i, (text, weight) in enumerate(zip(headers, col_weights)):
                header_frame.grid_columnconfigure(i, weight=weight)
                ctk.CTkLabel(header_frame, text=text, font=header_font, anchor="w").grid(row=0, column=i, sticky="w", padx=5)

            total = Decimal("0.0")
            for row in data:
                item_frame = ctk.CTkFrame(frame, fg_color=COR_FUNDO_FORM, corner_radius=6)
                item_frame.pack(fill="x", padx=10, pady=4, anchor="n")

                valor = Decimal(row.get('valor', '0.0'))
                total += valor

                agencia = row.get('agencia_origem') or row.get('agencia_destino')

                cols = [
                    (row.get('data_transacao').strftime('%d/%m/%Y %H:%M') if row.get('data_transacao') else "N/A"),
                    self.get_display_name(row.get('tipo_transacao')),
                    self.format_currency(valor),
                    row.get('cpf_cliente_origem') or row.get('conta_origem') or "N/A",
                    row.get('cpf_cliente_destino') or row.get('conta_destino') or "N/A",
                    f"Ag. {agencia}" if agencia else "N/A"
                ]

                for i, (text, weight) in enumerate(zip(cols, col_weights)):
                    item_frame.grid_columnconfigure(i, weight=weight)
                    ctk.CTkLabel(item_frame, text=text, font=ctk.CTkFont(size=12), anchor="w", wraplength=150).grid(row=0, column=i, sticky="w", padx=5, pady=5)

            # Total
            ctk.CTkFrame(frame, fg_color=COR_TEXTO_CINZA, height=1).pack(fill="x", padx=10, pady=10)
            ctk.CTkLabel(frame, text=f"Total Movimentado: {self.format_currency(total)} ({len(data)} transações)",
                         font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)

        except Exception as e:
            ctk.CTkLabel(frame, text=f"Erro ao gerar relatório: {e}", text_color=COR_TEXTO_VERMELHO).pack(pady=30)

    def show_relatorio_inadimplentes_screen(self):
        """Relatório de Clientes Inadimplentes (usa VIEW)."""
        self.clear_frame()
        self.title("Banco Malvader - Relatório de Inadimplentes")

        ctk.CTkButton(self.main_frame, text="← Voltar", command=self.show_employee_dashboard_screen,
                      fg_color="transparent", text_color=COR_BOTAO_AZUL_CLARO,
                      hover_color=COR_FUNDO, font=ctk.CTkFont(size=14)
        ).pack(anchor="w", padx=20, pady=(10, 0))

        ctk.CTkLabel(self.main_frame, text="Relatório de Clientes Inadimplentes",
                      font=ctk.CTkFont(size=32, weight="bold"),
                      text_color=COR_TEXTO_TITULO
        ).pack(pady=(10, 20))

        results_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color=COR_FUNDO_FRAME, corner_radius=16)
        results_frame.pack(fill="both", expand=True, padx=20, pady=20)

        try:
            self.config(cursor="watch"); self.update_idletasks()
            ok, data = self.conta_service.get_relatorio_inadimplentes()
            self.config(cursor="")

            if not ok: raise Exception(data[0])
            if not data:
                ctk.CTkLabel(results_frame, text="Nenhum cliente inadimplente encontrado.", text_color=COR_TEXTO_VERDE).pack(pady=30)
                return

            header_frame = ctk.CTkFrame(results_frame, fg_color="#333333", height=30)
            header_frame.pack(fill="x", padx=10, pady=(5, 5), anchor="n")
            header_font = ctk.CTkFont(size=12, weight="bold")

            headers = ["Nome", "CPF", "Telefone", "Nº Conta", "Saldo Devedor"]
            col_weights = [30, 20, 20, 15, 15]

            for i, (text, weight) in enumerate(zip(headers, col_weights)):
                header_frame.grid_columnconfigure(i, weight=weight)
                ctk.CTkLabel(header_frame, text=text, font=header_font, anchor="w").grid(row=0, column=i, sticky="w", padx=5)

            total_divida = Decimal("0.0")
            for row in data:
                item_frame = ctk.CTkFrame(results_frame, fg_color=COR_FUNDO_FORM, corner_radius=6)
                item_frame.pack(fill="x", padx=10, pady=4, anchor="n")

                saldo = Decimal(row.get('saldo', '0.0'))
                total_divida += saldo # Saldo é negativo, então somamos

                cols = [
                    row.get('nome'),
                    format_cpf(row.get('cpf')),
                    row.get('telefone'),
                    row.get('numero_conta'),
                    self.format_currency(saldo)
                ]

                for i, (text, weight) in enumerate(zip(cols, col_weights)):
                    item_frame.grid_columnconfigure(i, weight=weight)
                    ctk.CTkLabel(item_frame, text=text, font=ctk.CTkFont(size=12), anchor="w").grid(row=0, column=i, sticky="w", padx=5, pady=5)

            ctk.CTkFrame(results_frame, fg_color=COR_TEXTO_CINZA, height=1).pack(fill="x", padx=10, pady=10)
            ctk.CTkLabel(results_frame, text=f"Total Devido: {self.format_currency(total_divida)} ({len(data)} clientes)",
                         font=ctk.CTkFont(size=14, weight="bold"), text_color=COR_TEXTO_VERMELHO).pack(pady=10)

        except Exception as e:
            ctk.CTkLabel(results_frame, text=f"Erro ao gerar relatório: {e}", text_color=COR_TEXTO_VERMELHO).pack(pady=30)

    # -----------------------------------------------------------------
    # ⚡ MÉTODOS DE AÇÃO (Handlers de Cliente)
    # -----------------------------------------------------------------

    def load_accounts(self):
        """Carrega as contas do cliente logado."""
        if self.user_entity and self.user_entity.id_cliente:
            try:
                # O serviço get_contas_cliente já retorna o par (ok, lista/msg)
                ok, fetched_accounts = self.conta_service.get_contas_cliente(self.user_entity.id_cliente)

                if ok:
                    # Filtra apenas contas ativas (ENCERRADA não deve ser mostrada)
                    self.accounts = [acc for acc in fetched_accounts if acc.status == 'ATIVA']
                    # Ordena: CC, CP, CI (para priorizar a exibição)
                    self.accounts.sort(key=lambda x: (x.tipo_conta == 'CC', x.tipo_conta == 'CP', x.tipo_conta == 'CI'), reverse=True)
                else:
                    messagebox.showerror("Erro de Conta", fetched_accounts, parent=self)
                    self.accounts = []

            except Exception as e:
                messagebox.showerror("Erro de Rede", f"Não foi possível buscar as contas: {e}", parent=self)
                self.accounts = []
        else:
            self.accounts = []

    def _reload_account_data(self) -> bool:
        """Força a recarga dos dados das contas do cliente."""
        print("Recarregando dados das contas...")
        try:
            current_active_id = self.active_account.id_conta if self.active_account else None
            self.load_accounts()

            if not self.accounts:
                 self.logout()
                 return False

            found = False
            if current_active_id:
                for acc in self.accounts:
                    if acc.id_conta == current_active_id:
                        self.active_account = acc
                        found = True
                        break
            if not found:
                self.active_account = next((acc for acc in self.accounts if acc.tipo_conta == 'CC'), self.accounts[0])

            return True
        except Exception as e:
            messagebox.showerror("Erro de Rede", f"Não foi possível recarregar as contas: {e}", parent=self)
            self.logout()
            return False

    def reload_accounts_balance(self):
        """Recarrega os dados e atualiza a UI."""
        print("Recarregando saldo e atualizando widgets...")
        if self._reload_account_data():
            self.update_dashboard_display()
            self.update_dashboard_layout()

            if hasattr(self, 'account_switcher') and self.account_switcher.winfo_exists():
                account_names = list(self.account_name_map.keys())
                user_account_types = [acc.tipo_conta for acc in self.accounts]
                account_names_to_show = [name for name in account_names if self.account_name_map[name] in user_account_types]

                self.account_switcher.configure(values=account_names_to_show)
                if self.active_account:
                    self.account_switcher.set(self.get_display_name(self.active_account.tipo_conta))

    def show_deposito_screen(self):
        """Tela para realizar depósito."""
        if not self.active_account:
            messagebox.showerror("Erro", "Nenhuma conta ativa selecionada.", parent=self)
            return

        self.clear_frame()
        ctk.CTkButton(self.main_frame, text="← Voltar", command=self.show_dashboard_screen,
                      fg_color="transparent", text_color=COR_BOTAO_AZUL_CLARO,
                      hover_color=COR_FUNDO, font=ctk.CTkFont(size=14)
        ).pack(anchor="w", padx=20, pady=(10, 0))

        ctk.CTkLabel(self.main_frame, text="Depósito",
                     font=ctk.CTkFont(size=32, weight="bold"),
                     text_color=COR_TEXTO_TITULO
        ).pack(pady=(10, 30))

        op_frame = ctk.CTkFrame(self.main_frame, fg_color=COR_FUNDO_FRAME, corner_radius=16)
        op_frame.pack(padx=20, pady=20)

        ctk.CTkLabel(op_frame, text=f"Conta Destino: {self.active_account.numero_conta} ({self.get_display_name(self.active_account.tipo_conta)})",
                     font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(20, 10), padx=30)

        ctk.CTkLabel(op_frame, text=f"Saldo Atual: {self.format_currency(self.active_account.saldo)}",
                     font=ctk.CTkFont(size=14), text_color=COR_TEXTO_VERDE
        ).pack(pady=(0, 20), padx=30)

        ctk.CTkLabel(op_frame, text="Valor (R$)", font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA
        ).pack(anchor="w", padx=30, pady=(10, 0))
        self.deposito_valor_entry = ctk.CTkEntry(op_frame, width=300, height=40)
        self.deposito_valor_entry.pack(padx=30, pady=(5, 10))

        ctk.CTkLabel(op_frame, text="Descrição (Opcional)", font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA
        ).pack(anchor="w", padx=30, pady=(10, 0))
        self.deposito_desc_entry = ctk.CTkEntry(op_frame, width=300, height=40)
        self.deposito_desc_entry.pack(padx=30, pady=(5, 20))

        ctk.CTkButton(
            op_frame, text="CONFIRMAR DEPÓSITO", command=self.do_deposit,
            width=300, height=40, font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COR_BOTAO_VERDE, hover_color=COR_BOTAO_VERDE_HOVER
        ).pack(padx=30, pady=(20, 30))

    def do_deposit(self):
        if not self.active_account:
            messagebox.showerror("Erro", "Nenhuma conta ativa selecionada.", parent=self)
            return
        valor_str = self.deposito_valor_entry.get()
        try:
            valor = Decimal(valor_str.replace(',', '.'))
            if valor <= 0: raise InvalidOperation
        except InvalidOperation:
            messagebox.showerror("Valor Inválido", "O valor do depósito deve ser um número positivo (maior que zero).", parent=self)
            return
        descricao = self.deposito_desc_entry.get()
        try:
            self.config(cursor="watch"); self.update_idletasks()
            ok, msg = self.conta_service.depositar(self.active_account.id_conta, valor_str, descricao)
            self.config(cursor="")
            if ok:
                # 1. Recarrega o estado (solução de sincronização)
                self.reload_accounts_balance()
                # 2. Mostra o sucesso (bloqueia o fluxo até o usuário clicar OK)
                messagebox.showinfo("Sucesso", msg, parent=self)
                # 3. Manda para o dashboard, destruindo a tela de depósito AGORA
                self.show_dashboard_screen()
            else:
                messagebox.showerror("Erro no Depósito", msg, parent=self)
        except Exception as e:
            self.config(cursor="")
            messagebox.showerror("Erro Crítico", f"Ocorreu um erro inesperado: {e}", parent=self)

    def show_saque_screen(self):
        """Tela para realizar saque."""
        if not self.active_account:
            messagebox.showerror("Erro", "Nenhuma conta ativa selecionada.", parent=self)
            return

        self.clear_frame()
        ctk.CTkButton(self.main_frame, text="← Voltar", command=self.show_dashboard_screen,
                      fg_color="transparent", text_color=COR_BOTAO_AZUL_CLARO,
                      hover_color=COR_FUNDO, font=ctk.CTkFont(size=14)
        ).pack(anchor="w", padx=20, pady=(10, 0))

        ctk.CTkLabel(self.main_frame, text="Saque",
                     font=ctk.CTkFont(size=32, weight="bold"),
                     text_color=COR_TEXTO_TITULO
        ).pack(pady=(10, 30))

        op_frame = ctk.CTkFrame(self.main_frame, fg_color=COR_FUNDO_FRAME, corner_radius=16)
        op_frame.pack(padx=20, pady=20)

        ctk.CTkLabel(op_frame, text=f"Conta Origem: {self.active_account.numero_conta} ({self.get_display_name(self.active_account.tipo_conta)})",
                     font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(20, 10), padx=30)

        ctk.CTkLabel(op_frame, text=f"Saldo Atual: {self.format_currency(self.active_account.saldo)}",
                     font=ctk.CTkFont(size=14), text_color=COR_TEXTO_VERDE
        ).pack(pady=(0, 20), padx=30)

        ctk.CTkLabel(op_frame, text="Valor (R$)", font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA
        ).pack(anchor="w", padx=30, pady=(10, 0))
        self.saque_valor_entry = ctk.CTkEntry(op_frame, width=300, height=40)
        self.saque_valor_entry.pack(padx=30, pady=(5, 10))

        ctk.CTkButton(
            op_frame, text="CONFIRMAR SAQUE", command=self.do_saque,
            width=300, height=40, font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COR_BOTAO_LARANJA, hover_color=COR_BOTAO_LARANJA_HOVER
        ).pack(padx=30, pady=(20, 30))

    def do_saque(self):
        if not self.active_account:
            messagebox.showerror("Erro", "Nenhuma conta ativa selecionada.", parent=self)
            return
        valor_str = self.saque_valor_entry.get()
        try:
            valor = Decimal(valor_str.replace(',', '.'))
            if valor <= 0: raise InvalidOperation
        except InvalidOperation:
            messagebox.showerror("Valor Inválido", "O valor do saque deve ser um número positivo (maior que zero).", parent=self)
            return
        try:
            self.config(cursor="watch"); self.update_idletasks()
            ok, msg = self.conta_service.sacar(self.active_account.id_conta, valor_str)
            self.config(cursor="")
            if ok:
                self.reload_accounts_balance()
                messagebox.showinfo("Sucesso", msg, parent=self)
                self.show_dashboard_screen()
            else:
                messagebox.showerror("Erro no Saque", msg, parent=self)
        except Exception as e:
            self.config(cursor="")
            messagebox.showerror("Erro Crítico", f"Ocorreu um erro inesperado: {e}", parent=self)

    def show_transferencia_screen(self):
        """Tela para realizar transferência."""
        if not self.active_account:
            messagebox.showerror("Erro", "Nenhuma conta ativa selecionada.", parent=self)
            return

        self.clear_frame()
        ctk.CTkButton(self.main_frame, text="← Voltar", command=self.show_dashboard_screen,
                      fg_color="transparent", text_color=COR_BOTAO_AZUL_CLARO,
                      hover_color=COR_FUNDO, font=ctk.CTkFont(size=14)
        ).pack(anchor="w", padx=20, pady=(10, 0))

        ctk.CTkLabel(self.main_frame, text="Transferência",
                     font=ctk.CTkFont(size=32, weight="bold"),
                     text_color=COR_TEXTO_TITULO
        ).pack(pady=(10, 30))

        op_frame = ctk.CTkFrame(self.main_frame, fg_color=COR_FUNDO_FRAME, corner_radius=16)
        op_frame.pack(padx=20, pady=20)

        ctk.CTkLabel(op_frame, text=f"Conta Origem: {self.active_account.numero_conta} ({self.get_display_name(self.active_account.tipo_conta)})",
                     font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(20, 10), padx=30)

        ctk.CTkLabel(op_frame, text=f"Saldo Atual: {self.format_currency(self.active_account.saldo)}",
                     font=ctk.CTkFont(size=14), text_color=COR_TEXTO_VERDE
        ).pack(pady=(0, 20), padx=30)

        # Tipo de Chave
        ctk.CTkLabel(op_frame, text="Tipo de Destino", font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA
        ).pack(anchor="w", padx=30, pady=(10, 0))
        self.transfer_tipo_var = ctk.StringVar(value="CPF")
        ctk.CTkSegmentedButton(op_frame, variable=self.transfer_tipo_var, values=["CPF", "Conta"],
                               font=ctk.CTkFont(size=14)).pack(padx=30, pady=(5, 10), fill="x")

        # Destino
        ctk.CTkLabel(op_frame, text="Destino (CPF ou Nº Conta)", font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA
        ).pack(anchor="w", padx=30, pady=(10, 0))
        self.transfer_destino_entry = ctk.CTkEntry(op_frame, width=300, height=40)
        self.transfer_destino_entry.pack(padx=30, pady=(5, 10))

        # Valor
        ctk.CTkLabel(op_frame, text="Valor (R$)", font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA
        ).pack(anchor="w", padx=30, pady=(10, 0))
        self.transfer_valor_entry = ctk.CTkEntry(op_frame, width=300, height=40)
        self.transfer_valor_entry.pack(padx=30, pady=(5, 10))

        # Descrição
        ctk.CTkLabel(op_frame, text="Descrição (Opcional)", font=ctk.CTkFont(size=12), text_color=COR_TEXTO_CINZA
        ).pack(anchor="w", padx=30, pady=(10, 0))
        self.transfer_desc_entry = ctk.CTkEntry(op_frame, width=300, height=40)
        self.transfer_desc_entry.pack(padx=30, pady=(5, 20))

        ctk.CTkButton(
            op_frame, text="CONFIRMAR TRANSFERÊNCIA", command=self.do_transferencia,
            width=300, height=40, font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COR_BOTAO_AZUL_CLARO, hover_color="#2C81B0"
        ).pack(padx=30, pady=(20, 30))

    def do_transferencia(self):
        if not self.active_account:
            messagebox.showerror("Erro", "Nenhuma conta ativa selecionada.", parent=self)
            return
        tipo_selecionado = self.transfer_tipo_var.get()
        destino = self.transfer_destino_entry.get()
        valor_str = self.transfer_valor_entry.get()
        descricao = self.transfer_desc_entry.get()

        if not all([destino, valor_str]):
            messagebox.showwarning("Campos Vazios", "Preencha o destino e o valor.", parent=self)
            return

        try:
            valor = Decimal(valor_str.replace(',', '.'))
            if valor <= 0: raise InvalidOperation
        except InvalidOperation:
            messagebox.showerror("Valor Inválido", "O valor da transferência deve ser um número positivo (maior que zero).", parent=self)
            return

        try:
            by = 'cpf' if tipo_selecionado == "CPF" else 'account'
            self.config(cursor="watch"); self.update_idletasks()
            ok, msg = self.conta_service.transferir(self.active_account.id_conta, destino, by, valor_str, descricao)
            self.config(cursor="")
            if ok:
                self.reload_accounts_balance()
                messagebox.showinfo("Sucesso", msg, parent=self)
                self.show_dashboard_screen()
            else:
                messagebox.showerror("Erro na Transferência", msg, parent=self)
        except Exception as e:
            self.config(cursor="")
            messagebox.showerror("Erro Crítico", f"Ocorreu um erro inesperado: {e}", parent=self)

    def show_extrato_screen(self, go_back_command=None):
        """Tela para exibir o extrato."""
        if not self.active_account:
            messagebox.showerror("Erro", "Nenhuma conta ativa selecionada.", parent=self)
            self_command = go_back_command if go_back_command else self.show_dashboard_screen
            self_command()
            return

        self.clear_frame()
        back_command = go_back_command if go_back_command else self.show_dashboard_screen

        ctk.CTkButton(self.main_frame, text="← Voltar", command=back_command,
                      fg_color="transparent", text_color=COR_BOTAO_AZUL_CLARO,
                      hover_color=COR_FUNDO, font=ctk.CTkFont(size=14)
        ).pack(anchor="w", padx=20, pady=(10, 0))

        ctk.CTkLabel(self.main_frame, text="Extrato da Conta",
                     font=ctk.CTkFont(size=32, weight="bold"),
                     text_color=COR_TEXTO_TITULO
        ).pack(pady=(10, 10))

        ctk.CTkLabel(self.main_frame, text=f"Conta: {self.active_account.numero_conta} ({self.get_display_name(self.active_account.tipo_conta)})",
                     font=ctk.CTkFont(size=16)
        ).pack(pady=(0, 10))

        extrato_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color=COR_FUNDO_FRAME, corner_radius=16)
        extrato_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.config(cursor="watch"); self.update_idletasks()
        ok, transacoes = self.conta_service.get_extrato(self.active_account.id_conta)
        self.config(cursor="")

        if not ok:
            ctk.CTkLabel(extrato_frame, text=f"Erro ao buscar extrato: {transacoes}", text_color=COR_TEXTO_VERMELHO).pack(pady=30)
            return

        if not transacoes:
            ctk.CTkLabel(extrato_frame, text="Nenhuma transação encontrada.", text_color=COR_TEXTO_CINZA).pack(pady=30)
            return

        # Tabela de Extrato
        header_frame = ctk.CTkFrame(extrato_frame, fg_color="#333333", height=30)
        header_frame.pack(fill="x", padx=10, pady=(5, 5), anchor="n")
        header_font = ctk.CTkFont(size=12, weight="bold")

        # Define as colunas e pesos (total 100)
        col_info = [("Data", 25), ("Tipo", 20), ("Descrição/Destino", 40), ("Valor (R$)", 15)]
        col_weights = [25, 20, 40, 15]

        # Configura o cabeçalho
        for i, (text, weight) in enumerate(col_info):
            header_frame.grid_columnconfigure(i, weight=weight)
            ctk.CTkLabel(header_frame, text=text, font=header_font, anchor="w").grid(row=0, column=i, sticky="w", padx=5)

        for transacao in transacoes:
            # CORREÇÃO: Verifica se o objeto transacao existe e possui o atributo esperado
            if not isinstance(transacao, Transacao) or not hasattr(transacao, 'tipo'):
                 # Ignora ou trata a transação malformada
                 continue

            item_frame = ctk.CTkFrame(extrato_frame, fg_color=COR_FUNDO_FORM, corner_radius=6)
            item_frame.pack(fill="x", padx=10, pady=4, anchor="n")

            valor = transacao.valor
            cor = COR_TEXTO_VERDE if valor >= 0 else COR_TEXTO_VERMELHO

            # Formatação da Descrição/Destino
            if transacao.tipo == 'TRANSFERENCIA':
                # CORREÇÃO: Usa o novo atributo 'conta_origem' e 'conta_destino'
                desc = f"Transferência para {transacao.conta_destino}"
                if transacao.conta_origem == self.active_account.numero_conta:
                    desc = f"Transferência para {transacao.conta_destino}"
                    if transacao.cpf_cliente_destino:
                        desc += f" (CPF: {format_cpf(transacao.cpf_cliente_destino)})"
                else:
                    desc = f"Transferência de {transacao.conta_origem}"
                    if transacao.cpf_cliente_origem:
                        desc += f" (CPF: {format_cpf(transacao.cpf_cliente_origem)})"
            elif transacao.tipo in ['INVESTIR', 'RESGATAR', 'RENDIMENTO_CDI', 'RENDIMENTO_BOLSA']:
                # CORREÇÃO: Usa o nome da caixinha (tipo_investimento)
                caixinha_nome = transacao.caixinha_nome or transacao.tipo
                desc = f"{self.get_display_name(transacao.tipo)} - {caixinha_nome}"
            else:
                desc = transacao.descricao or self.get_display_name(transacao.tipo)

            cols = [
                transacao.data_transacao.strftime('%d/%m/%Y %H:%M'),
                self.get_display_name(transacao.tipo),
                desc,
                self.format_currency(valor)
            ]

            # Renderiza as linhas (Usando col_weights para o grid)
            for i, text in enumerate(cols):
                item_frame.grid_columnconfigure(i, weight=col_weights[i])
                text_color = cor if i == 3 else COR_TEXTO_BRANCO
                ctk.CTkLabel(item_frame, text=text, font=ctk.CTkFont(size=12), text_color=text_color, anchor="w", wraplength=200).grid(row=0, column=i, sticky="w", padx=5, pady=5)

    # Fim do método show_extrato_screen


    def do_aplicar_rendimento_poupanca(self):
        if not self.active_account or self.active_account.tipo_conta != 'CP':
            messagebox.showerror("Erro", "Esta função só está disponível para Contas Poupança.", parent=self)
            return
        if not messagebox.askyesno("Confirmar Rendimento",
                                   f"Aplicar rendimento de {self.active_account.taxa_rendimento * 100:.2f}% sobre o saldo de {self.format_currency(self.active_account.saldo)}?",
                                   parent=self):
            return
        try:
            self.config(cursor="watch"); self.update_idletasks()
            ok, msg = self.conta_service.aplicar_rendimento_poupanca(self.active_account.id_conta)
            self.config(cursor="")
            if ok:
                self.reload_accounts_balance()
                messagebox.showinfo("Sucesso", msg, parent=self)
                self.show_dashboard_screen()
            else:
                messagebox.showerror("Erro ao Aplicar Rendimento", msg, parent=self)
        except Exception as e:
            self.config(cursor="")
            messagebox.showerror("Erro Crítico", f"Ocorreu um erro inesperado: {e}", parent=self)

    def do_investir(self, caixinha: CaixinhaInvestimento):
        # 1. Checa se há conta de origem (CC ou CP) com saldo > 0
        conta_corrente = next((acc for acc in self.accounts if acc.tipo_conta == 'CC' and acc.status == 'ATIVA'), None)
        conta_poupanca = next((acc for acc in self.accounts if acc.tipo_conta == 'CP' and acc.status == 'ATIVA'), None)

        source_accounts = {}
        if conta_corrente and conta_corrente.saldo > 0:
            source_accounts["Conta Corrente"] = conta_corrente
        if conta_poupanca and conta_poupanca.saldo > 0:
            source_accounts["Poupança"] = conta_poupanca

        if not source_accounts:
            messagebox.showerror("Erro", "Nenhuma Conta Corrente ou Poupança com saldo encontrada para investir.", parent=self)
            return

        # 2. Pergunta qual conta usar (se houver mais de uma)
        conta_origem = None
        if len(source_accounts) == 1:
            conta_origem = list(source_accounts.values())[0]
        else:
            dialog = SourceAccountDialog(self, source_accounts)
            conta_origem = dialog.get_choice()
            if not conta_origem: return

        # 3. Pede o valor
        valor_str = simpledialog.askstring(
            "Investir",
            f"Quanto deseja investir na Caixinha {caixinha.tipo_investimento}?\n\n"
            f"Origem: {self.get_display_name(conta_origem.tipo_conta)}\n"
            f"Saldo: {self.format_currency(conta_origem.saldo)}",
            parent=self)

        if not valor_str: return

        try:
            valor = Decimal(valor_str.replace(',', '.'))
            if valor <= 0: raise InvalidOperation
        except InvalidOperation:
            messagebox.showerror("Valor Inválido", "O valor do investimento deve ser um número positivo (maior que zero).", parent=self)
            return

        # 4. Chama o serviço
        try:
            self.config(cursor="watch"); self.update_idletasks()
            ok, msg = self.conta_service.investir(
                conta_origem_id=conta_origem.id_conta,
                caixinha_destino_id=caixinha.id_caixinha,
                valor_str=valor_str
            )
            self.config(cursor="")
            if ok:
                self.reload_accounts_balance()
                messagebox.showinfo("Sucesso", msg, parent=self)
                self.show_dashboard_screen()
            else:
                messagebox.showerror("Erro ao Investir", msg, parent=self)
        except Exception as e:
            self.config(cursor="")
            messagebox.showerror("Erro Crítico", f"Ocorreu um erro inesperado: {e}", parent=self)

    def do_resgatar(self, caixinha: CaixinhaInvestimento):
        # 1. Checa se há Conta Corrente para receber o resgate
        conta_corrente = next((acc for acc in self.accounts if acc.tipo_conta == 'CC' and acc.status == 'ATIVA'), None)
        if not conta_corrente:
            messagebox.showerror("Erro", "Nenhuma Conta Corrente ativa encontrada para receber o resgate.", parent=self)
            return

        # 2. Pede o valor
        valor_str = simpledialog.askstring(
            "Resgatar",
            f"Quanto deseja resgatar da Caixinha {caixinha.tipo_investimento}?\n\n"
            f"Saldo na Caixinha: {self.format_currency(caixinha.saldo)}",
            parent=self)

        if not valor_str: return

        try:
            valor = Decimal(valor_str.replace(',', '.'))
            if valor <= 0: raise InvalidOperation
        except InvalidOperation:
            messagebox.showerror("Valor Inválido", "O valor do resgate deve ser um número positivo (maior que zero).", parent=self)
            return

        # 3. Chama o serviço
        try:
            self.config(cursor="watch"); self.update_idletasks()
            ok, msg = self.conta_service.resgatar(
                caixinha_origem_id=caixinha.id_caixinha,
                conta_destino_id=conta_corrente.id_conta,
                valor_str=valor_str
            )
            self.config(cursor="")
            if ok:
                self.reload_accounts_balance()
                messagebox.showinfo("Sucesso", msg, parent=self)
                self.show_dashboard_screen() # Chamada de transição
            else:
                messagebox.showerror("Erro ao Resgatar", msg, parent=self)
        except Exception as e:
            self.config(cursor="")
            messagebox.showerror("Erro Crítico", f"Ocorreu um erro inesperado: {e}", parent=self)

    def do_aplicar_rendimento_investimento(self, caixinha: CaixinhaInvestimento):
        taxa_str = "115% do CDI (0.91%/mês)" if caixinha.tipo_investimento == 'CDI' else "Bolsa (0.015%/dia)"

        if not messagebox.askyesno("Confirmar Rendimento",
                                   f"Simular aplicação de rendimento de {taxa_str} sobre o saldo de {self.format_currency(caixinha.saldo)}?",
                                   parent=self):
            return

        try:
            self.config(cursor="watch"); self.update_idletasks()
            ok, msg = self.conta_service.aplicar_rendimento_investimento(caixinha.id_caixinha)
            self.config(cursor="")
            if ok:
                self.reload_accounts_balance()
                messagebox.showinfo("Sucesso", msg, parent=self)
                self.show_dashboard_screen()
            else:
                messagebox.showerror("Erro ao Aplicar Rendimento", msg, parent=self)
        except Exception as e:
            self.config(cursor="")
            messagebox.showerror("Erro Crítico", f"Ocorreu um erro inesperado: {e}", parent=self)

    def logout(self):
        """Limpa a sessão e volta para a tela de login."""
        self.user_entity = None
        self.accounts = []
        self.active_account = None
        self.cached_client_data = None
        self.cached_account_data = None
        self.cached_employee_data = None
        self.show_login_screen()

    def show_delete_account_dialog(self):
        """Handler para o botão 'Excluir Conta' (agora usado pelo cliente)."""
        if not self.user_entity:
            self.logout()
            return

        senha = simpledialog.askstring("Confirmar Exclusão",
                                       f"Você está prestes a DELETAR seu usuário ({self.user_entity.nome}).\n"
                                       "Isso apagará seu login e TODAS as suas contas (CC, CP, CI).\n\n"
                                       "Esta ação NÃO PODE ser desfeita.\n"
                                       "Digite sua SENHA para confirmar:",
                                       parent=self, show="*")
        if not senha:
            return

        if not messagebox.askyesno("Confirmar Exclusão Final",
                                   "Você tem CERTEZA?\n\nTODOS os seus dados (contas, caixinhas, extratos) serão PERMANENTEMENTE apagados.",
                                   parent=self, icon='warning'):
            return

        self.do_delete_account(self.user_entity.cpf, senha)

    def do_delete_account(self, cpf, senha):
        """Chama o serviço de autenticação para deletar a conta (lógica antiga)."""
        self.config(cursor="watch"); self.update_idletasks()
        try:
            if not hasattr(self.auth_service, 'delete_account'):
                # Simula o erro da funcionalidade não implementada no service mockado
                raise NotImplementedError("Funcionalidade 'delete_account' não implementada no AuthService.")

            ok, msg = self.auth_service.delete_account(cpf, senha)
        except NotImplementedError:
            ok, msg = False, "Erro: Funcionalidade de exclusão de usuário não implementada no backend. Use o encerramento manual de contas pelo funcionário."
        except Exception as e:
            ok, msg = False, f"Erro crítico na exclusão: {e}"

        self.config(cursor="")

        if ok:
            messagebox.showinfo("Conta Excluída", msg, parent=self)
            self.logout()
        else:
            messagebox.showerror("Erro na Exclusão", msg, parent=self)

            #final do gui