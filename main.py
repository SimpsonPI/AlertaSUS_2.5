import os
import logging
from telegram import BotCommand, BotCommandScopeAllPrivateChats
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
    comando_suporte,
    detalhar_plano,
    conv_cadastro,
    conv_consulta_especifica,
    conv_excluir,
    iniciar_cadastro_manual,
    iniciar_corrigir,
    iniciar_excluir,
    iniciar_verificar_especifico,
    start,
    faq_cadastrar,
    faq_consultar,
    faq_id,
    faq_alterar,
    faq_planos,
    faq_governo,
)
from handler_gestao import (
    selecionar_regulacao_callback,
    selecionar_campo_callback,
    salvar_novo_valor,
)
from handler_pagamento import gerar_pagamento_pix
from utils import (
    SELECIONAR_REGULACAO,
    SELECIONAR_CAMPO,
    AGUARDAR_NOVO_VALOR,
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

# ═══════════════════════════════════════════════════════════════
# NOVOS IMPORTS — ATENDIMENTO AO CLIENTE
# ═══════════════════════════════════════════════════════════════
from handler_atendimento import (
    menu_atendimento,
    iniciar_faq,
    processar_pergunta_faq,
    iniciar_atendimento_humanizado,
    processar_mensagem_humanizado,
    ver_meus_chamados,
    comando_ver_chamados,
    comando_responder_chamado,
    AGUARDANDO_MENSAGEM_CHAMADO,
    cancelar_atendimento,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

async def erro_global_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Exceção capturada pelo bot:", exc_info=context.error)

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN") or TELEGRAM_BOT_TOKEN
    app = ApplicationBuilder().token(token).build()
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

    # ═══════════════════════════════════════════════════════════════
    # NOVO — CONVERSATION HANDLER PARA ATENDIMENTO HUMANIZADO
    # ═══════════════════════════════════════════════════════════════
    conv_atendimento_humanizado = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(iniciar_atendimento_humanizado, pattern="^atendimento_humanizado$"),
            CommandHandler("atendimento_humanizado", iniciar_atendimento_humanizado),
        ],
        states={
            AGUARDANDO_MENSAGEM_CHAMADO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, processar_mensagem_humanizado)
            ],
        },
        fallbacks=[
            CommandHandler("cancelar", cancelar_atendimento),
            CallbackQueryHandler(cancelar_atendimento, pattern="^cancelar_atendimento$"),
        ],
        per_message=False,
    )

    app.add_handler(conv_cadastro)
    app.add_handler(conv_consulta_especifica)
    app.add_handler(conv_corrigir)
    app.add_handler(conv_excluir)
    # ═══════════════════════════════════════════════════════════════
    # NOVO — ADICIONA O CONVERSATION HANDLER DE ATENDIMENTO
    # ═══════════════════════════════════════════════════════════════
    app.add_handler(conv_atendimento_humanizado)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("iniciar", start))
    app.add_handler(CommandHandler("menu", start))
    app.add_handler(CommandHandler("cadastrar_nova", iniciar_cadastro_manual))
    app.add_handler(CommandHandler("verificar_todos", comando_verificar_todas))
    app.add_handler(CommandHandler("verificar_especifico", iniciar_verificar_especifico))
    app.add_handler(CommandHandler("corrigir", iniciar_corrigir))
    app.add_handler(CommandHandler("excluir", iniciar_excluir))
    app.add_handler(CommandHandler("planos", comando_planos))
    app.add_handler(CommandHandler("privacidade", comando_privacidade))
    app.add_handler(CommandHandler("suporte", comando_suporte))  # <-- AJUSTADO

    # ═══════════════════════════════════════════════════════════════
    # NOVOS COMANDOS — ATENDIMENTO AO CLIENTE
    # ═══════════════════════════════════════════════════════════════
    app.add_handler(CommandHandler("atendimento", menu_atendimento))
    app.add_handler(CommandHandler("faq", iniciar_faq))
    app.add_handler(CommandHandler("chamados", comando_ver_chamados))
    app.add_handler(CommandHandler("responder", comando_responder_chamado))

    # Comandos Administrativos unificados do admin.py
    app.add_handler(CommandHandler("admin", comando_menu_admin))
    app.add_handler(CommandHandler("menu_admin", comando_menu_admin))
    app.add_handler(CommandHandler("estatisticas", comando_estatisticas))
    app.add_handler(CommandHandler("ativos", comando_listar_ativos))
    app.add_handler(CommandHandler("detalhes", comando_detalhes))
    app.add_handler(CommandHandler("dar_plano", comando_dar_plano))
    app.add_handler(CommandHandler("cortesia", comando_cortesia))
    app.add_handler(CommandHandler("remover_cortesia", comando_remover_cortesia))
    app.add_handler(CommandHandler("bloquear", comando_bloquear))
    app.add_handler(CommandHandler("aviso", comando_aviso))

    app.add_handler(CallbackQueryHandler(detalhar_plano, pattern="^plano_"))
    app.add_handler(CallbackQueryHandler(gerar_pagamento_pix, pattern="^pix_"))
    app.add_handler(CallbackQueryHandler(comando_planos, pattern="^planos$"))
    app.add_handler(CallbackQueryHandler(start, pattern="^iniciar$"))

    # ═══════════════════════════════════════════════════════════════
    # NOVOS CALLBACKS — FAQ DO SUPORTE
    # ═══════════════════════════════════════════════════════════════
    app.add_handler(CallbackQueryHandler(faq_cadastrar, pattern="^faq_cadastrar$"))
    app.add_handler(CallbackQueryHandler(faq_consultar, pattern="^faq_consultar$"))
    app.add_handler(CallbackQueryHandler(faq_id, pattern="^faq_id$"))
    app.add_handler(CallbackQueryHandler(faq_alterar, pattern="^faq_alterar$"))
    app.add_handler(CallbackQueryHandler(faq_planos, pattern="^faq_planos$"))
    app.add_handler(CallbackQueryHandler(faq_governo, pattern="^faq_governo$"))

    # ═══════════════════════════════════════════════════════════════
    # NOVOS CALLBACKS — ATENDIMENTO AO CLIENTE
    # ═══════════════════════════════════════════════════════════════
    app.add_handler(CallbackQueryHandler(menu_atendimento, pattern="^atendimento_menu$"))
    app.add_handler(CallbackQueryHandler(iniciar_faq, pattern="^atendimento_faq$"))
    app.add_handler(CallbackQueryHandler(iniciar_atendimento_humanizado, pattern="^atendimento_humanizado$"))
    app.add_handler(CallbackQueryHandler(ver_meus_chamados, pattern="^ver_chamados$"))
    app.add_handler(CallbackQueryHandler(menu_atendimento, pattern="^atendimento_email$"))
    app.add_handler(CallbackQueryHandler(cancelar_atendimento, pattern="^cancelar_atendimento$"))
    
    # Handler para processar perguntas do FAQ quando o usuário digita texto
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, processar_pergunta_faq),
        group=1
    )

    # Servidor HTTP auxiliar para o Railway manter a porta aberta e execução via Polling
    PORT = int(os.environ.get("PORT", "8080"))
    
    import threading
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class SimpleHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot AlertaSUS 2.5 is running!")

    def run_http_server(port):
        server = HTTPServer(("0.0.0.0", port), SimpleHandler)
        server.serve_forever()

    threading.Thread(target=run_http_server, args=(PORT,), daemon=True).start()
    logger.info(f"Servidor HTTP auxiliar rodando na porta {PORT}")

    logger.info("Iniciando o bot AlertaSUS via polling...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
