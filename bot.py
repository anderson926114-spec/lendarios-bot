from flask import Flask, request
import requests
import sqlite3

app = Flask(__name__)

# CONFIGURAÇÕES
VERIFY_TOKEN = "lendarios_token"
TOKEN = "EAAsCShhhFUoBRJZBmQ9jl9vZCcY58DN3GUQTbc7BcqZCSYU8IIwaLQRx1TSmsNgYRcEhdUuwXBPqQosCOBUV9zGQacPNInHo72SxCZAmAbWMOU89KHYLnAUwZBA9VYQF8CIPaeuFaVSfDkypkLaHBJCihP3kbH6NnJwJcQ0ZCyrj9l6gzZAY64y3BzfxTAVYkuAkyaP1FCycZBrTzqP6RQmAq1ZAGBbiIy976woQoOAZArOV4F6I7E3bjUsZA1hj45APh5EfSROyhN65ZCkwkeI5nzqqDB0eKwZDZD"
PHONE_NUMBER_ID = "1094450353745202"

# CONTROLE
usuarios = {}
solicitacoes = {}

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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS solicitacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT,
        cidade TEXT,
        tipo TEXT,
        data TEXT,
        hora TEXT,
        quantidade INTEGER,
        status TEXT
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

    print("STATUS:", r.status_code)
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
                # CADASTRO ATLETA
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

                        if texto not in tipos:
                            enviar(numero, "❌ Opção inválida.\n1 Goleiro\n2 Linha\n3 Árbitro")
                            return "ok"

                        usuarios[numero]["tipo"] = tipos[texto]
                        dados = usuarios[numero]

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
                # SOLICITAÇÃO DE JOGADOR
                # =========================
                if numero in solicitacoes:

                    etapa = solicitacoes[numero]["etapa"]

                    if etapa == "cidade":
                        solicitacoes[numero]["cidade"] = texto
                        solicitacoes[numero]["etapa"] = "tipo"
                        enviar(numero, "⚽ Tipo:\n1 Goleiro\n2 Linha\n3 Árbitro")
                        return "ok"

                    elif etapa == "tipo":
                        tipos = {"1": "Goleiro", "2": "Linha", "3": "Árbitro"}

                        if texto not in tipos:
                            enviar(numero, "❌ Opção inválida.\n1 Goleiro\n2 Linha\n3 Árbitro")
                            return "ok"

                        solicitacoes[numero]["tipo"] = tipos[texto]
                        solicitacoes[numero]["etapa"] = "data"
                        enviar(numero, "📅 Digite a data (DD/MM/AA)")
                        return "ok"

                    elif etapa == "data":
                        solicitacoes[numero]["data"] = texto
                        solicitacoes[numero]["etapa"] = "hora"
                        enviar(numero, "⏰ Digite a hora (HH:MM)")
                        return "ok"

                    elif etapa == "hora":
                        solicitacoes[numero]["hora"] = texto
                        solicitacoes[numero]["etapa"] = "quantidade"
                        enviar(numero, "👥 Quantos atletas?")
                        return "ok"

                    elif etapa == "quantidade":
                        solicitacoes[numero]["quantidade"] = texto

                        dados = solicitacoes[numero]

                        conn = sqlite3.connect("lendarios.db")
                        cursor = conn.cursor()

                        cursor.execute("""
                        INSERT INTO solicitacoes (numero, cidade, tipo, data, hora, quantidade, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            numero,
                            dados["cidade"],
                            dados["tipo"],
                            dados["data"],
                            dados["hora"],
                            dados["quantidade"],
                            "aberto"
                        ))

                        conn.commit()
                        conn.close()

                        enviar(numero, f"""✅ Solicitação criada!

Cidade: {dados['cidade']}
Tipo: {dados['tipo']}
Data: {dados['data']}
Hora: {dados['hora']}
Qtd: {dados['quantidade']}
""")

                        del solicitacoes[numero]
                        return "ok"

                # =========================
                # MENU PRINCIPAL
                # =========================
                if texto == "1":
                    usuarios[numero] = {"etapa": "nome"}
                    enviar(numero, "⚽ Cadastro de atleta\n\nDigite seu nome:")
                    return "ok"

                elif texto == "2":
                    solicitacoes[numero] = {"etapa": "cidade"}
                    enviar(numero, "📍 Qual a cidade do jogo?")
                    return "ok"

                elif texto == "3":
                    enviar(numero, "📋 Em breve lista de jogos")
                    return "ok"

                elif texto == "4":
                    enviar(numero, "👑 Fale com o administrador")
                    return "ok"

                elif texto == "0":
                    enviar(numero, "👋 Você saiu")
                    return "ok"

                else:
                    enviar(numero, """🏆 LENDÁRIOS

1️⃣ Sou atleta
2️⃣ Solicitar jogador
3️⃣ Ver jogos
4️⃣ Falar com administrador
0️⃣ Sair
""")
                    return "ok"

        except Exception as e:
            print("ERRO:", e)

        return "ok", 200

@app.route("/")
def home():
    return "BOT LENDARIOS ONLINE"

if __name__ == "__main__":
    app.run(port=5000)
