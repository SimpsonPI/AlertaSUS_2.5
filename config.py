import os
from dotenv import load_dotenv
from supabase import create_client, Client
from zoneinfo import ZoneInfo

# Carrega o .env se existir localmente (no seu PC), mas ignora se não achar (no Railway)
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Validação segura que não quebra o deploy se as variáveis já estiverem no painel do Railway
if not TELEGRAM_BOT_TOKEN or not SUPABASE_URL or not SUPABASE_KEY:
    print("⚠️ ATENÇÃO: Alguma variável de ambiente principal está faltando!")

# ==================== IDs DE ADMINISTRAÇÃO ====================

raw_admin_id = os.getenv("ADMIN_CHAT_ID", "5444152614").strip()
ADMIN_CHAT_ID = int(raw_admin_id) if raw_admin_id.isdigit() else None

raw_admin_ids = os.getenv("ADMIN_IDS", "5242040324").strip()
ADMIN_IDS = [int(x.strip()) for x in raw_admin_ids.split(",") if x.strip().isdigit()]

# ==================== CONFIGURAÇÕES DE API E SERVIDOR ====================

SCRAPER_KEY = os.getenv("SCRAPER_KEY")
PORT = int(os.getenv("PORT", 10000))

# URL Base do Formulário WebApp no GitHub Pages
URL_FORMULARIO_PAGES = "https://simpsonpi.github.io/alerta-sus-bot/"

# ==================== CONTATOS E CANAIS OFICIAIS DO ALERTASUS ====================
# ATUALIZADO com os novos contatos
EMAIL_SUPORTE = "suportealertasus@gmail.com"
BOT_SUPORTE_USERNAME = "@Atendimento_AlertaSUS_2.0"
BOT_SUPORTE_LINK = "https://t.me/Atendimento_AlertaSUS_2.0"

# ==================== VALIDAÇÃO DAS VARIÁVEIS OBRIGATÓRIAS ====================

# No final do seu config.py, mude a verificação para ignorar se faltar o token principal caso seja o suporte:
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("⚠️ ERRO CRÍTICO: Variáveis SUPABASE_URL ou SUPABASE_KEY não configuradas no arquivo .env!")

# O token do Telegram passa a ser opcional aqui para evitar travar o serviço de suporte
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ==================== CLIENTE SUPABASE ====================

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==================== CONFIGURAÇÕES GLOBAIS ====================

FUSO_HORARIO = ZoneInfo("America/Fortaleza")
URL_BUSCA_FMS = "https://agendamentos.sus.fms.pmt.pi.gov.br/detail_scheduling/index"

BOT_APP = None
MAIN_LOOP = None

# ==================== CONFIGURAÇÕES DO BOT DE SUPORTE ====================

# Token do bot de suporte (deve estar no arquivo .env)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# ID do canal de suporte no Telegram
CANAL_SUPORTE_ID = -1004479965268

# ==================== ESTADOS DO CONVERSATIONHANDLER ====================

# Estados principais do fluxo de atendimento
MENU_PRINCIPAL = 0              # Menu inicial com FAQ e opções
AGUARDANDO_MENSAGEM = 1         # Aguardando mensagem do usuário
AGUARDANDO_RESPOSTA_ADMIN = 2   # Aguardando resposta do administrador
AGUARDANDO_FAQ = 3              # Navegando pelo FAQ

# ==================== MENSAGENS DO SISTEMA ====================

# Mensagens de confirmação e status
MSG_RESPOSTA_ENVIADA = "✅ Resposta enviada com sucesso para o usuário!"
MSG_ATENDIMENTO_ENCERRADO = "❌ Atendimento encerrado. Se precisar de algo, acesse o menu novamente!"
MSG_MODAL_RESPOSTA = "✍️ <b>Modo de Resposta Ativado</b> para o ID: <code>{user_id}</code>\n\nDigite a mensagem que deseja enviar para este usuário agora:"

# Mensagens de boas-vindas e menu
MSG_BOAS_VINDAS = (
    "🤖 <b>Central de Atendimento ao Usuário AlertaSUS 2.0</b>\n\n"
    "Seja bem-vindo(a)! Como posso ajudá-lo hoje?\n\n"
    "🔹 <b>Menu Principal:</b>\n"
    "• /ajuda - Perguntas Frequentes (FAQ)\n"
    "• /suporte - Falar com a equipe de suporte\n"
    "• /planos - Gerenciar planos e assinatura\n"
    "• /privacidade - Política de privacidade\n\n"
    f"📧 <b>E-mail Oficial:</b> {EMAIL_SUPORTE}\n"
    f"🤖 <b>Bot de Atendimento:</b> {BOT_SUPORTE_USERNAME}"
)

MSG_SUPORTE_INICIAL = (
    "🛠️ <b>Canais de Atendimento</b>\n\n"
    "Precisa de auxílio ou deseja reportar um problema?\n"
    f"• <b>E-mail:</b> <code>{EMAIL_SUPORTE}</code>\n"
    f"• <b>Telegram:</b> {BOT_SUPORTE_USERNAME}\n\n"
    "Nossa equipe responderá em horário comercial."
)

