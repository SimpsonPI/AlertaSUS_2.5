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
from handler_ia_atendimento import iniciar_atendimento, tratar_escolha_menu, MENU_PRINCIPAL
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from telegram.request import HTTPXRequest

from config import TELEGRAM_BOT_TOKEN
from handler import (
    comando_planos,
    comando_privacidade,
    comando_verificar_todas,
    callback_ajuda,
    conv_cadastro,
    conv_consulta_especifica,
    conv_corrigir,
    conv_excluir,
    detalhar_plano,
    iniciar_cadastro_manual,
    iniciar_corrigir,
    iniciar_excluir,
    iniciar_verificar_especifico,
    start,
    tratar_menu_interativo,
)
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
from handler_admin import (
    comando_conceder_cortesia,
    comando_remover_cortesia,
)
from handler_pagamento import gerar_pagamento_pix
from suporte import (
    AGUARDANDO_MENSAGEM,
    menu_suporte,
    exibir_resposta_faq,
    iniciar_atendimento_20,
    menu_suporte,
    receber_mensagem_suporte,
)
# Configuração de Logs
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def erro_global_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Captura exceções de timeout e rede sem derrubar o bot."""
    if isinstance(context.error, (TimedOut, NetworkError)):
        logger.warning(
            f"Oscilação de rede com o Telegram capturada: {context.error}"
        )
    else:
        logger.error(
            msg="Exceção capturada pelo bot:",
            exc_info=context.error,
        )


async def registrar_menu_nativo(app):
    """Registra todos os comandos no menu nativo do Telegram e força a atualização."""
    comandos = [
        BotCommand("start", "Menu Principal"),
        BotCommand("cadastrar_nova", "Cadastrar Nova Regulação"),
        BotCommand("verificar_especifico", "Consultar Regulação Específica"),
        BotCommand("verificar_todos", "Verificar Todas as Regulações"),
        BotCommand("corrigir", "Corrigir Dados de Regulação"),
        BotCommand("excluir", "Excluir Regulação"),
        BotCommand("planos", "Ver Planos de Assinatura"),
        BotCommand("privacidade", "Política de Privacidade e LGPD"),
        BotCommand("ajuda", "Central de Atendimento"),
        BotCommand("suporte", "Suporte Técnico"),
        BotCommand("admin", "Painel Administrativo"),
        BotCommand("estatisticas", "Estatísticas do Bot"),
        BotCommand("ativos", "Assinaturas Ativas"),
        BotCommand("dar_plano", "Conceder Plano"),
        BotCommand("bloquear", "Bloquear Usuário"),
        BotCommand("aviso", "Enviar Aviso em Massa"),
    ]

    await app.bot.delete_my_commands(scope=BotCommandScopeAllPrivateChats())
    await app.bot.set_my_commands(
        commands=comandos, scope=BotCommandScopeAllPrivateChats()
    )


def main():
    # Inicialização limpa e padrão do bot
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Adicionando o Handler de Erros Globais
    app.add_error_handler(erro_global_handler)

    # 1. Registro dos ConversationHandlers (Fluxos em etapas)
    app.add_handler(conv_cadastro)
    app.add_handler(conv_consulta_especifica)
    app.add_handler(conv_corrigir)
    app.add_handler(conv_excluir)
    
    # Aqui entra o seu novo fluxo de suporte estruturado por menu e transbordo:
    conv_handler_suporte = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, iniciar_atendimento)],
        states={
            MENU_PRINCIPAL: [CallbackQueryHandler(tratar_escolha_menu)],
        },
        fallbacks=[]
    )
    app.add_handler(conv_handler_suporte)

    # 2. Comandos Principais[cite: 7]
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("iniciar", start))
    app.add_handler(CommandHandler("cadastrar_nova", iniciar_cadastro_manual))
    app.add_handler(CommandHandler("verificar_todos", comando_verificar_todas))
    app.add_handler(
        CommandHandler("verificar_especifico", iniciar_verificar_especifico)
    )
    app.add_handler(CommandHandler("corrigir", iniciar_corrigir))
    app.add_handler(CommandHandler("excluir", iniciar_excluir))
    app.add_handler(CommandHandler("planos", comando_planos))
    app.add_handler(CommandHandler("privacidade", comando_privacidade))
    app.add_handler(CommandHandler("ajuda", menu_suporte))
    app.add_handler(CommandHandler("suporte", menu_suporte))

    # 3. Comandos Administrativos[cite: 7]
    app.add_handler(
        CommandHandler("conceder_cortesia", comando_conceder_cortesia)
    )
    app.add_handler(CommandHandler("cortesia", comando_conceder_cortesia))
    app.add_handler(CommandHandler("conceder", comando_conceder_cortesia))
    app.add_handler(
        CommandHandler("remover_cortesia", comando_remover_cortesia)
    )
    app.add_handler(CommandHandler("remover", comando_remover_cortesia))
    app.add_handler(CommandHandler("admin", comando_menu_admin))
    app.add_handler(CommandHandler("estatisticas", comando_estatisticas))
    app.add_handler(CommandHandler("ativos", comando_listar_ativos))
    app.add_handler(CommandHandler("detalhes", comando_detalhes))
    app.add_handler(CommandHandler("dar_plano", comando_dar_plano))
    app.add_handler(CommandHandler("cortesia", comando_cortesia))
    app.add_handler(CommandHandler("remover_cortesia", comando_remover_cortesia))
    app.add_handler(CommandHandler("bloquear", comando_bloquear))
    app.add_handler(CommandHandler("aviso", comando_aviso))
    app.add_handler(CommandHandler("menu", comando_menu_admin))

    # 4. Callbacks de Botões Inline[cite: 7]
    app.add_handler(CallbackQueryHandler(detalhar_plano, pattern="^plano_"))
    app.add_handler(
        CallbackQueryHandler(gerar_pagamento_pix, pattern="^pix_")
    )
    app.add_handler(CallbackQueryHandler(comando_planos, pattern="^planos$"))
    app.add_handler(CallbackQueryHandler(start, pattern="^iniciar$"))
    app.add_handler(
        CallbackQueryHandler(
            comando_verificar_todas, pattern="^verificar_todos$"
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            comando_privacidade, pattern="^privacidade$"
        )
    )
    app.add_handler(CallbackQueryHandler(exibir_resposta_faq, pattern="^faq_"))
    app.add_handler(CallbackQueryHandler(iniciar_atendimento_20, pattern="^iniciar_atendimento_20$"))
    app.add_handler(CallbackQueryHandler(menu_suporte, pattern="^ajuda$"))

    # Handler genérico de texto para menu interativo caso necessário
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, tratar_menu_interativo))

    # 5. Inicialização e Execução do Bot[cite: 7]
    logger.info("Iniciando o bot AlertaSUS...")
    app.run_polling()


if __name__ == "__main__":
    main()