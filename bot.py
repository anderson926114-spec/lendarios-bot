from flask import Flask, request
import requests
import os

app = Flask(__name__)

TOKEN = os.getenv("EAAsCShhhFUoBRTF8rEGtaXEh6UES9mEiu9pXyNTLZBfluXfyLBY3ZARCzj6fElBYGe26Ogdz4QS306Qf977w7X38PqABTRpeJ4G0YNUefup4oOn8V6ToZBHgrQCf9JuZC5JE1avatcevENYN2e5ipc609qJdLmVdtWeL3BmoZAdQCjsEIR2sU9p1dFRqaJH14VqkMMWuzQXedMIe7yg2obx3c1JpuWPlJmlHIj4BWXzGnnXJjm6MPDz6Ko9lhTNfsSxD9SWGCoj1SfLZC4KZAOUaJPc")
PHONE_NUMBER_ID = os.getenv("1094450353745202")
VERIFY_TOKEN = os.getenv("lendarios_token")

SUPABASE_URL = os.getenv("https://lhrovzoayhxmhdlmznnx.supabase.co")
SUPABASE_KEY = os.getenv("sb_publishable_WJ-gbgLNK9_74ASgrjf6dA_tFKf0tRr")

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
    r = requests.get(f"{SUPABASE_URL}/rest/v1/usuarios?telefone=eq.{numero}", headers=HEADERS)
    data = r.json()
    return data[0] if data else None

def salvar_usuario(numero, dados):
    dados["telefone"] = numero
    requests.post(f"{SUPABASE_URL}/rest/v1/usuarios", headers=HEADERS, json=dados)

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
                salvar_usuario(numero, {"etapa": "cpf"})
                enviar(numero, "Digite seu CPF:")
                return "ok"

            elif texto.startswith("2"):
                salvar_usuario(numero, {"etapa": "s_cpf"})
                enviar(numero, "Digite seu CPF:")
                return "ok"

            else:
                enviar(numero, "🏆 LENDÁRIOS\n\n1 Cadastro\n2 Solicitação")
                return "ok"

        etapa = user["etapa"]

        # ================= CADASTRO =================
        if etapa == "cpf":
            atualizar_usuario(numero, {"cpf": texto, "etapa": "nome"})
            enviar(numero, "Digite seu nome:")
            return "ok"

        if etapa == "nome":
            atualizar_usuario(numero, {"nome": texto, "etapa": "pix"})
            enviar(numero, "Digite seu PIX:")
            return "ok"

        if etapa == "pix":
            atualizar_usuario(numero, {"pix": texto, "etapa": "final"})
            enviar(numero, "✅ Cadastro finalizado!")
            return "ok"

        # ================= SOLICITAÇÃO =================
        if etapa == "s_cpf":
            atualizar_usuario(numero, {"cpf": texto, "etapa": "campo"})
            enviar(numero, "Nome do campo:")
            return "ok"

        if etapa == "campo":
            atualizar_usuario(numero, {"campo": texto, "etapa": "cidade"})
            enviar(numero, "Cidade:")
            return "ok"

        if etapa == "cidade":
            atualizar_usuario(numero, {"cidade": texto, "etapa": "final_s"})
            enviar(numero, "Finalizando...")
            
            salvar_solicitacao({
                "telefone": numero,
                "cpf": user.get("cpf"),
                "campo": texto,
                "cidade": texto
            })

            enviar(numero, "✅ Solicitação enviada!")
            return "ok"

    except Exception as e:
        print("ERRO:", e)

    return "ok"

@app.route("/")
def home():
    return "BOT ONLINE"

if __name__ == "__main__":
    app.run()

