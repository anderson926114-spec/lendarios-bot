from flask import Flask, request
import requests
from supabase import create_client

app = Flask(__name__)

# ===== CONFIG =====
TOKEN = "EAAsCShhhFUoBRSmrGrXyUrZB3SVGQlgST8Nm2GnhSPwFEzXCpMICn9kNIPoqOPG0tf8ZB6Ui1asGiJi6cP4T09a4LRjQr522aCOAUpqmKIRjBaIcZCqy7s6AJhziRuFW60prmH3zPc3XEP9aCQ0153ZC8oYcPyD0rTHuAsRm3UZCKckUhZBDfZCQrTaCcIZADL30CMbF1YqjQam3xRnjJs1u6Bkp7E1DlqyfWSSdpTZA3mKhMGlVkIhhI5N8omKBxzg5c8PuUZAEVscjFDXji6afCGC6ZAe"
PHONE_NUMBER_ID = "1094450353745202"
VERIFY_TOKEN = "lendarios_token"

MAKE_WEBHOOK = "https://hook.us2.make.com/pcgibko4cd3yqr5375q4nsy5fgpip4m2"

SUPABASE_URL = "https://lhrovzoayhxmhdlmznnx.supabase.co/rest/v1/"
SUPABASE_KEY = "sb_publishable_WJ-gbgLNK9_74ASgrjf6dA_tFKf0tRr"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ===== FUNÇÕES =====

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

# ===== BANCO =====

def get_user(numero):
    res = supabase.table("usuarios").select("*").eq("telefone", numero).execute()
    return res.data[0] if res.data else None

def save_user(numero, tipo, etapa, dados):
    supabase.table("usuarios").upsert({
        "telefone": numero,
        "tipo_fluxo": tipo,
        "etapa": etapa,
        "dados": dados
    }).execute()

def delete_user(numero):
    supabase.table("usuarios").delete().eq("telefone", numero).execute()

# ===== WEBHOOK =====

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

        user = get_user(numero)

        # ===== MENU =====
        if not user:
            if texto == "1":
                save_user(numero, "cadastro", "cpf", {})
                enviar(numero, "Digite seu CPF:")
                return "ok"

            elif texto == "2":
                save_user(numero, "solicitacao", "cpf", {})
                enviar(numero, "Digite seu CPF:")
                return "ok"

            else:
                enviar(numero, "1 Cadastro\n2 Solicitação")
                return "ok"

        tipo = user["tipo_fluxo"]
        etapa = user["etapa"]
        dados = user["dados"] or {}

        # ===== CADASTRO =====
        if tipo == "cadastro":

            if etapa == "cpf":
                dados["cpf"] = texto
                save_user(numero, tipo, "nome", dados)
                enviar(numero, "Nome:")
                return "ok"

            if etapa == "nome":
                dados["nome"] = texto
                save_user(numero, tipo, "cidade", dados)
                enviar(numero, "Cidade:")
                return "ok"

            if etapa == "cidade":
                dados["cidade"] = texto
                save_user(numero, tipo, "tipo", dados)
                enviar(numero, "Tipo:")
                return "ok"

            if etapa == "tipo":
                dados["tipo"] = texto
                save_user(numero, tipo, "pix", dados)
                enviar(numero, "PIX:")
                return "ok"

            if etapa == "pix":
                dados["pix"] = texto

                enviar_make({
                    "tipo": "cadastro",
                    **dados,
                    "telefone": numero
                })

                enviar(numero, "Cadastro concluído!")
                delete_user(numero)
                return "ok"

        # ===== SOLICITAÇÃO =====
        if tipo == "solicitacao":

            if etapa == "cpf":
                dados["cpf"] = texto
                save_user(numero, tipo, "campo", dados)
                enviar(numero, "Campo:")
                return "ok"

            if etapa == "campo":
                dados["campo"] = texto
                save_user(numero, tipo, "cidade", dados)
                enviar(numero, "Cidade:")
                return "ok"

            if etapa == "cidade":
                dados["cidade"] = texto
                save_user(numero, tipo, "quantidade", dados)
                enviar(numero, "Quantidade:")
                return "ok"

            if etapa == "quantidade":
                dados["quantidade"] = texto

                enviar_make({
                    "tipo": "solicitacao",
                    **dados,
                    "telefone": numero
                })

                enviar(numero, "Solicitação enviada!")
                delete_user(numero)
                return "ok"

        return "ok"

    except Exception as e:
        print("ERRO:", e)
        return "ok"

@app.route("/")
def home():
    return "BOT ONLINE"

if __name__ == "__main__":
    app.run(port=5000)
