from flask import Flask, request
import requests
import os

app = Flask(__name__)

VERIFY_TOKEN = "lendarios_token"

TOKEN = "EAAsCShhhFUoBRLdZA8drnlca021m56hXfeLZCmUZAM9lTezLjK5w1x3dgyqF6htEr5J45JVZA5xX5pNh65eZBJWSlNYyjSE7dZCASzZCreHztKtdVFrfYrpS0jY0ACv7Qyxl5tA4C0t2flX8krOiO4WL0B5WasMxIgceqW0t9lmCVbvzTDawLG7LQkZBViTsUtVPqtSXJTZAquCZCpzs5CRN7StfcDlWv8kv7L4Jb4hXJo35wvZC4UmOeGboZChF5RfvUbZCLWQgOmKAi463i0JzinjfVlvvgawZDZD"
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

    requests.post(url, headers=headers, json=data)

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
