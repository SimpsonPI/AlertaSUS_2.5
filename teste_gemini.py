import os
from google import genai

# Inicializa o cliente buscando a chave no ambiente do PowerShell
client = genai.Client()

print("Conectando ao Gemini...")

# Fazendo a chamada com o modelo correto e atual
response = client.models.generate_content(
    model='gemini-3.6-flash',
    contents='Olá! Responda apenas com uma frase curta dizendo que a conexão funcionou.',
)

print("\nResposta da IA:")
print(response.text)