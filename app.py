from flask import Flask, request, jsonify, send_from_directory
import anthropic
import os
import base64
from elevenlabs.client import ElevenLabs
from core.memory import salvar_mensagem, buscar_historico, buscar_contexto

app = Flask(__name__)
app.static_folder = "frontend"

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
elevenlabs = ElevenLabs(api_key=os.environ.get("ELEVENLABS_API_KEY"))

# Nome do usuário via variável de ambiente — mais seguro
NOME_USUARIO = os.environ.get("NOME_USUARIO", "Jonas")

PERSONALIDADE = f"""Você é JARVIS, assistente pessoal de inteligência artificial de {NOME_USUARIO}.
Você é inteligente, levemente sarcástico e bem-humorado, como o JARVIS do Homem de Ferro.
Sempre chame o usuário de '{NOME_USUARIO}'.
Seja direto, às vezes irônico, mas sempre útil.
Responda sempre em português brasileiro.
Respostas naturais e conversacionais — não muito longas, como numa conversa real."""

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/perguntar", methods=["POST"])
def perguntar():
    try:
        dados = request.json
        pergunta = dados.get("pergunta", "").strip()
        user_id = dados.get("user_id", "jonas")
        usar_audio = dados.get("audio", True)  # frontend pode desativar

        if not pergunta:
            return jsonify({"erro": "Pergunta vazia"}), 400

        # Busca histórico + contexto relevante
        historico = buscar_historico(user_id, limite=10)
        contexto = buscar_contexto(user_id, pergunta)  # agora sendo usado!

        # Injeta contexto relevante no system prompt se existir
        system = PERSONALIDADE
        if contexto:
            system += f"\n\nContexto relevante da memória:\n{contexto}"

        mensagens = historico + [{"role": "user", "content": pergunta}]

        resposta_ia = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system=system,
            messages=mensagens
        )
        resposta = resposta_ia.content[0].text

        salvar_mensagem(user_id, "user", pergunta)
        salvar_mensagem(user_id, "assistant", resposta)

        # Áudio opcional
        audio_b64 = None
        if usar_audio:
            audio = elevenlabs.text_to_speech.convert(
                text=resposta,
                voice_id="JBFqnCBsd6RMkjVDRZzb",
                model_id="eleven_multilingual_v2"
            )
            audio_bytes = b"".join(audio)
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        return jsonify({"resposta": resposta, "audio": audio_b64})

    except anthropic.APIError as e:
        return jsonify({"erro": f"Erro na IA: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"erro": f"Erro interno: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
