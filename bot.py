from flask import Flask, request
import requests

app = Flask(__name__)

VERIFY_TOKEN = "lendarios_token"

TOKEN = "EAAsCShhhFUoBRJoxzOzCcY2H2dVP9LLGZBXC7sgUlRzT5rw4fzTArwXyMQFPj0fJB2QWyZAHrfD85aTMJ9kgPh0vfp3J4o9DyZCMdbQn0GUKBpdj0YXZCjt5LCDhZCX0xS1vuZBki3b4CJ9IFgsHU0Uiq7FO3Ifr2m5KlqrXp648pzcdllPZCZB86YxVq36OJASaKZAJSd7YU0vtoq3qdzEB2yPhwx1XAqBeBYCiAYDl1KpBI8BAqZBrsZBDLlZCjCR5drAGvk6VNWu0inVEu0t9RGcFMODhXgZDZD"
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
