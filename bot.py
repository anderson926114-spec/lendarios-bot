from flask import Flask, request
import requests
import sqlite3

app = Flask(__name__)

# CONFIGURAÇÕES
VERIFY_TOKEN = "lendarios_token"
TOKEN = "EAAsCShhhFUoBRA8clslnR8NcZApGDKN5o4VBVZBeCQYdDcAG9ruxgQGspQu9YolH2IC0Ng7cLbhsE4mDr9aBwZCLzcQwGmX24FE31xWaZB9nRCZBlqf3RSHZCkJI1BWm3MwkfSkI3tZAjMlzbS42q8QpKy5J2ZBj2Sp7T5N6FFTkmWIrzTnD3VlKe6NuPnYXgN2IkmZBIIZBAafzQojOTEk3a8ZCQ8VO1Lz5qztg3kWjCWe6R8ZBv8w6Ya6LynNoLT01Uida74gBNtDt37awuXWeNhPGuhSl"
PHONE_NUMBER_ID = "1094450353745202"

# CONTROLE DE ETAPAS
usuarios = {}

# =========================
# BANCO DE DADOS
# =========================
def init_db():
    conn = sqlite3.connect("lendarios.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS atletas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT,
        nome TEXT,
        cidade TEXT,
        tipo TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# =========================
# ENVIAR MENSAGEM
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

    r = requests.post(url, headers=headers, json=payload)

    print("STATUS ENVIO:", r.status_code)
    print("RESPOSTA:", r.text)

# =========================
# WEBHOOK
# =========================
@app.route("/webhook", methods=["GET", "POST"])
def webhook():

    if request.method == "GET":
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if token == VERIFY_TOKEN:
            return challenge
        return "erro", 403

    if request.method == "POST":

        data = request.get_json()

        try:
            if "messages" in data["entry"][0]["changes"][0]["value"]:

                msg = data["entry"][0]["changes"][0]["value"]["messages"][0]

                numero = msg["from"]
                texto = msg["text"]["body"].strip().lower()

                # Corrigir número sem 9
                if numero.startswith("5548") and len(numero) == 12:
                    numero = "55489" + numero[4:]

                print(numero, texto)

                # =========================
                # CADASTRO (PRIORIDADE)
                # =========================
                if numero in usuarios:

                    etapa = usuarios[numero]["etapa"]

                    if etapa == "nome":
                        usuarios[numero]["nome"] = texto
                        usuarios[numero]["etapa"] = "cidade"
                        enviar(numero, "📍 Qual sua cidade?")
                        return "ok"

                    elif etapa == "cidade":
                        usuarios[numero]["cidade"] = texto
                        usuarios[numero]["etapa"] = "tipo"
                        enviar(numero, "⚽ Tipo:\n1 Goleiro\n2 Linha\n3 Árbitro")
                        return "ok"

                    elif etapa == "tipo":

                        tipos = {
                            "1": "Goleiro",
                            "2": "Linha",
                            "3": "Árbitro"
                        }

                        print("TIPO RECEBIDO:", texto)

                        if texto not in tipos:
                            enviar(numero, "❌ Opção inválida.\nDigite:\n1 Goleiro\n2 Linha\n3 Árbitro")
                            return "ok"

                        usuarios[numero]["tipo"] = tipos[texto]
                        dados = usuarios[numero]

                        # SALVAR NO BANCO
                        conn = sqlite3.connect("lendarios.db")
                        cursor = conn.cursor()

                        cursor.execute("""
                        INSERT INTO atletas (numero, nome, cidade, tipo)
                        VALUES (?, ?, ?, ?)
                        """, (numero, dados["nome"], dados["cidade"], dados["tipo"]))

                        conn.commit()
                        conn.close()

                        enviar(numero, f"""✅ Cadastro concluído!

Nome: {dados['nome']}
Cidade: {dados['cidade']}
Tipo: {dados['tipo']}
""")

                        del usuarios[numero]
                        return "ok"

                # =========================
                # MENU PRINCIPAL
                # =========================
                if texto == "1":
                    usuarios[numero] = {"etapa": "nome"}
                    enviar(numero, "⚽ *Cadastro de Atleta*\n\nDigite seu nome:")
                    return "ok"

                elif texto == "2":
                    enviar(numero, "📅 Solicitação de jogador em breve!")
                    return "ok"

                elif texto == "3":
                    enviar(numero, "📋 Lista de jogos em breve!")
                    return "ok"

                elif texto == "4":
                    enviar(numero, "👑 Fale com o administrador.")
                    return "ok"

                elif texto == "0":
                    enviar(numero, "👋 Você saiu.")
                    return "ok"

                else:
                    menu = """🏆 *LENDÁRIOS*

Escolha uma opção:

1️⃣ Sou atleta
2️⃣ Solicitar jogador
3️⃣ Ver jogos
4️⃣ Falar com administrador
0️⃣ Sair
"""
                    enviar(numero, menu)
                    return "ok"

        except Exception as e:
            print("ERRO:", e)

        return "ok", 200

# =========================
# HOME
# =========================
@app.route("/")
def home():
    return "BOT LENDARIOS ONLINE"

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(port=5000)
