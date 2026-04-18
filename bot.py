from flask import Flask, request
import requests

app = Flask(__name__)

TOKEN = "EAAsCShhhFUoBRGTZCd2ye7vngDcsXxExbvZAqKDH267WUAwXZCcxtorbo6CyAKqZAt365BSZBdO35b5LCjm3UIR9CymZBRjbZCEgHFgxKeHSkMLDUIAGpByKVqrX0ItzmWpqG8ZAauP4U6VHLdf7IkSUXje5ioms5LWfpWo2YnrsE4UgAMauTaRrTb3tghy14fOVDyvWyZBkFfH93biZAYGQ1iYqSU7ehUwQ1Ksk0xdBGxs7BRn9g75ZAgD0cJYL7pbdRszVMRGSVdiEDwTWLcebHHsL15P"
PHONE_NUMBER_ID = "1094450353745202"
VERIFY_TOKEN = "lendarios_token"

MAKE_WEBHOOK_URL = "https://hook.us2.make.com/gcgl67hj5uaww80orbjetvjrsuz7ya78"

usuarios = {}
solicitacoes = {}

# =========================
def normalizar(numero):
    numero = "".join(filter(str.isdigit, numero))
    if numero.startswith("55") and len(numero) == 12:
        numero = numero[:4] + "9" + numero[4:]
    return numero

# =========================
def enviar(numero, texto):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

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

    requests.post(url, headers=headers, json=payload)

# =========================
def enviar_make(dados):
    try:
        requests.post(MAKE_WEBHOOK_URL, json=dados)
        print("ENVIADO PARA MAKE:", dados)
    except Exception as e:
        print("ERRO MAKE:", e)

# =========================
@app.route("/teste")
def teste():
    requests.post(MAKE_WEBHOOK_URL, json={"teste": "ok"})
    return "enviado"

# =========================
@app.route("/webhook", methods=["GET", "POST"])
def webhook():

    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "erro", 403

    data = request.get_json()

    try:
        value = data["entry"][0]["changes"][0]["value"]

        # 🔥 IGNORA EVENTOS SEM MENSAGEM
        if "messages" not in value:
            return "ok"

        msg = value["messages"][0]

        numero = normalizar(msg["from"])
        texto = msg["text"]["body"].strip().lower()

        print("MSG:", numero, texto)

        # MENU
        if numero not in usuarios and numero not in solicitacoes:

            if texto == "1":
                usuarios[numero] = {"etapa": "nome"}
                enviar(numero, "Digite seu nome:")
                return "ok"

            if texto == "2":
                solicitacoes[numero] = {"etapa": "cidade"}
                enviar(numero, "Digite cidade:")
                return "ok"

            enviar(numero, "1 Cadastro\n2 Solicitação")
            return "ok"

        # CADASTRO
        if numero in usuarios:
            u = usuarios[numero]

            if u["etapa"] == "nome":
                u["nome"] = texto
                enviar(numero, "Cadastro finalizado!")

                enviar_make({
                    "tipo": "cadastro",
                    "nome": u["nome"],
                    "numero": numero
                })

                del usuarios[numero]
                return "ok"

        # SOLICITAÇÃO
        if numero in solicitacoes:
            s = solicitacoes[numero]

            if s["etapa"] == "cidade":
                s["cidade"] = texto

                enviar(numero, "Solicitação criada!")

                enviar_make({
                    "tipo": "solicitacao",
                    "cidade": s["cidade"],
                    "numero": numero
                })

                del solicitacoes[numero]
                return "ok"

    except Exception as e:
        print("ERRO:", e)

    return "ok"

# =========================
@app.route("/")
def home():
    return "BOT ONLINE"

if __name__ == "__main__":
    app.run(port=5000)
