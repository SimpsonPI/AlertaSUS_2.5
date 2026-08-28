import asyncio
import logging
from datetime import datetime
from warnings import filterwarnings

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.warnings import PTBUserWarning
from telegram.ext import ContextTypes, filters, MessageHandler, CallbackQueryHandler, CommandHandler

from config import (
    CANAL_SUPORTE_ID,
    FUSO_HORARIO,
    MSG_ATENDIMENTO_ENCERRADO,
)

# Defina o estado caso ele venha do config ou diretamente aqui:
AGUARDANDO_MENSAGEM = 1

filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# ==================== DADOS COMPARTILHADOS ====================
CHAMADOS_ATIVOS = {}        # user_id -> message_id no canal
HISTORICO_CONVERSA = {}     # user_id -> lista de mensagens
ULTIMA_MENSAGEM_USUARIO = {} # user_id -> message_id da última mensagem do usuário
MODO_RESPOSTA_ADMIN = {}    # admin_id -> user_id (quem o admin está respondendo)
LOCK_DADOS = asyncio.Lock()


# ==================== FUNÇÕES AUXILIARES ====================

def formatar_historico(historico: list) -> str:
    if not historico:
        return "📝 <i>Nenhuma mensagem ainda.</i>"
    
    texto = ""
    for msg in historico:
        if msg['tipo'] == 'usuario':
            texto += f"\n👤 <b>Você:</b> {msg['texto']}"
        elif msg['tipo'] == 'suporte':
            texto += f"\n💬 <b>Suporte:</b> {msg['texto']}"
        elif msg['tipo'] == 'sistema':
            texto += f"\n📌 {msg['texto']}"
    return texto


def atualizar_historico(user_id: int, tipo: str, texto: str):
    if user_id not in HISTORICO_CONVERSA:
        HISTORICO_CONVERSA[user_id] = []
    
    HISTORICO_CONVERSA[user_id].append({
        'tipo': tipo,
        'texto': texto,
        'timestamp': datetime.now(FUSO_HORARIO).strftime("%H:%M")
    })


async def atualizar_interface_usuario(context, user_id: int, mensagem_extra: str = None):
    """Atualiza a mensagem do usuário com o histórico"""
    try:
        if user_id not in HISTORICO_CONVERSA:
            return
        
        historico = HISTORICO_CONVERSA[user_id]
        
        texto = (
            "💬 <b>Histórico da Conversa</b>\n"
            "━━━━━━━━━━━━━━━━\n"
            f"{formatar_historico(historico)}\n"
            "━━━━━━━━━━━━━━━━\n\n"
        )
        
        if mensagem_extra:
            texto += mensagem_extra
        else:
            texto += "✏️ <i>Digite sua mensagem abaixo:</i>"
        
        teclado = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Encerrar Atendimento", callback_data="usuario_sair")]
        ])
        
        if user_id in ULTIMA_MENSAGEM_USUARIO:
            try:
                await context.bot.edit_message_text(
                    chat_id=user_id,
                    message_id=ULTIMA_MENSAGEM_USUARIO[user_id],
                    text=texto,
                    parse_mode="HTML",
                    reply_markup=teclado
                )
            except Exception as e:
                logger.warning(f"Não foi possível editar, enviando nova: {e}")
                msg = await context.bot.send_message(
                    chat_id=user_id,
                    text=texto,
                    parse_mode="HTML",
                    reply_markup=teclado
                )
                ULTIMA_MENSAGEM_USUARIO[user_id] = msg.message_id
        else:
            msg = await context.bot.send_message(
                chat_id=user_id,
                text=texto,
                parse_mode="HTML",
                reply_markup=teclado
            )
            ULTIMA_MENSAGEM_USUARIO[user_id] = msg.message_id
            
    except Exception as e:
        logger.error(f"Erro ao atualizar usuário {user_id}: {e}")


