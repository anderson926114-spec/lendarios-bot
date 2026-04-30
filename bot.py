from flask import Flask, request
import requests

app = Flask(__name__)

# ================= CONFIG =================
TOKEN = "EAAsCShhhFUoBRSmrGrXyUrZB3SVGQlgST8Nm2GnhSPwFEzXCpMICn9kNIPoqOPG0tf8ZB6Ui1asGiJi6cP4T09a4LRjQr522aCOAUpqmKIRjBaIcZCqy7s6AJhziRuFW60prmH3zPc3XEP9aCQ0153ZC8oYcPyD0rTHuAsRm3UZCKckUhZBDfZCQrTaCcIZADL30CMbF1YqjQam3xRnjJs1u6Bkp7E1DlqyfWSSdpTZA3mKhMGlVkIhhI5N8omKBxzg5c8PuUZAEVscjFDXji6afCGC6ZAe"
PHONE_NUMBER_ID = "1094450353745202"
VERIFY_TOKEN = "lendarios_token"

MAKE_WEBHOOK = "https://hook.us2.make.com/pcgibko4cd3yqr5375q4nsy5fgpip4m2"

usuarios = {}
solicitacoes = {}

# ================= DADOS =================
CIDADES = {
    "1": "São José",
    "2": "Palhoça",
    "3": "Biguaçu",
    "4": "Florianópolis Continente",
    "5": "Florianópolis Ilha"
}

TIPOS = {
    "1": ("Goleiro", 40),
    "2": ("Jogador Linha", 30),
    "3": ("Árbitro", 50)
}

CAMPOS = {
    "1": "Campo Oficial",
    "2": "Society",
    "3": "Futsal"
}

# ================= FUNÇÕES =================
def normalizar(numero):
    numero = "".join(filter(str.isdigit, numero))
    if numero.startswith("55") and len(numero) == 12:
        numero = numero[:4] + "9" + numero[4:]
    return numero

def enviar(numero, texto):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": texto}
    }
    requests.post(url, headers=headers, json=payload)

def enviar_make(dados):
    requests.post(MAKE_WEBHOOK, json=dados)
    print("ENVIADO:", dados)

def menu(numero):
    enviar(numero,
        "🏆 LENDÁRIOS\n\n"
        "1 Cadastro\n"
        "2 Solicitação"
    )

# ================= WEBHOOK =================
@app.route("/webhook", methods=["GET", "POST"])
def webhook():

    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "erro", 403

    data = request.get_json()

    try:
        msg = data["entry"][0]["changes"][0]["value"]["messages"][0]
        numero = normalizar(msg["from"])
        texto = msg["text"]["body"].strip().lower()

        # MENU
        if numero not in usuarios and numero not in solicitacoes:
            if texto == "1":
                usuarios[numero] = {"etapa": "nome"}
                enviar(numero, "Digite seu nome:")
                return "ok"

            elif texto == "2":
                solicitacoes[numero] = {"etapa": "campo"}
                enviar(numero, "Digite o campo:")
                return "ok"

            else:
                menu(numero)
                return "ok"

        # CADASTRO
        if numero in usuarios:
            u = usuarios[numero]

            if u["etapa"] == "nome":
                u["nome"] = texto

                enviar_make({
                    "tipo": "cadastro",
                    "nome": texto,
                    "telefone": numero
                })

                enviar(numero, "Cadastro feito!")
                del usuarios[numero]
                return "ok"

        # SOLICITAÇÃO
        if numero in solicitacoes:
            s = solicitacoes[numero]

            if s["etapa"] == "campo":
                s["campo"] = texto

                enviar_make({
                    "tipo": "solicitacao",
                    "campo": texto,
                    "telefone": numero
                })

                enviar(numero, "Solicitação enviada!")
                del solicitacoes[numero]
                return "ok"

    except Exception as e:
        print("ERRO:", e)

    return "ok"

@app.route("/")
def home():
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
