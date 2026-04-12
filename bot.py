from flask import Flask, request
import requests

app = Flask(__name__)

VERIFY_TOKEN = "lendarios_token"

TOKEN = "EAAsCShhhFUoBRO66HuKZCcs6gfPlPDDtSD3vZBuHRScteFn3RnuMzzqNh2P2Ow4bIU5QSvYGNNeiZCapCxQZB56sZBbxEPwaUzj89QVE16yWhbjBQIw0fRAI7iTjwoLZAklZBii6n3fmPYzCQ5X2wEeZBDDoYNmamJyVxsLrLjHZCBJoQKW6ruSn3W76gFiuTosH5gc9KTl5lSZCfrIn6POecy2FmeGry9Enn4JHBpdPNq9tCLNI689g7eESj441RZC6cU9ZBVQPieTkrrBattkUVdyWFPyggAZDZD"
PHONE_NUMBER_ID = "1094450353745202"


def enviar(numero, texto):

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

    r = requests.post(url, headers=headers, json=payload)

    print("ENVIO:", r.status_code)
    print("RESPOSTA:", r.text)


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

        try:
            numero = data["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
            mensagem = data["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]

            # Corrigir número (caso venha sem 9)
            if numero.startswith("5548") and len(numero) == 12:
                numero = "55489" + numero[4:]

            print(numero, mensagem)

            # MENU
            if mensagem.lower() in ["oi", "menu", "ola", "olá"]:
                resposta = """🏆 LENDÁRIOS

1️⃣ Sou atleta
2️⃣ Solicitar jogador
3️⃣ Ver jogos
4️⃣ Falar com administrador
0️⃣ Sair
"""

            elif mensagem == "1":
                resposta = "⚽ Cadastro de atleta em breve!"

            elif mensagem == "2":
                resposta = "📅 Solicitação de jogador em breve!"

            elif mensagem == "3":
                resposta = "📋 Lista de jogos em breve!"

            elif mensagem == "4":
                resposta = "👑 Fale com o administrador."

            elif mensagem == "0":
                resposta = "👋 Você saiu do menu."

            else:
                resposta = "❌ Opção inválida. Digite *menu* para voltar."

            enviar(numero, resposta)

        except Exception as e:
            print("ERRO:", e)

        return "ok"


@app.route("/")
def home():
    return "BOT LENDÁRIOS ONLINE"