async def atualizar_canal_suporte(context, user_id: int):
    """Atualiza a mensagem no canal de suporte"""
    try:
        if user_id not in HISTORICO_CONVERSA:
            return
        
        historico = HISTORICO_CONVERSA[user_id]
        ultimas = historico[-5:] if len(historico) > 5 else historico
        
        try:
            user = await context.bot.get_chat(user_id)
            nome = user.full_name
            username = f"@{user.username}" if user.username else "Sem username"
        except:
            nome = f"Usuário {user_id}"
            username = "Sem username"
        
        texto = (
            f"🚨 <b>CHAMADO DE SUPORTE ATIVO</b>\n\n"
            f"• <b>Usuário:</b> {nome} ({username})\n"
            f"• <b>ID:</b> <code>{user_id}</code>\n"
            f"• <b>Status:</b> 🟢 Em atendimento\n\n"
            f"<b>💬 Últimas mensagens:</b>\n{formatar_historico(ultimas)}\n\n"
            f"<i>Clique em 'Responder' para enviar uma mensagem</i>"
        )
        
        teclado = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✍️ Responder Usuário", callback_data=f"resp_{user_id}"),
                InlineKeyboardButton("✅ Concluir Chamado", callback_data=f"concluir_{user_id}")
            ]
        ])
        
        if user_id in CHAMADOS_ATIVOS:
            try:
                await context.bot.edit_message_text(
                    chat_id=CANAL_SUPORTE_ID,
                    message_id=CHAMADOS_ATIVOS[user_id],
                    text=texto,
                    parse_mode="HTML",
                    reply_markup=teclado
                )
            except Exception as e:
                logger.warning(f"Não foi possível editar no canal: {e}")
                msg = await context.bot.send_message(
                    chat_id=CANAL_SUPORTE_ID,
                    text=texto,
                    parse_mode="HTML",
                    reply_markup=teclado
                )
                CHAMADOS_ATIVOS[user_id] = msg.message_id
        else:
            msg = await context.bot.send_message(
                chat_id=CANAL_SUPORTE_ID,
                text=texto,
                parse_mode="HTML",
                reply_markup=teclado
            )
            CHAMADOS_ATIVOS[user_id] = msg.message_id
            
    except Exception as e:
        logger.error(f"Erro ao atualizar canal: {e}")


# ==================== MENUS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start atualizado com canal de suporte e e-mail oficial"""
    texto = (
        "🤖 <b>Bem-vindo ao AlertaSUS 2.0!</b>\n\n"
        "Este bot monitora e envia informações atualizadas sobre dados de saúde e pesquisas.\n\n"
        "Escolha uma opção abaixo:\n\n"
        "📧 <b>Suporte Oficial:</b> suporte@alertasus.exemplo\n"
        "🤖 <b>Bot de Atendimento:</b> @SuporteAlertaSUS_bot"
    )
    teclado = InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Ajuda / FAQ", callback_data="ajuda")],
        [InlineKeyboardButton("🎧 Falar com Suporte", callback_data="ir_para_suporte")],
    ])
    
    await update.message.reply_text(texto, parse_mode="HTML", reply_markup=teclado)


