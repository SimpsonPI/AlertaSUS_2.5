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

# Constantes de estados
AGUARDANDO_MENSAGEM = 1
AGUARDANDO_RESPOSTA_ADMIN = 2

# Dicionários para gerenciar os chamados e o histórico de mensagens:
# CHAMADOS_ATIVOS = {user_id: message_id_no_canal}
CHAMADOS_ATIVOS = {}
# HISTORICO_MENSAGENS = {user_id: [lista_de_mensagens]}
HISTORICO_MENSAGENS = {}


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

    teclado_usuario = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Encerrar Atendimento", callback_data="usuario_sair")]
    ])

    await query.edit_message_text(
        text="🎧 <b>Atendimento Personalizado AlertaSUS</b>\n\n"
             "Olá! Escreva abaixo a sua dúvida ou demanda para que nossa equipe possa te ajudar:",
        parse_mode="HTML",
        reply_markup=teclado_usuario
    )

    return AGUARDANDO_MENSAGEM


async def receber_mensagem_suporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    texto_usuario = update.message.text
    CANAL_SUPORTE_ID = -1004479965268

    # Inicializa ou adiciona ao histórico do usuário
    if user.id not in HISTORICO_MENSAGENS:
        HISTORICO_MENSAGENS[user.id] = []
    
    HISTORICO_MENSAGENS[user.id].append(texto_usuario)

    # Monta o histórico acumulado (exibe todas as mensagens enviadas)
    historico_texto = "\n".join([f"• <i>{msg}</i>" for msg in HISTORICO_MENSAGENS[user.id]])

    teclado_canal = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✍️ Responder Usuário", callback_data=f"resp_{user.id}"),
            InlineKeyboardButton("✅ Concluir Chamado", callback_data=f"concluir_{user.id}")
        ]
    ])

    texto_chamado = (
        f"🚨 <b>CHAMADO DE SUPORTE ATIVO</b>\n\n"
        f"• <b>Usuário:</b> {user.full_name} (@{user.username or 'Sem username'})\n"
        f"• <b>ID do Telegram:</b> <code>{user.id}</code>\n\n"
        f"• <b>Mensagens do Usuário:</b>\n{historico_texto}"
    )

    try:
        if user.id in CHAMADOS_ATIVOS:
            msg_id_canal = CHAMADOS_ATIVOS[user.id]
            try:
                # Atualiza a mensagem existente no canal somando o histórico
                await context.bot.edit_message_text(
                    chat_id=CANAL_SUPORTE_ID,
                    message_id=msg_id_canal,
                    text=texto_chamado,
                    parse_mode="HTML",
                    reply_markup=teclado_canal
                )
            except Exception:
                nova_msg = await context.bot.send_message(
                    chat_id=CANAL_SUPORTE_ID, text=texto_chamado, parse_mode="HTML", reply_markup=teclado_canal
                )
                CHAMADOS_ATIVOS[user.id] = nova_msg.message_id
        else:
            nova_msg = await context.bot.send_message(
                chat_id=CANAL_SUPORTE_ID, text=texto_chamado, parse_mode="HTML", reply_markup=teclado_canal
            )
            CHAMADOS_ATIVOS[user.id] = nova_msg.message_id
        
        teclado_usuario = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Encerrar Atendimento", callback_data="usuario_sair")]
        ])

        await update.message.reply_text(
            "✅ Mensagem enviada para a equipe! Pode continuar digitando se precisar.",
            reply_markup=teclado_usuario
        )
    except Exception as e:
        print(f"ERRO AO ENVIAR/ATUALIZAR NO CANAL: {e}")

    return AGUARDANDO_MENSAGEM


async def cancelar_suporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Encerra o atendimento a pedido do usuário."""
    user = update.effective_user
    query = update.callback_query
    
    if user:
        CHAMADOS_ATIVOS.pop(user.id, None)
        HISTORICO_MENSAGENS.pop(user.id, None)

    if query:
        await query.answer()
        await query.edit_message_text("❌ Atendimento encerrado. Se precisar de algo, acesse o menu novamente!")
    elif update.message:
        await update.message.reply_text("❌ Atendimento encerrado. Se precisar de algo, acesse o menu novamente!")

    return ConversationHandler.END


async def botao_canal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("resp_"):
        user_id = data.split("_")[1]
        context.user_data["atendendo_user_id"] = user_id
        
        await query.message.reply_text(
            f"✍️ <b>Modo de Resposta Ativado</b> para o ID: <code>{user_id}</code>\n\n"
            "Digite a mensagem que deseja enviar para este usuário agora:",
            parse_mode="HTML"
        )
        return AGUARDANDO_RESPOSTA_ADMIN

    elif data.startswith("concluir_"):
        user_id_str = data.split("_")[1]
        user_id = int(user_id_str)
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="✅ O seu chamado foi concluído pela equipe de suporte. Obrigado por utilizar o AlertaSUS!"
            )
        except Exception as e:
            print(f"Erro ao avisar usuário sobre conclusão: {e}")

        # Limpa dos registros ativos e histórico
        CHAMADOS_ATIVOS.pop(user_id, None)
        HISTORICO_MENSAGENS.pop(user_id, None)

        await query.edit_message_text(
            text=query.message.text + "\n\n<b>[✅ CHAMADO CONCLUÍDO]</b>",
            parse_mode="HTML",
            reply_markup=None
        )


async def enviar_resposta_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id_str = context.user_data.get("atendendo_user_id")
    resposta = update.message.text

    if not user_id_str:
        await update.message.reply_text("⚠️ Nenhum usuário selecionado para resposta.")
        return ConversationHandler.END

    user_id = int(user_id_str)

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"💬 <b>Suporte AlertaSUS:</b>\n\n{resposta}",
            parse_mode="HTML"
        )
        await update.message.reply_text("✅ Resposta enviada com sucesso para o usuário!")
    except Exception as e:
        await update.message.reply_text(f"❌ Erro ao enviar resposta: {e}")

    context.user_data.pop("atendendo_user_id", None)
    return ConversationHandler.END


# Declaração do ConversationHandler
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
        AGUARDANDO_MENSAGEM: [
            CallbackQueryHandler(cancelar_suporte, pattern="^usuario_sair$"),
            CommandHandler("sair", cancelar_suporte),
            MessageHandler(filters.TEXT & ~filters.COMMAND, receber_mensagem_suporte)
        ],
    },
    fallbacks=[]
)


# Funções de autoatendimento para os comandos do bot
async def comando_cadastrar_nova(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📌 Novo Cadastro de Regulação", parse_mode="HTML")

async def comando_verificar_todos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Consultar Regulações Ativas", parse_mode="HTML")

async def comando_verificar_especifico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Consulta Específica", parse_mode="HTML")

async def comando_corrigir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✏️ Correção de Cadastro", parse_mode="HTML")

async def comando_excluir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🗑️ Exclusão de Regulação", parse_mode="HTML")

async def comando_planos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💳 Planos e Assinaturas", parse_mode="HTML")

async def comando_privacidade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔒 Política de Privacidade", parse_mode="HTML")