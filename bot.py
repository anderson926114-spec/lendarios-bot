from flask import Flask, request
import requests
import os

app = Flask(__name__)

VERIFY_TOKEN = "lendarios_token"

TOKEN = "EAAsCShhhFUoBREu4i43KsyIqNijN4VLEDOGlW2wFZCJeJldm1qzwoaT2UNn2ateswAiUfCL9ZCW4nmZB8u7gKXt1iHAXOfgE4BL8NYVRaImk0HNJc6bNNct1LfGpvC9mMwZCTkcmlZBvNdOaTbW9XmZCFoy3kVqTDgxV5bgYsHQ9txRHQ9pWB9bfZBd8V4RtJhYS9dL4USD5riUrBpf9d3GdZCZCfyHVthWcEHcbwVFIwvT9gjCHOnf2yGfwn6aA7mHUL8NHZA6cb21eu1E0rQXZBBPZC3xV"
PHONE_NUMBER_ID = "1094450353745202"

def enviar_mensagem(numero, mensagem):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": numero,
        "text": {"body": mensagem}
    }

    r = requests.post(url, headers=headers, json=data)
print(r.text)

@app.route("/webhook", methods=["GET", "POST"])
def webhook():

    if request.method == "GET":
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if token == VERIFY_TOKEN:
            return challenge
        return "Token inválido"

    if request.method == "POST":
        data = request.get_json()

        try:
            numero = data["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
            mensagem = data["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]

            print(numero, mensagem)

            resposta = """🏆 LENDÁRIOS

1️⃣ Cadastro de atleta
2️⃣ Solicitar atleta
3️⃣ Jogos disponíveis
4️⃣ Ranking
5️⃣ Falar com administrador
"""

            enviar_mensagem(numero, resposta)

        except:
            pass

        return "ok"

@app.route("/")
def home():
    return "Bot Lendários Online"
