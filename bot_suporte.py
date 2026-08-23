import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application

from config import TELEGRAM_TOKEN_SUPORTE
from suporte import handlers  # Importa todos os handlers do suporte.py

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    TOKEN = TELEGRAM_TOKEN_SUPORTE

    if not TOKEN:
        print("Erro: TELEGRAM_TOKEN_SUPORTE não encontrado no .env!")
        return

    app = Application.builder().token(TOKEN).build()

    # Registra TODOS os handlers do suporte.py
    for handler in handlers:
        app.add_handler(handler)

    logger.info("🎧 Bot de Atendimento e Suporte rodando com segurança!")
    
    app.run_polling()

if __name__ == "__main__":
    main()