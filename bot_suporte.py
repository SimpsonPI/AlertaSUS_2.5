import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from suporte import (
    conv_suporte, 
    menu_ajuda, 
    menu_suporte,
    comando_cadastrar_nova,
    comando_verificar_todos,
    comando_verificar_especifico,
    comando_corrigir,
    comando_excluir,
    comando_planos,
    comando_privacidade,
    botao_canal_callback,
    enviar_resposta_admin,
    AGUARDANDO_RESPOSTA_ADMIN
)

# Carrega as variáveis do arquivo .env
load_dotenv()

# Configuração de logs
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    # Puxa o token de forma segura do ambiente
    TOKEN_NOVO_BOT = os.getenv("TELEGRAM_TOKEN_SUPORTE")

    if not TOKEN_NOVO_BOT:
        print("Erro: A variável TELEGRAM_TOKEN_SUPORTE não foi encontrada no arquivo .env!")
        return

    # Inicializa a aplicação do bot
    app = Application.builder().token(TOKEN_NOVO_BOT).build()

    # Registra o ConversationHandler de suporte principal
    app.add_handler(conv_suporte)

    # Handler global para gerenciar os cliques nos botões do canal (Responder / Concluir)
    app.add_handler(CallbackQueryHandler(botao_canal_callback, pattern="^(resp_|concluir_)"))

    # Handler para capturar o texto digitado pelo administrador após clicar em "Responder Usuário"
    app.add_handler(MessageHandler(filters.Chat(-1004479965268) & filters.TEXT & ~filters.COMMAND, enviar_resposta_admin))

    # Registra os demais comandos do bot
    app.add_handler(CommandHandler("ajuda", menu_ajuda))
    app.add_handler(CommandHandler("suporte", menu_suporte))
    app.add_handler(CommandHandler("cadastrar_nova", comando_cadastrar_nova))
    app.add_handler(CommandHandler("verificar_todos", comando_verificar_todos))
    app.add_handler(CommandHandler("verificar_especifico", comando_verificar_especifico))
    app.add_handler(CommandHandler("corrigir", comando_corrigir))
    app.add_handler(CommandHandler("excluir", comando_excluir))
    app.add_handler(CommandHandler("planos", comando_planos))
    app.add_handler(CommandHandler("privacidade", comando_privacidade))

    logger.info("🎧 Bot de Atendimento e Suporte rodando com segurança!")
    
    app.run_polling()

if __name__ == "__main__":
    main()