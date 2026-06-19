from flask import Flask, request, jsonify, send_from_directory
import anthropic
import os
from elevenlabs.client import ElevenLabs
import base64

app = Flask(__name__)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
elevenlabs = ElevenLabs(api_key=os.environ.get("ELEVENLABS_API_KEY"))

personalidade = """Você é JARVIS, assistente pessoal de inteligência artificial.
Você é inteligente, levemente sarcástico e bem-humorado.
Sempre chame o usuário de 'Jonas'.
Seja direto, às vezes irônico, mas sempre útil.
Responda sempre em português. Respostas curtas, no máximo 2 frases."""

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/perguntar", methods=["POST"])
def perguntar():
    dados = request.json
    pergunta = dados.get("pergunta", "")

    mensagem = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        system=personalidade,
        messages=[{"role": "user", "content": pergunta}]
    )
    resposta = mensagem.content[0].text

    audio = elevenlabs.text_to_speech.convert(
        text=resposta,
        voice_id="JBFqnCBsd6RMkjVDRZzb",
        model_id="eleven_multilingual_v2"
    )

    audio_bytes = b"".join(audio)
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    return jsonify({"resposta": resposta, "audio": audio_b64})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
