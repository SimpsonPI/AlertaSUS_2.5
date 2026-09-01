import asyncio
from telegram import Bot, BotCommand

# Token do bot principal
TOKEN = "8988706536:AAEydocNLCLaQzjHJHfGgG0OvBmArz-5ZRA"

async def atualizar_menu():
    bot = Bot(token=TOKEN)
    
    comandos = [
        BotCommand("iniciar", "🚀 Menu principal e boas-vindas"),
        BotCommand("verificar_todos", "🔍 Verificar todas as regulações"),
        BotCommand("verificar_especifico", "🎯 Verificar regulação específica"),
        BotCommand("cadastrar_nova", "➕ Cadastrar nova regulação"),
        BotCommand("corrigir", "✏️ Corrigir dados de regulação"),
        BotCommand("planos", "💳 Ver planos e assinaturas"),
        BotCommand("excluir", "🗑️ Excluir uma regulação"),
        BotCommand("privacidade", "🔒 Política de privacidade e LGPD"),
        BotCommand("suporte", "🤖 Central de Atendimento"),
    ]
    
    await bot.set_my_commands(comandos)
    print("✅ Menu atualizado com sucesso!")

asyncio.run(atualizar_menu())