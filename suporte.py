from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
import logging
from handler_ia_atendimento import iniciar_atendimento, tratar_escolha_menu, MENU_PRINCIPAL

# Configuração de logger
logger = logging.getLogger(__name__)

# Constante de estado para o ConversationHandler
AGUARDANDO_MENSAGEM = 1


async def menu_ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu Inicial da Central de Ajuda (FAQ interativo)."""
    texto = (
        "🤖 <b>Central de Atendimento ao Usuário AlertaSUS 2.0</b>\n\n"
        "Seja bem-vindo(a) ao nosso centro de ajuda! Selecione abaixo uma das perguntas frequentes para tirar sua dúvida instantaneamente:\n\n"
        "<b>📌 Perguntas Frequentes (FAQ):</b>\n"
        "1️⃣ Como cadastrar uma regulação?\n"
        "2️⃣ Como consultar minhas regulações ativas?\n"
        "3️⃣ Onde encontrar o número do Cartão SUS ou ID?\n"
        "4️⃣ Como alterar meus dados de cadastro?\n"
        "5️⃣ Como renovar ou alterar meu plano de assinatura?"
    )

    teclado = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("1️⃣ Cadastrar Regulação", callback_data="faq_cadastrar"),
            InlineKeyboardButton("2️⃣ Consultar Regulações", callback_data="faq_consultar"),
        ],
        [
            InlineKeyboardButton("3️⃣ Onde achar Cartão SUS/ID", callback_data="faq_id"),
            InlineKeyboardButton("4️⃣ Alterar Dados", callback_data="faq_alterar"),
        ],
        [
            InlineKeyboardButton("5️⃣ Planos e Assinatura", callback_data="faq_planos"),
        ],
        [
            InlineKeyboardButton(
                "💬 Não encontrou sua resposta? Ir para o Suporte",
                callback_data="ir_para_suporte",
            )
        ],
        [InlineKeyboardButton("❌ Fechar", callback_data="fechar_menu")],
    ])

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            texto, parse_mode="HTML", reply_markup=teclado
        )
    elif update.message:
        await update.message.reply_text(
            texto, parse_mode="HTML", reply_markup=teclado
        )


async def menu_suporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu exclusivo para a Central de Suporte e Atendimento."""
    texto = (
        "🎧 <b>Central de Suporte e Atendimento AlertaSUS 2.0</b>\n\n"
        "Não encontrou o que precisava na central de ajuda ou está enfrentando algum problema técnico? "
        "Clique no botão abaixo para ir direto para o nosso Bot de Atendimento:"
    )

    teclado = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎧 Atendimento AlertaSUS", url="https://t.me/meu_atendimento_123_bot")],
        [InlineKeyboardButton("📖 Voltar para a Central de Ajuda", callback_data="ajuda")],
        [InlineKeyboardButton("❌ Fechar", callback_data="fechar_menu")],
    ])

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.message.edit_text(texto, parse_mode="HTML", reply_markup=teclado)
    elif update.message:
        await update.message.reply_text(texto, parse_mode="HTML", reply_markup=teclado)


async def exibir_resposta_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Exibe as respostas individuais do FAQ com botão para voltar ao menu ou ir ao Suporte."""
    query = update.callback_query
    await query.answer()

    dados = query.data

    respostas = {
        "faq_cadastrar": (
            "📌 <b>Como cadastrar uma nova regulação?</b>\n\n"
            "• Utilize o comando <b>/cadastrar_nova</b> no menu do bot.\n"
            "• Digite o número do seu <b>Cartão SUS</b> (15 dígitos) ou o <b>ID da Regulação</b> solicitado.\n"
            "• Siga as instruções na tela até a confirmação do cadastro."
        ),
        "faq_consultar": (
            "🔍 <b>Como consultar minhas regulações?</b>\n\n"
            "• Para ver todas as suas regulações: digite <b>/verificar_todos</b>.\n"
            "• Para consultar uma regulação específica: digite <b>/verificar_especifico</b>."
        ),
        "faq_id": (
            "🆔 <b>Onde encontrar o Cartão SUS ou ID da Regulação?</b>\n\n"
            "• <b>Cartão SUS:</b> O número possui 15 dígitos e pode ser encontrado no seu cartão impresso ou no aplicativo 'Meu SUS Digital'.\n"
            "• <b>ID da Regulação:</b> É o código de identificação fornecido pelo posto de saúde ou hospital no momento da solicitação do procedimento."
        ),
        "faq_alterar": (
            "✏️ <b>Como corrigir ou alterar dados?</b>\n\n"
            "• Para alterar informações de uma regulação já cadastrada, utilize o comando <b>/corrigir</b> e selecione o registro desejado."
        ),
        "faq_planos": (
            "💳 <b>Planos e Renovação de Assinatura</b>\n\n"
            "• Para verificar seus planos ativos, renovar ou fazer um upgrade, acesse o comando <b>/planos</b> no menu principal."
        ),
    }

    texto_resposta = respostas.get(
        dados, "Informação não encontrada no FAQ."
    )
    texto_resposta += "\n\nSua dúvida foi resolvida? Se ainda precisar de suporte personalizado:"

    teclado = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📋 Abrir Chamado de Suporte",
                callback_data="iniciar_atendimento_20",
            )
        ],
        [InlineKeyboardButton("⬅️ Voltar ao FAQ", callback_data="ajuda")],
    ])

    await query.edit_message_text(
        texto_resposta, parse_mode="HTML", reply_markup=teclado
    )


async def iniciar_atendimento_20(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # O bot envia a mensagem pedindo para o usuário digitar a demanda
    await query.edit_message_text(
        text="🎧 <b>Atendimento Personalizado AlertaSUS</b>\n\n"
             "Olá! Escreva abaixo a sua dúvida ou demanda para que nossa equipe possa te ajudar:",
        parse_mode="HTML"
    )

    # IMPORTANTE: Retorna o estado que avisa o bot para esperar o texto do usuário
    return AGUARDANDO_MENSAGEM

    teclado = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Voltar ao Suporte", callback_data="suporte_menu")],
        [InlineKeyboardButton("❌ Fechar", callback_data="fechar_menu")],
    ])

    await query.edit_message_text(
        mensagem, parse_mode="HTML", reply_markup=teclado
    )

    return AGUARDANDO_MENSAGEM


async def receber_mensagem_suporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    texto_usuario = update.message.text
    
    # ID fixo do seu canal de suporte que testamos
    CANAL_SUPORTE_ID = -1004479965268

    try:
        # Envia a mensagem diretamente para o canal do Telegram
        await context.bot.send_message(
            chat_id=CANAL_SUPORTE_ID,
            text=(
                f"🚨 <b>NOVO CHAMADO DE SUPORTE</b>\n\n"
                f"• <b>Usuário:</b> {user.full_name} (@{user.username or 'Sem username'})\n"
                f"• <b>ID do Telegram:</b> <code>{user.id}</code>\n\n"
                f"• <b>Mensagem do usuário:</b>\n{texto_usuario}"
            ),
            parse_mode="HTML"
        )
        
        # Responde para o usuário que deu certo
        await update.message.reply_text(
            "✅ Sua mensagem foi enviada com sucesso para nossa equipe! Aguarde que já vamos te atender."
        )
    except Exception as e:
        print(f"ERRO AO ENVIAR PARA O CANAL: {e}")

    return ConversationHandler.END


async def cancelar_suporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela ou fecha o fluxo de atendimento."""
    texto = "❌ Atendimento encerrado. Se precisar de algo, acesse o menu novamente!"

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(texto)
    elif update.message:
        await update.message.reply_text(texto)

    return ConversationHandler.END


