import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler

logger = logging.getLogger(__name__)

# Definindo os estados da conversação
MENU_PRINCIPAL = 0

async def iniciar_atendimento(update: Update, context):
    """Passo 1: Recebe a mensagem inicial, dá boas-vindas e exibe o menu de opções."""
    if update.message and update.message.from_user.is_bot:
        return

    user_nome = update.effective_user.first_name or "Usuário"
    
    # Teclado inline com as perguntas direcionadas e a opção de atendimento personalizado
    teclado = [
        [InlineKeyboardButton("1️⃣ Como consultar minha regulação?", callback_data="opcao_1")],
        [InlineKeyboardButton("2️⃣ Prazos para exames e consultas", callback_data="opcao_2")],
        [InlineKeyboardButton("3️⃣ Problemas de acesso à plataforma", callback_data="opcao_3")],
        [InlineKeyboardButton("👤 Falar com Atendimento Personalizado", callback_data="personalizado")]
    ]
    reply_markup = InlineKeyboardMarkup(teclado)

    texto_boas_vindas = (
        f"Olá, <b>{user_nome}</b>! Seja bem-vindo ao suporte do AlertaSUS 2.0.\n\n"
        "Para agilizar o seu atendimento, escolha uma das opções abaixo clicando em um dos botões:"
    )

    if update.message:
        await update.message.reply_text(texto_boas_vindas, reply_markup=reply_markup, parse_mode="HTML")
    
    return MENU_PRINCIPAL

async def tratar_escolha_menu(update: Update, context):
    """Passo 2: Processa a alternativa escolhida e exibe a resposta automática correspondente."""
    query = update.callback_query
    await query.answer()
    
    dados = query.data

    # Teclado para retornar ao menu ou encerrar
    teclado_voltar = [
        [InlineKeyboardButton("⬅️ Voltar ao Menu", callback_data="voltar_menu"),
         InlineKeyboardButton("👤 Atendimento Personalizado", callback_data="personalizado")]
    ]
    reply_markup = InlineKeyboardMarkup(teclado_voltar)

    if dados == "opcao_1":
        resposta = (
            "📌 <b>Como consultar sua regulação:</b>\n\n"
            "Você pode acompanhar o status da sua regulação diretamente pelo menu principal do AlertaSUS inserindo o seu cartão SUS ou CPF."
        )
    elif dados == "opcao_2":
        resposta = (
            "📌 <b>Prazos para exames e consultas:</b>\n\n"
            "Os prazos variam conforme a prioridade médica definida na rede pública. Casos urgentes são priorizados pela central de regulação do estado."
        )
    elif dados == "opcao_3":
        resposta = (
            "📌 <b>Problemas de acesso:</b>\n\n"
            "Caso esteja com falhas para entrar, tente redefinir sua senha na tela de login ou limpe os dados de navegação do seu aplicativo."
        )
    elif dados == "voltar_menu":
        return await iniciar_atendimento_callback(query)
    elif dados == "personalizado":
        return await transbordo_para_atendente(query, context)
    else:
        resposta = "Opção inválida."

    await query.edit_message_text(text=resposta, reply_markup=reply_markup, parse_mode="HTML")
    return MENU_PRINCIPAL

async def iniciar_atendimento_callback(query):
    """Auxiliar para reiniciar o menu via callback."""
    teclado = [
        [InlineKeyboardButton("1️⃣ Como consultar minha regulação?", callback_data="opcao_1")],
        [InlineKeyboardButton("2️⃣ Prazos para exames e consultas", callback_data="opcao_2")],
        [InlineKeyboardButton("3️⃣ Problemas de acesso à plataforma", callback_data="opcao_3")],
        [InlineKeyboardButton("👤 Falar com Atendimento Personalizado", callback_data="personalizado")]
    ]
    await query.edit_message_text(
        text="Escolha uma das opções abaixo:",
        reply_markup=InlineKeyboardMarkup(teclado),
        parse_mode="HTML"
    )
    return MENU_PRINCIPAL

async def transbordo_para_atendimento(query, context):
    """Passo 4: Encaminha para o atendimento personalizado."""
    user = query.from_user
    user_nome = user.first_name or "Usuário"
    user_id = user.id
    username = f"@{user.username}" if user.username else "Sem username"

    await query.edit_message_text(
        text="✅ <b>Solicitação registrada!</b>\n\n"
             "Aguarde, em breve você receberá atendimento personalizado da nossa equipe por aqui.",
        parse_mode="HTML"
    )

    logger.info(f"🚨 TRANSBORDO SOLICITADO - Usuário: {user_nome} ({username}) | ID: {user_id}")
    
    return ConversationHandler.END