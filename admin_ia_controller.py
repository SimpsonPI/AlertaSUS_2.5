import os
import json
import logging
import httpx
from telegram import Update
from telegram.ext import ContextTypes
from database import supabase

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))  # Se não existir, usa 0 (bloqueia acesso)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
NOME_ADMIN = os.getenv("NOME_ADMIN", "")

logger = logging.getLogger(__name__)

# Validação: se ADMIN_ID não for configurado corretamente, desativa o modo admin
if ADMIN_ID == 0:
    logger.warning("⚠️ ADMIN_ID não configurado. Modo admin desativado.")

# URL base para leitura de arquivos do GitHub
GITHUB_BASE_URL = "https://raw.githubusercontent.com/SimpsonPI/central_alertasus_2.5/main/"

async def chamar_groq(system_prompt: str, user_message: str) -> str:
    """Chama a API do Groq e retorna a resposta em texto."""
    if not GROQ_API_KEY:
        return "❌ GROQ_API_KEY não configurada."

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.2
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Erro ao chamar Groq: {e}")
        return f"❌ Erro na chamada à IA: {str(e)}"

async def executar_acao_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para mensagens do administrador (linguagem natural)."""
    if update.effective_user.id != ADMIN_ID:
        return

    if not update.message or not update.message.text:
        return

    user_text = update.message.text

    # 1. PROMPT DE DETECÇÃO (agora entende "minha regulação")
    prompt_deteccao = (
        "Você é o assistente **VS (VigiaSaúde)**. Identifique a ação que o administrador deseja. "
        "Responda APENAS com um JSON válido neste formato:\n"
        "{\n"
        "  \"acao\": \"ler_tabela\" | \"ler_arquivo\" | \"resumo\",\n"
        "  \"tabela\": \"nome_da_tabela\" (se ler_tabela),\n"
        "  \"filtro\": {\"campo\": \"valor\"} (opcional),\n"
        "  \"arquivo\": \"nome_do_arquivo\" (se ler_arquivo)\n"
        "}\n\n"
        "**IMPORTANTE:** Se o administrador disser 'minha regulação', 'meu cadastro' ou 'verifique o status da minha regulação', "
        f"aplique o filtro com `nome_paciente` igual a '{NOME_ADMIN}'.\n"
        "Na tabela `AlertaSUS_2.0`, os campos são: `nome_paciente`, `numero_reg`, `status_anterior`, `procedimento`.\n"
        "Na tabela `assinaturas`, os campos são: `chat_id`, `tipo_plano`, `status`.\n\n"
        "Tabelas: assinaturas, AlertaSUS_2.0.\n"
        "Arquivos: handler_atendimento.py, database_atendimento.py, ia_atendimento.py.\n"
        "Se não souber, use {\"acao\": \"resumo\"}."
    )

    resposta_ia = await chamar_groq(prompt_deteccao, user_text)

    try:
        data = json.loads(resposta_ia)
        acao = data.get("acao", "resumo")
        tabela = data.get("tabela", "")
        filtro = data.get("filtro", {})
        arquivo = data.get("arquivo", "")

        dados_brutos = ""

        # 2. Executa a ação e coleta os dados
        if acao == "ler_tabela":
            try:
                query = supabase.table(tabela).select("*")
                # Aplica o filtro
                if filtro:
                    for campo, valor in filtro.items():
                        query = query.eq(campo, valor)
                # Se o filtro estiver vazio, mas o usuário pediu "minha regulação", filtra manualmente
                elif "minha regulação" in user_text.lower() or NOME_ADMIN.lower() in user_text.lower():
                    query = query.eq("nome_paciente", NOME_ADMIN)

                res = query.limit(5).execute()
                dados_brutos = json.dumps(res.data, ensure_ascii=False, indent=2)
            except Exception as e:
                dados_brutos = f"Erro: {str(e)}"

        elif acao == "ler_arquivo":
            try:
                url = f"{GITHUB_BASE_URL}{arquivo}"
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url)
                    if response.status_code == 200:
                        dados_brutos = response.text[:3000]
                    else:
                        dados_brutos = f"Arquivo não encontrado (status {response.status_code})."
            except Exception as e:
                dados_brutos = f"Erro: {str(e)}"

        elif acao == "resumo":
            try:
                total_assinaturas = supabase.table("assinaturas").select("*", count="exact").execute().count
                total_regulacoes = supabase.table("AlertaSUS_2.0").select("*", count="exact").execute().count
                dados_brutos = f"Total de assinaturas: {total_assinaturas}. Total de regulações: {total_regulacoes}."
            except Exception as e:
                dados_brutos = f"Erro: {str(e)}"

        # 3. PROMPT DE FORMATAÇÃO (resposta direta e sem Markdown)
        prompt_formatacao = (
            "Você é o **VS**, assistente pessoal do **Sr. Lincoln**. "
            "Receba os dados a seguir e transforme em uma resposta **direta, acertiva e sem burocracia**. "
            "Não use Markdown (não use **, ##, etc). Use apenas texto puro. "
            "Não explique o que fez. Apenas apresente a informação solicitada. "
            "Se for o status de uma regulação, traga o número da regulação, o procedimento e o status atual. "
            "Se não encontrar dados, diga claramente que não encontrou.\n\n"
            f"**Dados recebidos:**\n{dados_brutos}\n\n"
            "**Como responder:**\n"
            "Comece com uma saudação curta (ex: 'Sr. Lincoln,'). "
            "Apresente as informações de forma organizada e legível."
        )

        resposta_final = await chamar_groq(prompt_formatacao, "Formate os dados acima para mim.")

    except json.JSONDecodeError:
        resposta_final = resposta_ia  # Fallback

    # Envia a resposta (sem parse_mode para evitar erros)
    try:
        await update.message.reply_text(resposta_final, parse_mode=None)
    except Exception as e:
        logger.error(f"Erro ao enviar resposta: {e}")
        await update.message.reply_text("Desculpe, tive um problema ao processar sua solicitação.")