# Declaração correta e única do fluxo conversacional do suporte
conv_suporte = ConversationHandler(
    entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, iniciar_atendimento)],
    states={
        MENU_PRINCIPAL: [
            CallbackQueryHandler(tratar_escolha_menu),
            CallbackQueryHandler(exibir_resposta_faq, pattern="^faq_"),
            CallbackQueryHandler(iniciar_atendimento_20, pattern="^iniciar_atendimento_20$"),
            CallbackQueryHandler(menu_ajuda, pattern="^ajuda$"),
            CallbackQueryHandler(menu_suporte, pattern="^(suporte_menu|ir_para_suporte)$"),
            CallbackQueryHandler(cancelar_suporte, pattern="^fechar_menu$"),
        ],
    },
    fallbacks=[]
)


# =====================================================================
# FUNÇÕES DE AUTOATENDIMENTO PARA OS COMANDOS DO BOT
# =====================================================================

async def comando_cadastrar_nova(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde ao comando /cadastrar_nova."""
    await update.message.reply_text(
        "📌 <b>Novo Cadastro de Regulação</b>\n\n"
        "Utilizado para realizar o cadastro de uma nova regulação no sistema, "
        "solicitando o número do Cartão SUS (15 dígitos) ou o ID da Regulação.",
        parse_mode="HTML"
    )


async def comando_verificar_todos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde ao comando /verificar_todos."""
    await update.message.reply_text(
        "🔍 <b>Consultar Regulações Ativas</b>\n\n"
        "Permite que o usuário consulte e visualize a lista completa de todas as suas regulações ativas no sistema.",
        parse_mode="HTML"
    )


async def comando_verificar_especifico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde ao comando /verificar_especifico."""
    await update.message.reply_text(
        "🔍 <b>Consulta Específica</b>\n\n"
        "Utilizado para consultar os detalhes de uma regulação específica.",
        parse_mode="HTML"
    )


async def comando_corrigir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde ao comando /corrigir."""
    await update.message.reply_text(
        "✏️ <b>Correção de Cadastro</b>\n\n"
        "Destinado à alteração ou correção de informações de uma regulação já cadastrada anteriormente.",
        parse_mode="HTML"
    )


async def comando_excluir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde ao comando /excluir."""
    await update.message.reply_text(
        "🗑️ <b>Exclusão de Regulação</b>\n\n"
        "Utilizado para deletar o ID de regulação cadastrado pelo usuário, "
        "apagando permanentemente o registro junto com todos os dados que constavam no cadastro.",
        parse_mode="HTML"
    )


async def comando_planos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde ao comando /planos."""
    await update.message.reply_text(
        "💳 <b>Planos e Assinaturas - AlertaSUS 2.0</b>\n\n"
        "Permite que o usuário visualize os planos disponíveis para contratação, "
        "verifique o plano de assinatura ativo, realize renovações ou solicite upgrades na plataforma.",
        parse_mode="HTML"
    )


async def comando_privacidade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde ao comando /privacidade."""
    await update.message.reply_text(
        "🔒 <b>Política de Privacidade - AlertaSUS 2.0</b>\n\n"
        "Exibe as diretrizes de privacidade e termos sobre o tratamento e proteção de dados do usuário.",
        parse_mode="HTML"
    )