async def menu_ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu de ajuda com FAQ e textos prontos solicitados"""
    texto = (
        "🤖 <b>Central de Ajuda - AlertaSUS</b>\n\n"
        "Este bot monitora e envia informações atualizadas sobre dados de saúde e pesquisas.\n\n"
        "• <b>Comandos disponíveis:</b> Use os botões do menu ou digite os filtros por estado.\n"
        "• <b>Suporte Técnico:</b> Se encontrar algum erro ou inconsistência, entre em contato pelo e-mail <code>suporte@alertasus.exemplo</code> ou fale diretamente com nossa equipe pelo bot de atendimento: @SuporteAlertaSUS_bot.\n\n"
        "Selecione uma opção:\n\n"
        "1️⃣ Como cadastrar regulação?\n"
        "2️⃣ Como consultar regulações?\n"
        "3️⃣ Onde achar Cartão SUS/ID?\n"
        "4️⃣ Como alterar dados?\n"
        "5️⃣ Planos e assinatura?"
    )
    teclado = InlineKeyboardMarkup([
        [InlineKeyboardButton("1️⃣ Cadastrar", callback_data="faq_cadastrar"),
         InlineKeyboardButton("2️⃣ Consultar", callback_data="faq_consultar")],
        [InlineKeyboardButton("3️⃣ Cartão SUS/ID", callback_data="faq_id"),
         InlineKeyboardButton("4️⃣ Alterar Dados", callback_data="faq_alterar")],
        [InlineKeyboardButton("5️⃣ Planos", callback_data="faq_planos")],
        [InlineKeyboardButton("💬 Falar com Suporte", callback_data="ir_para_suporte")],
        [InlineKeyboardButton("❌ Fechar", callback_data="fechar_menu")],
    ])
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(texto, parse_mode="HTML", reply_markup=teclado)
    else:
        await update.message.reply_text(texto, parse_mode="HTML", reply_markup=teclado)


async def menu_suporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu principal de suporte integrado com os canais e horários"""
    texto = (
        "🛠️ <b>Canais de Atendimento</b>\n\n"
        "Precisa de auxílio ou deseja reportar um problema?\n"
        "• <b>E-mail:</b> <code>suporte@alertasus.exemplo</code>\n"
        "• <b>Telegram:</b> @SuporteAlertaSUS_bot\n\n"
        "Nossa equipe responderá em horário comercial."
    )
    teclado = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎧 Iniciar Atendimento Interno", callback_data="iniciar_atendimento")],
        [InlineKeyboardButton("🤖 Bot de Atendimento", url="https://t.me/SuporteAlertaSUS_bot")],
        [InlineKeyboardButton("📧 Enviar E-mail", url="mailto:suporte@alertasus.exemplo")],
        [InlineKeyboardButton("📖 Voltar para Ajuda", callback_data="ajuda")],
        [InlineKeyboardButton("❌ Fechar", callback_data="fechar_menu")],
    ])
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(texto, parse_mode="HTML", reply_markup=teclado)
    else:
        await update.message.reply_text(texto, parse_mode="HTML", reply_markup=teclado)


async def exibir_resposta_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Exibe respostas do FAQ"""
    query = update.callback_query
    await query.answer()
    
    respostas = {
        "faq_cadastrar": "📌 Use /cadastrar_nova no bot principal",
        "faq_consultar": "🔍 Use /verificar_todos ou /verificar_especifico",
        "faq_id": "🆔 Cartão SUS: 15 dígitos no app Meu SUS Digital",
        "faq_alterar": "✏️ Use /corrigir no bot principal",
        "faq_planos": "💳 Use /planos no bot principal",
    }
    
    texto = respostas.get(query.data, "Informação não encontrada.")
    texto += "\n\nPrecisa de ajuda personalizada?"
    
    teclado = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎧 Abrir Chamado", callback_data="iniciar_atendimento")],
        [InlineKeyboardButton("⬅️ Voltar", callback_data="ajuda")],
    ])
    
    await query.edit_message_text(texto, parse_mode="HTML", reply_markup=teclado)


# ==================== FLUXO DO USUÁRIO ====================

async def iniciar_atendimento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia o atendimento personalizado"""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    
    logger.info(f"🟢 Iniciando atendimento para {user_id}")
    
    async with LOCK_DADOS:
        CHAMADOS_ATIVOS.pop(user_id, None)
        HISTORICO_CONVERSA.pop(user_id, None)
        ULTIMA_MENSAGEM_USUARIO.pop(user_id, None)
        MODO_RESPOSTA_ADMIN.pop(user_id, None)
        
        HISTORICO_CONVERSA[user_id] = []
        atualizar_historico(user_id, 'sistema', "🎧 Atendimento iniciado")
    
    texto = "🎧 <b>Atendimento AlertaSUS</b>\n\nDigite sua dúvida:"
    teclado = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Encerrar", callback_data="usuario_sair")]
    ])
    
    msg = await query.edit_message_text(texto, parse_mode="HTML", reply_markup=teclado)
    ULTIMA_MENSAGEM_USUARIO[user_id] = msg.message_id
    
    await atualizar_canal_suporte(context, user_id)


