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
    r = requests.post(url, headers=headers, json=payload)
    print("ENVIO:", r.status_code, r.text)

# =========================
# BANCO
# =========================
def init_db():
    conn = sqlite3.connect("lendarios.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS atletas (
        numero TEXT,
        nome TEXT,
        cidades TEXT,
        tipos TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# =========================
# INSERIR ATLETAS TESTE
# =========================
def criar_atletas_teste():

    conn = sqlite3.connect("lendarios.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM atletas")

    # 👉 COLOQUE SEU NÚMERO AQUI
    cursor.execute("INSERT INTO atletas VALUES (?,?,?,?)",
                   ("5548984845799", "Você Teste", "São José", "Goleiro"))

    conn.commit()
    conn.close()

# =========================
# BUSCAR ATLETAS
# =========================
def buscar_atletas(cidade, tipo):

    conn = sqlite3.connect("lendarios.db")
    cursor = conn.cursor()

    cursor.execute("SELECT numero,nome,cidades,tipos FROM atletas")
    dados = cursor.fetchall()
    conn.close()

    resultado = []

    for a in dados:
        numero, nome, cidades, tipos = a

        if cidade in cidades and tipo in tipos:
            resultado.append(a)

    return resultado

# =========================
# MATCH
# =========================
def enviar_convites(cidade, tipo, quantidade):

    atletas = buscar_atletas(cidade, tipo)

    if not atletas:
        print("⚠ Nenhum atleta encontrado")
        return

    solicitacao_id = 1

    vagas[solicitacao_id] = {
        "total": quantidade,
        "aceitos": []
    }

    for a in atletas:
        numero = a[0]

        convites[numero] = {
            "solicitacao": solicitacao_id
        }

        enviar(numero, f"""⚽ NOVA PARTIDA!

📍 {cidade}
⚽ {tipo}
👥 Vagas: {quantidade}

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

        print("MSG:", numero, texto)

        # =========================
        # RESPOSTA CONVITE
        # =========================
        if numero in convites:

            solicitacao_id = convites[numero]["solicitacao"]
            controle = vagas.get(solicitacao_id)

            if not controle:
                enviar(numero, "❌ Vaga encerrada.")
                return "ok"

            if texto == "1":

                if numero in controle["aceitos"]:
                    enviar(numero, "⚠ Já aceitou")
                    return "ok"

                if len(controle["aceitos"]) >= controle["total"]:
                    enviar(numero, "❌ Vagas completas")
                    return "ok"

                controle["aceitos"].append(numero)

                enviar(numero, "✅ Você entrou no jogo!")

                if len(controle["aceitos"]) == controle["total"]:
                    for n in controle["aceitos"]:
                        enviar(n, "🏆 Time completo!")

                return "ok"

            if texto == "2":
                enviar(numero, "❌ Você recusou")
                return "ok"

        # =========================
        # COMANDO TESTE
        # =========================
        if texto.lower() == "match":

            criar_atletas_teste()

            enviar_convites(
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
    return "MATCH OK"

if __name__ == "__main__":
    app.run(port=5000)
