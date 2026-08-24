import os
import logging
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder
from suporte import handlers as suporte_handlers
from config import TELEGRAM_TOKEN_SUPORTE # ou a variável de token de suporte correspondente

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    token = os.getenv("TELEGRAM_TOKEN_SUPORTE") or os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("Token do bot de suporte não encontrado!")
        return

    application = ApplicationBuilder().token(token).build()

    # Adiciona todos os handlers do suporte
    for handler in suporte_handlers:
        application.add_handler(handler)

    logger.info("🎧 Bot de Atendimento e Suporte rodando isolado com segurança!")
    application.run_polling()

if __name__ == "__main__":
    main()