async def cancelar_atendimento_usuario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Usuário cancela o atendimento"""
    user_id = update.effective_user.id
    
    logger.info(f"🔴 Usuário {user_id} encerrou atendimento")
    
    async with LOCK_DADOS:
        CHAMADOS_ATIVOS.pop(user_id, None)
        HISTORICO_CONVERSA.pop(user_id, None)
        ULTIMA_MENSAGEM_USUARIO.pop(user_id, None)
        MODO_RESPOSTA_ADMIN.pop(user_id, None)
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(MSG_ATENDIMENTO_ENCERRADO)
    else:
        await update.message.reply_text(MSG_ATENDIMENTO_ENCERRADO)


# ==================== AÇÕES DO ADMIN ====================

async def callback_botoes_canal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gerencia os botões do canal de suporte"""
    query = update.callback_query
    await query.answer()
    data = query.data
    admin_id = update.effective_user.id
    user_id = int(data.split("_")[1])
    
    logger.info(f"🔄 Admin {admin_id} clicou em: {data}")
    
    if data.startswith("resp_"):
        MODO_RESPOSTA_ADMIN[admin_id] = user_id
        
        await query.message.reply_text(
            f"✍️ <b>Modo de resposta ativado</b>\n\n"
            f"Respondendo para usuário <code>{user_id}</code>\n\n"
            f"Digite sua mensagem abaixo:",
            parse_mode="HTML"
        )
        
        logger.info(f"✍️ Admin {admin_id} está respondendo {user_id}")
        
        try:
            await query.edit_message_text(
                text=query.message.text + "\n\n🔄 <i>Admin está digitando uma resposta...</i>",
                parse_mode="HTML"
            )
        except:
            pass
    
    elif data.startswith("concluir_"):
        logger.info(f"✅ Admin {admin_id} concluiu chamado de {user_id}")
        
        async with LOCK_DADOS:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="✅ <b>Chamado Concluído</b>\n\n"
                         "Seu chamado foi concluído pela equipe de suporte.\n\n"
                         "Obrigado por usar o AlertaSUS! 🙏",
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.warning(f"Não foi possível notificar usuário {user_id}: {e}")
            
            CHAMADOS_ATIVOS.pop(user_id, None)
            HISTORICO_CONVERSA.pop(user_id, None)
            ULTIMA_MENSAGEM_USUARIO.pop(user_id, None)
            MODO_RESPOSTA_ADMIN.pop(user_id, None)
        
        try:
            await query.edit_message_text(
                text=query.message.text + "\n\n<b>[✅ CHAMADO CONCLUÍDO]</b>",
                parse_mode="HTML",
                reply_markup=None
            )
        except:
            pass


async def cancelar_resposta_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.effective_user.id
    MODO_RESPOSTA_ADMIN.pop(admin_id, None)
    await update.message.reply_text("❌ Modo de resposta cancelado.")


# ==================== COMANDOS AUXILIARES ====================

async def comando_cadastrar_nova(update, context):
    await update.message.reply_text("📌 Use /cadastrar_nova no bot principal", parse_mode="HTML")

async def comando_verificar_todos(update, context):
    await update.message.reply_text("🔍 Use /verificar_todos no bot principal", parse_mode="HTML")

async def comando_verificar_especifico(update, context):
    await update.message.reply_text("🔍 Use /verificar_especifico no bot principal", parse_mode="HTML")

async def comando_corrigir(update, context):
    await update.message.reply_text("✏️ Use /corrigir no bot principal", parse_mode="HTML")

async def comando_excluir(update, context):
    await update.message.reply_text("🗑️ Use /excluir no bot principal", parse_mode="HTML")

async def comando_planos(update, context):
    await update.message.reply_text("💳 Use /planos no bot principal", parse_mode="HTML")

async def comando_privacidade(update, context):
    await update.message.reply_text("🔒 Política de Privacidade no bot principal", parse_mode="HTML")


# ==================== PROCESSAMENTO DE MENSAGENS ====================