MSG_ATENDIMENTO_INICIADO = (
    "🎧 <b>Atendimento Personalizado AlertaSUS</b>\n\n"
    "Olá! Escreva abaixo a sua dúvida ou demanda para que nossa equipe receba por aqui:\n\n"
    "✏️ <i>Digite sua mensagem agora...</i>"
)

# Rodapé padrão para alertas automáticos do sistema
RODAPE_ALERTAS = (
    f"\n\n━━━━━━━━━━━━━━━━━━━━\n"
    f"📧 E-mail: {EMAIL_SUPORTE}\n"
    f"🤖 Atendimento: {BOT_SUPORTE_LINK}"
)

# ==================== CONFIGURAÇÕES DE SEGURANÇA ====================

# Tempo máximo de inatividade (em segundos) antes de encerrar um chamado
TIMEOUT_ATENDIMENTO = 3600  # 1 hora

# Número máximo de tentativas de envio de mensagem
MAX_TENTATIVAS_ENVIO = 3

# ==================== CONFIGURAÇÕES DO BANCO DE DADOS ====================

# Nomes das tabelas no Supabase
TABELA_USUARIOS = "usuarios"
TABELA_REGULACOES = "regulacoes"
TABELA_CHAMADOS = "chamados_suporte"
TABELA_HISTORICO = "historico_atendimento"

# ==================== FUNÇÕES AUXILIARES ====================

def is_admin(user_id: int) -> bool:
    """
    Verifica se um usuário é administrador
    
    Args:
        user_id: ID do usuário do Telegram
        
    Returns:
        bool: True se for administrador, False caso contrário
    """
    return user_id in ADMIN_IDS or user_id == ADMIN_CHAT_ID

def get_fuso_horario():
    """
    Retorna o fuso horário configurado
    
    Returns:
        ZoneInfo: Objeto ZoneInfo com o fuso horário
    """
    return FUSO_HORARIO

def get_supabase_client() -> Client:
    """
    Retorna o cliente Supabase configurado
    
    Returns:
        Client: Cliente Supabase
    """
    return supabase

# ==================== VALIDAÇÃO ADICIONAL ====================

# Verifica se o token do bot de suporte está configurado
if not TELEGRAM_BOT_TOKEN:
    print("⚠️ AVISO: TELEGRAM_BOT_TOKEN não configurado. O bot de suporte pode não funcionar.")

# Verifica se o ID do canal é válido
if CANAL_SUPORTE_ID >= 0:
    print("⚠️ AVISO: CANAL_SUPORTE_ID parece ser um ID de grupo positivo. Certifique-se de que é um ID de canal/chat válido.")

# ==================== EXPORTAÇÕES ====================

# Lista de todas as variáveis exportadas para facilitar a importação
__all__ = [
    # Configurações principais
    'SUPABASE_URL',
    'SUPABASE_KEY',
    'TELEGRAM_BOT_TOKEN',
    
    # IDs de administração
    'ADMIN_CHAT_ID',
    'ADMIN_IDS',
    
    # Configurações de API e servidor
    'SCRAPER_KEY',
    'PORT',
    'URL_FORMULARIO_PAGES',
    'EMAIL_SUPORTE',
    'BOT_SUPORTE_USERNAME',
    'BOT_SUPORTE_LINK',
    'RODAPE_ALERTAS',
    
    # Cliente Supabase
    'supabase',
    
    # Configurações globais
    'FUSO_HORARIO',
    'URL_BUSCA_FMS',
    'BOT_APP',
    'MAIN_LOOP',
    
    # Configurações do bot de suporte
    'TELEGRAM_BOT_TOKEN',
    'CANAL_SUPORTE_ID',
    
    # Estados do ConversationHandler
    'MENU_PRINCIPAL',
    'AGUARDANDO_MENSAGEM',
    'AGUARDANDO_RESPOSTA_ADMIN',
    'AGUARDANDO_FAQ',
    
    # Mensagens do sistema
    'MSG_RESPOSTA_ENVIADA',
    'MSG_ATENDIMENTO_ENCERRADO',
    'MSG_MODAL_RESPOSTA',
    'MSG_BOAS_VINDAS',
    'MSG_SUPORTE_INICIAL',
    'MSG_ATENDIMENTO_INICIADO',
    
    # Configurações de segurança
    'TIMEOUT_ATENDIMENTO',
    'MAX_TENTATIVAS_ENVIO',
    
    # Configurações do banco de dados
    'TABELA_USUARIOS',
    'TABELA_REGULACOES',
    'TABELA_CHAMADOS',
    'TABELA_HISTORICO',
    
    # Funções auxiliares
    'is_admin',
    'get_fuso_horario',
    'get_supabase_client',
]