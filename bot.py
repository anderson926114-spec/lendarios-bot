from flask import Flask, request
import requests

app = Flask(__name__)

VERIFY_TOKEN = "lendarios_token"

TOKEN = "EAAsCShhhFUoBRBm9HfgxZCtXdWrUtomZA3aKylRpbbXkUPUO65AEZBHuCWRnpF92vZCuLuhVvZCznz5yiDK70TTu9cNZAZAyEAfLZBfb9y589PvrX4BHO00aGGJVc0tEO3kW06iRZB8GHwVWo6WNFkaRglDpPRnErU70nZACqRSbXYQZCwmMjU5DbFIySqfb8elPpT0LWPltIlhxvuzISiUwO8CXneZCcARZBrvB9FeOoavYfTRiuvuJybgF7Oc4pYNSD9YE7VgZCFI48KKQQthh2lWZBjKzWjoAQZDZD"
PHONE_NUMBER_ID = "1094450353745202"


def enviar_mensagem(numero, texto):

    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": texto}
    }

    resposta = requests.post(url, headers=headers, json=payload)

    print("STATUS:", resposta.status_code)
    print("RESPOSTA:", resposta.text)


@app.route("/webhook", methods=["GET", "POST"])
def webhook():

    if request.method == "GET":
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if token == VERIFY_TOKEN:
            return challenge
        return "erro"

    if request.method == "POST":

        data = request.get_json()

        print("EVENTO:", data)

        try:

            numero = data["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
            if numero.startswith("5548") and len(numero) == 12:
    numero = "55489" + numero[4:]

            menu = """🏆 LENDÁRIOS

1️⃣ Cadastro de atleta
2️⃣ Solicitar atleta
3️⃣ Jogos disponíveis
4️⃣ Ranking
5️⃣ Falar com administrador
"""

            enviar_mensagem(numero, menu)

        except Exception as erro:

            print("ERRO:", erro)

        return "ok"


@app.route("/")
def home():
    return "BOT LENDÁRIOS ONLINE"