async def processar_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa TODAS as mensagens de texto (usuário E admin) de forma unificada"""
    if not update.effective_user or not update.effective_chat:
        return
        
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if not update.message or not update.message.text:
        return
        
    texto = update.message.text
    
    if chat_id == CANAL_SUPORTE_ID:
        admin_id = user_id
        user_id_destino = MODO_RESPOSTA_ADMIN.get(admin_id)
        
        if not user_id_destino:
            await update.message.reply_text("❌ Clique em '✍️ Responder Usuário' no painel do chamado antes de digitar.")
            return
        
        if user_id_destino not in HISTORICO_CONVERSA:
            await update.message.reply_text("❌ O chamado deste usuário já foi encerrado.")
            MODO_RESPOSTA_ADMIN.pop(admin_id, None)
            return
        
        try:
            await context.bot.send_message(
                chat_id=user_id_destino,
                text=f"💬 <b>Suporte:</b> {texto}",
                parse_mode="HTML"
            )
            
            async with LOCK_DADOS:
                atualizar_historico(user_id_destino, 'suporte', texto)
                await atualizar_interface_usuario(context, user_id_destino)
                try:
                    await atualizar_canal_suporte(context, user_id_destino)
                except Exception:
                    pass
            
            await update.message.reply_text(f"✅ Resposta enviada com sucesso para o usuário <code>{user_id_destino}</code>!", parse_mode="HTML")
            
        except Exception as e:
            logger.error(f"Erro ao enviar resposta do admin para {user_id_destino}: {e}")
            await update.message.reply_text(f"❌ Erro ao enviar a mensagem: {e}")
        
        return
    
    if user_id not in HISTORICO_CONVERSA:
        await update.message.reply_text(
            "❌ Você não tem um atendimento ativo.\n\n"
            "Use /start para iniciar um novo atendimento."
        )
        return
    
    async with LOCK_DADOS:
        atualizar_historico(user_id, 'usuario', texto)
        await atualizar_interface_usuario(context, user_id)
        try:
            await atualizar_canal_suporte(context, user_id)
        except Exception:
            pass


# ==================== FUNÇÃO PARA RODAPÉ DOS ALERTAS ====================

def obter_rodape_alerta() -> str:
    """Retorna o rodapé padrão para os alertas automáticos"""
    return (
        "\n\n━━━━━━━━━━━━━━━━\n"
        "🔔 <b>AlertaSUS</b> - Monitoramento de Dados de Saúde\n"
        "📧 <b>Contato:</b> suporte@alertasus.exemplo\n"
        "🤖 <b>Atendimento:</b> @SuporteAlertaSUS_bot\n"
        "💡 <i>Reporte falsos positivos ou falhas pelo bot de atendimento</i>"
    )


# ==================== HANDLERS ====================

handlers = [
    # Comandos
    CommandHandler("start", start),
    CommandHandler("ajuda", menu_ajuda),
    CommandHandler("suporte", menu_suporte),
    CommandHandler("cadastrar_nova", comando_cadastrar_nova),
    CommandHandler("verificar_todos", comando_verificar_todos),
    CommandHandler("verificar_especifico", comando_verificar_especifico),
    CommandHandler("corrigir", comando_corrigir),
    CommandHandler("excluir", comando_excluir),
    CommandHandler("planos", comando_planos),
    CommandHandler("privacidade", comando_privacidade),
    
    # Callbacks dos menus
    CallbackQueryHandler(exibir_resposta_faq, pattern="^faq_"),
    CallbackQueryHandler(iniciar_atendimento, pattern="^iniciar_atendimento$"),
    CallbackQueryHandler(menu_ajuda, pattern="^ajuda$"),
    CallbackQueryHandler(menu_suporte, pattern="^ir_para_suporte$"),
    CallbackQueryHandler(cancelar_atendimento_usuario, pattern="^fechar_menu$"),
    CallbackQueryHandler(cancelar_atendimento_usuario, pattern="^usuario_sair$"),
    
    # Callbacks do canal
    CallbackQueryHandler(callback_botoes_canal, pattern="^(resp_|concluir_)"),
    
    # Handler ÚNICO para mensagens de texto
    MessageHandler(filters.TEXT & ~filters.COMMAND, processar_mensagem),
]