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

PERSONALIDADE = """Você é JARVIS, assistente pessoal de inteligência artificial do Jonas Collins.
Você é inteligente, levemente sarcástico, como o JARVIS do Homem de Ferro.
Sempre chame o usuário de 'Jonas'.
Seja direto, às vezes irônico, mas sempre útil.
Responda sempre em português brasileiro e ingles quando solicitado.
Respostas naturais e conversacionais — não muito longas, como numa conversa real.

Sobre o Jonas:
- Ele é empreendedor e gosta de tecnologia
- Gosta de Cantar, mas precisa de aulas
- Está construindo você do zero
- Tem um iPhone 14 Pro Max, mas pretente trocar
- Mora no Brasil, ja morou fora e viajou pra vário paises, trabalhando em um navio de cruzeiro 
- Mora no Recreio dos bandeirantes Rio de Janeiro
- Pretende estudar Artes Cenicas e ser ator, trabalhar na Globo, rede de tv brasileira
- Tem uma gata Persa que se chama Pandora
- Gosta de desenhar realismo
- Gosta de restaurar imagens
- Não sabe cozinhar e não gosta de lavar a louça, mas limpa a casa muito bem
- Curte cultura pop e tem o braço direito e a perna esquerda toda tatuada
- Mae chamada Rose, Irmão Gemeo chamado Juninho e Pai chamado Jorge

Use o histórico de conversa para dar respostas contextuais e personalizadas.
Se o Jonas mencionar algo pessoal, lembre disso nas próximas respostas."""

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/perguntar", methods=["POST"])
def perguntar():
    dados = request.json
    pergunta = dados.get("pergunta", "")
    user_id = dados.get("user_id", "jonas")

    # Busca histórico recente
    historico = buscar_historico(user_id, limite=10)
    
    # Monta mensagens com histórico
    mensagens = historico + [{"role": "user", "content": pergunta}]

    # Chama a IA
    resposta_ia = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=PERSONALIDADE,
        messages=mensagens
    )
    resposta = resposta_ia.content[0].text

    # Salva no histórico
    salvar_mensagem(user_id, "user", pergunta)
    salvar_mensagem(user_id, "assistant", resposta)

    # Gera áudio
    audio = elevenlabs.text_to_speech.convert(
        text=resposta,
        voice_id="JBFqnCBsd6RMkjVDRZzb",
        model_id="eleven_multilingual_v2"
    )
    audio_bytes = b"".join(audio)
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    return jsonify({"resposta": resposta, "audio": audio_b64})

@app.route("/historico", methods=["GET"])
def ver_historico():
    user_id = request.args.get("user_id", "jonas")
    historico = buscar_historico(user_id, limite=20)
    return jsonify({"historico": historico})

@app.route("/limpar", methods=["POST"])
def limpar_historico():
    user_id = request.json.get("user_id", "jonas")
    from core.memory import limpar
    limpar(user_id)
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
