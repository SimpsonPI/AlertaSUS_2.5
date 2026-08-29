# -*- coding: utf-8 -*-
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Bot ativo com sucesso.')

def main():
    token = '8988706536:AAElQEEH-LouWkLa5YNW_k0isUcUGzm0jps'
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler('start', start))
    app.run_polling()

if __name__ == '__main__':
    main()
