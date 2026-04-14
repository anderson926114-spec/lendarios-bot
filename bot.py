from flask import Flask, request
import requests
import sqlite3

app = Flask(__name__)

TOKEN = "EAAsCShhhFUoBRB1Rbs9EW5xCH0FGvZB7iQDECvbNPiMUyUvcygOZBF9hloJZC4rdmjLu1vMY6BgUPzttv635QBgYKotm1GOtPZCCLwYXH6IL5vDWpVPoZClv1hZAepe5yvMa3SNaCjkFAdrCWnTqf0TR7oZBgJyNzZAOcluV6JXU47h0R2PMELmEy3B3Y47XwuTZA5ZCHTGhjg7LZC7iZADM0gxA3QXQrpnLXfw4I3d9YE597L8BjaRBiupUpw0MQD8bMpZBXr1BXf9NgteOX9ZAUuB1z3rICM"
PHONE_NUMBER_ID = "1094450353745202"
VERIFY_TOKEN = "lendarios_token"

convites = {}
vagas = {}

# =========================
# FUNÇÕES
# =========================
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

# =========================
# BANCO
# =========================
def get_atletas():
    conn = sqlite3.connect("lendarios.db")
    cursor = conn.cursor()
    cursor.execute("SELECT numero,nome,cidades,tipos FROM atletas")
    dados = cursor.fetchall()
    conn.close()
    return dados

# =========================
# MATCH
# =========================
def enviar_convites(solicitacao_id, cidade, tipo, quantidade):

    atletas = get_atletas()

    vagas[solicitacao_id] = {
        "total": quantidade,
        "aceitos": []
    }

    for a in atletas:
        numero, nome, cidades, tipos = a

        if cidade in cidades and tipo in tipos:

            convites[numero] = {
                "solicitacao": solicitacao_id
            }

            enviar(numero, f"""⚽ NOVA PARTIDA!

📍 {cidade}
⚽ {tipo}
👥 Vagas: {quantidade}

Responda:
1 Aceitar
2 Recusar
""")

# =========================
# WEBHOOK
# =========================
@app.route("/webhook", methods=["GET","POST"])
def webhook():

    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "erro", 403

    data = request.get_json()

    try:
        value = data["entry"][0]["changes"][0]["value"]

        if "messages" not in value:
            return "ok"

        msg = value["messages"][0]

        if msg["type"] != "text":
            return "ok"

        numero = normalizar(msg["from"])
        texto = msg["text"]["body"].strip()

        # =========================
        # RESPOSTA CONVITE
        # =========================
        if numero in convites:

            convite = convites[numero]
            solicitacao_id = convite["solicitacao"]

            if solicitacao_id not in vagas:
                enviar(numero, "❌ Vaga encerrada.")
                del convites[numero]
                return "ok"

            controle = vagas[solicitacao_id]

            # ACEITAR
            if texto == "1":

                if numero in controle["aceitos"]:
                    enviar(numero, "⚠ Você já aceitou.")
                    return "ok"

                if len(controle["aceitos"]) >= controle["total"]:
                    enviar(numero, "❌ Vagas já preenchidas.")
                    del convites[numero]
                    return "ok"

                controle["aceitos"].append(numero)

                enviar(numero, "✅ Confirmado na partida!")

                # COMPLETO
                if len(controle["aceitos"]) == controle["total"]:
                    for n in controle["aceitos"]:
                        enviar(n, "🏆 Time completo!")

                    del vagas[solicitacao_id]

                del convites[numero]
                return "ok"

            # RECUSAR
            elif texto == "2":
                enviar(numero, "❌ Você recusou.")
                del convites[numero]
                return "ok"

        # =========================
        # TESTE MATCH
        # =========================
        if texto == "match":

            enviar_convites(
                solicitacao_id=1,
                cidade="São José",
                tipo="Goleiro",
                quantidade=2
            )

            enviar(numero, "🚀 Convites enviados!")
            return "ok"

        enviar(numero, "Digite: match")
        return "ok"

    except Exception as e:
        print("ERRO:", e)

    return "ok"

@app.route("/")
def home():
    return "MATCH NIVEL 2 ONLINE"

if __name__ == "__main__":
    app.run(port=5000)
