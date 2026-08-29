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
    comando_ajuda,
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
from suporte import menu_suporte 
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

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

async def erro_global_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Exceção capturada pelo bot:", exc_info=context.error)

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
    app.add_handler(CallbackQueryHandler(CallbackQueryHandler, pattern="^ajuda$"))
    app.add_handler(CallbackQueryHandler(faq_o_que_e, pattern="^faq_o_que_e$"))
    app.add_handler(CallbackQueryHandler(faq_rastrear, pattern="^faq_rastrear$"))
    app.add_handler(CallbackQueryHandler(faq_seguranca, pattern="^faq_seguranca$"))
    app.add_handler(CallbackGroup := CallbackQueryHandler(faq_corrigir, pattern="^faq_corrigir$"))
    app.add_handler(CallbackQueryHandler(voltar_ajuda, pattern="^voltar_ajuda$"))
    app.add_handler(CallbackQueryHandler(comando_verificar_todas, pattern="^verificar_todos$"))
    app.add_handler(CallbackQueryHandler(comando_privacidade, pattern="^privacidade$"))

    # Configuração de Webhook para Railway
    PORT = int(os.environ.get("PORT", "8080"))
    RAILWAY_STATIC_URL = os.environ.get("RAILWAY_STATIC_URL") or os.environ.get("RAILWAY_PUBLIC_DOMAIN")

    if RAILWAY_STATIC_URL:
        if not RAILWAY_STATIC_URL.startswith("https://"):
            webhook_url = f"https://{RAILWAY_STATIC_URL}/{TELEGRAM_BOT_TOKEN}"
        else:
            webhook_url = f"{RAILWay_STATIC_URL}/{TELEGRAM_BOT_TOKEN}" if 'RAILWay_STATIC_URL' in locals() else f"{RAILWAY_STATIC_URL}/{TELEGRAM_BOT_TOKEN}"
            
        logger.info(f"Iniciando bot via Webhook em porta {PORT} com URL: {webhook_url}")
        
        # Inicia o webhook com o servidor embutido do PTB
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            secret_token="alertasus_secret_token_secure",
            webhook_url=webhook_url,
        )
    else:
        logger.error("ERRO CRITICO: Nenhuma URL do Railway encontrada! Verifique as variaveis de ambiente.")
        app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

    # Bloco final da funcao main()
    PORT = int(os.environ.get("PORT", "8080"))
    
    import threading
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class SimpleHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot AlertaSUS 2.5 is running via Polling!")

    def run_http_server(port):
        server = HTTPServer(("0.0.0.0", port), SimpleHandler)
        server.serve_forever()

    threading.Thread(target=run_http_server, args=(PORT,), daemon=True).start()
    logger.info(f"Servidor HTTP auxiliar rodando na porta {PORT}")

    logger.info("Iniciando o bot AlertaSUS via polling...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()