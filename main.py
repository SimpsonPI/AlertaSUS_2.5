from admin import (
    comando_estatisticas,
    comando_listar_ativos,
    comando_bloquear,
    comando_detalhes,
    comando_dar_plano,
    comando_cortesia,
    comando_remover_cortesia,
    comando_aviso,
    comando_menu_admin,
)
import logging
from telegram import BotCommand, BotCommandScopeAllPrivateChats
from telegram.error import NetworkError, TimedOut
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from config import TELEGRAM_BOT_TOKEN
from handler import (
    comando_planos,
    comando_privacidade,
    comando_verificar_todas,
    comando_ajuda,
    # comando_suporte foi removido daqui
    callback_ajuda,
    faq_o_que_e,
    faq_rastrear,
    faq_seguranca,
    faq_corrigir,
    detalhar_plano,
    voltar_ajuda,
    conv_cadastro,
    conv_consulta_especifica,
    conv_excluir,
    iniciar_cadastro_manual,
    iniciar_corrigir,
    iniciar_excluir,
    iniciar_verificar_especifico,
    start,
    callback_faq_suporte,
    callback_privacidade_voltar,
)
from handler_gestao import (
    selecionar_regulacao_callback,
    selecionar_campo_callback,
    salvar_novo_valor,
)
from handler_admin import (
    comando_conceder_cortesia,
    comando_remover_cortesia,
)
from handler_pagamento import gerar_pagamento_pix

# === IMPORTAÇÃO CORRETA DO SUPORTE ===
from suporte import menu_suporte 

from utils import (
    SELECIONAR_REGULACAO,
    SELECIONAR_CAMPO,
    AGUARDAR_NOVO_VALOR,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

async def erro_global_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(context.error, (TimedOut, NetworkError)):
        logger.warning(f"Oscilação de rede com o Telegram capturada: {context.error}")
    else:
        logger.error(msg="Exceção capturada pelo bot:", exc_info=context.error)

async def registrar_menu_nativo(app):
    comandos = [
        BotCommand("start", "Menu Principal"),
        BotCommand("cadastrar_nova", "Cadastrar Nova Regulação"),
        BotCommand("verificar_especifico", "Consultar Regulação Específica"),
        BotCommand("verificar_todos", "Verificar Todas as Regulações"),
        BotCommand("corrigir", "Corrigir Dados de Regulação"),
        BotCommand("excluir", "Excluir Regulação"),
        BotCommand("planos", "Ver Planos de Assinatura"),
        BotCommand("privacidade", "Política de Privacidade e LGPD"),
        BotCommand("ajuda", "Central de Ajuda e FAQ"),
        BotCommand("suporte", "Falar com o Suporte"),
        BotCommand("admin", "Painel Administrativo"),
    ]
    await app.bot.delete_my_commands(scope=BotCommandScopeAllPrivateChats())
    await app.bot.set_my_commands(commands=comandos, scope=BotCommandScopeAllPrivateChats())

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_error_handler(erro_global_handler)

    conv_corrigir = ConversationHandler(
        entry_points=[
            CommandHandler("corrigir", iniciar_corrigir),
            CallbackQueryHandler(selecionar_regulacao_callback, pattern="^corr_reg_")
        ],
        states={
            SELECIONAR_REGULACAO: [CallbackQueryHandler(selecionar_regulacao_callback, pattern="^corr_reg_")],
            SELECIONAR_CAMPO: [CallbackQueryHandler(selecionar_campo_callback, pattern="^corr_campo_")],
            AGUARDAR_NOVO_VALOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, salvar_novo_valor)],
        },
        fallbacks=[CallbackQueryHandler(selecionar_regulacao_callback, pattern="^cancelar_corr$")],
    )

    app.add_handler(conv_cadastro)
    app.add_handler(conv_consulta_especifica)
    app.add_handler(conv_corrigir)
    app.add_handler(conv_excluir)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("iniciar", start))
    app.add_handler(CommandHandler("cadastrar_nova", iniciar_cadastro_manual))
    app.add_handler(CommandHandler("verificar_todos", comando_verificar_todas))
    app.add_handler(CommandHandler("verificar_especifico", iniciar_verificar_especifico))
    app.add_handler(CommandHandler("corrigir", iniciar_corrigir))
    app.add_handler(CommandHandler("excluir", iniciar_excluir))
    app.add_handler(CommandHandler("planos", comando_planos))
    app.add_handler(CommandHandler("privacidade", comando_privacidade))
    app.add_handler(CommandHandler("ajuda", comando_ajuda))
    
    # === REGISTRO ATUALIZADO DO SUPORTE ===
    app.add_handler(CommandHandler("suporte", menu_suporte))

    app.add_handler(CommandHandler("conceder_cortesia", comando_conceder_cortesia))
    app.add_handler(CommandHandler("admin", comando_menu_admin))
    app.add_handler(CommandHandler("estatisticas", comando_estatisticas))
    app.add_handler(CommandHandler("ativos", comando_listar_ativos))
    app.add_handler(CommandHandler("detalhes", comando_detalhes))
    app.add_handler(CommandHandler("dar_plano", comando_dar_plano))
    app.add_handler(CommandHandler("bloquear", comando_bloquear))
    app.add_handler(CommandHandler("aviso", comando_aviso))

    app.add_handler(CallbackQueryHandler(detalhar_plano, pattern="^plano_"))
    app.add_handler(CallbackQueryHandler(gerar_pagamento_pix, pattern="^pix_"))
    app.add_handler(CallbackQueryHandler(comando_planos, pattern="^planos$"))
    app.add_handler(CallbackQueryHandler(start, pattern="^iniciar$"))
    app.add_handler(CallbackQueryHandler(callback_faq_suporte, pattern="^abrir_faq_suporte$"))
    app.add_handler(CallbackQueryHandler(callback_privacidade_voltar, pattern="^privacidade_voltar$"))
    app.add_handler(CallbackQueryHandler(callback_ajuda, pattern="^ajuda$"))
    app.add_handler(CallbackQueryHandler(faq_o_que_e, pattern="^faq_o_que_e$"))
    app.add_handler(CallbackQueryHandler(faq_rastrear, pattern="^faq_rastrear$"))
    app.add_handler(CallbackQueryHandler(faq_seguranca, pattern="^faq_seguranca$"))
    app.add_handler(CallbackQueryHandler(faq_corrigir, pattern="^faq_corrigir$"))
    app.add_handler(CallbackQueryHandler(voltar_ajuda, pattern="^voltar_ajuda$"))
    app.add_handler(CallbackQueryHandler(comando_verificar_todas, pattern="^verificar_todos$"))
    app.add_handler(CallbackQueryHandler(comando_privacidade, pattern="^privacidade$"))

    logger.info("Iniciando o bot AlertaSUS...")
    app.run_polling(drop_pending_updates=True, allowed_updates=["message", "callback_query"])