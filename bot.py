from flask import Flask, request
import requests
import os

app = Flask(__name__)

# ================= VARIÁVEIS =================
TOKEN = os.getenv("TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print("URL:", SUPABASE_URL)
print("KEY:", SUPABASE_KEY)

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# ================= WHATSAPP =================
def enviar(numero, texto):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": texto}
    }
    requests.post(url, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }, json=payload)

# ================= BANCO =================
def get_usuario(numero):
    url = f"{SUPABASE_URL}/rest/v1/usuarios?telefone=eq.{numero}"
    r = requests.get(url, headers=HEADERS)
    data = r.json()
    return data[0] if data else None

def criar_usuario(numero, etapa):
    requests.post(f"{SUPABASE_URL}/rest/v1/usuarios", headers=HEADERS, json={
        "telefone": numero,
        "etapa": etapa
    })

def atualizar_usuario(numero, dados):
    requests.patch(f"{SUPABASE_URL}/rest/v1/usuarios?telefone=eq.{numero}", headers=HEADERS, json=dados)

def salvar_solicitacao(dados):
    requests.post(f"{SUPABASE_URL}/rest/v1/solicitacoes", headers=HEADERS, json=dados)

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
        numero = msg["from"]
        texto = msg["text"]["body"].strip().lower()

        print("MSG:", numero, texto)

        user = get_usuario(numero)

        # ================= MENU =================
        if not user:
            if texto.startswith("1"):
                criar_usuario(numero, "cpf")
                enviar(numero, "Digite seu CPF:")
                return "ok"

            elif texto.startswith("2"):
                criar_usuario(numero, "s_cpf")
                enviar(numero, "Digite seu CPF:")
                return "ok"

            else:
                enviar(numero, "🏆 LENDÁRIOS\n\n1 Cadastro\n2 Solicitação")
                return "ok"

        etapa = user.get("etapa")

        # ================= CADASTRO =================
        if etapa == "cpf":
            atualizar_usuario(numero, {"cpf": texto, "etapa": "nome"})
            enviar(numero, "Digite seu nome:")
            return "ok"

        if etapa == "nome":
            atualizar_usuario(numero, {"nome": texto, "etapa": "pix"})
            enviar(numero, "Digite sua chave PIX:")
            return "ok"

        if etapa == "pix":
            atualizar_usuario(numero, {"pix": texto, "etapa": "final"})
            enviar(numero, "✅ Cadastro finalizado com sucesso!")
            return "ok"

        # ================= SOLICITAÇÃO =================
        if etapa == "s_cpf":
            atualizar_usuario(numero, {"cpf": texto, "etapa": "campo"})
            enviar(numero, "Digite o nome do campo:")
            return "ok"

        if etapa == "campo":
            atualizar_usuario(numero, {"campo": texto, "etapa": "cidade"})
            enviar(numero, "Digite a cidade:")
            return "ok"

        if etapa == "cidade":
            atualizar_usuario(numero, {"cidade": texto, "etapa": "final_s"})

            salvar_solicitacao({
                "telefone": numero,
                "cpf": user.get("cpf"),
                "campo": user.get("campo"),
                "cidade": texto
            })

            enviar(numero, "✅ Solicitação enviada com sucesso!")
            return "ok"

    except Exception as e:
        print("ERRO:", e)

    return "ok"

@app.route("/")
def home():
    return "BOT ONLINE"

if __name__ == "__main__":
    app.run()
