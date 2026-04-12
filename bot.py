from flask import Flask, request
import requests
import sqlite3

app = Flask(__name__)

# =========================
# CONFIGURAÇÕES
# =========================
VERIFY_TOKEN = "lendarios_token"
TOKEN = "EAAsCShhhFUoBRJDVSHkFlGzpSn2XYyzfVxGfPxrG80Wx9eYXkZC96o34JoZBAqZBni6W4IMa0re7n8Nd8XXqr9bnRE4uWeqAVgCsoGSlPbDQGZB6Ta8iVMyZAmoOITNrFcE09zVtUVrpuIO983542AkGIMcuWEvJgZCL4UVmVrfyqAzqZCwc9aBbPEYwC27uGZCxyd0vkAjCK9ZAjirY0r0ZAEtv00uVUpkszYZAHk1ZB0STq36nXc9qSM03oHyTIoQsJ4ubBCMdABHMNRqW7g7NSKB8yx2e"
PHONE_NUMBER_ID = "1094450353745202"

# =========================
# CONTROLE
# =========================
usuarios = {}
solicitacoes = {}

# =========================
# NORMALIZAR NÚMERO
# =========================
def normalizar_numero(numero):
    numero = "".join(filter(str.isdigit, numero))

    if numero.startswith("55") and len(numero) == 12:
        numero = numero[:4] + "9" + numero[4:]

    return numero

# =========================
# BANCO
# =========================
def init_db():
    conn = sqlite3.connect("lendarios.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS atletas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT,
        nome TEXT,
        cidades TEXT,
        tipos TEXT
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
        quantidade TEXT,
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
    numero = normalizar_numero(numero)

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
# CIDADES FIXAS (USADAS EM TUDO)
# =========================
CIDADES = {
    "1": "São José",
    "2": "Palhoça",
    "3": "Biguaçu",
    "4": "Florianópolis / Continente",
    "5": "Florianópolis / Ilha"
}

TIPOS = {
    "1": "Goleiro",
    "2": "Linha",
    "3": "Árbitro"
}

# =========================
# WEBHOOK
# =========================
@app.route("/webhook", methods=["GET", "POST"])
def webhook():

    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "erro", 403

    try:
        msg = request.get_json()["entry"][0]["changes"][0]["value"]["messages"][0]

        numero = normalizar_numero(msg["from"])
        texto = msg["text"]["body"].strip().lower()

        print("DEBUG:", numero, texto)

        # =========================
        # MENU
        # =========================
        if texto in ["oi", "menu"]:

            enviar(numero, """🏆 LENDÁRIOS

1 🧤 Cadastro de atleta
2 ⚽ Solicitar atleta
3 📋 Meus jogos
4 👑 Falar com admin
5 🚪 Sair
""")
            return "ok"

        # =========================
        # CADASTRO ATLETA
        # =========================
        if texto == "1":
            usuarios[numero] = {
                "etapa": "nome",
                "cidades": [],
                "tipos": []
            }
            enviar(numero, "⚽ Cadastro de atleta\n\nDigite seu nome:")
            return "ok"

        if numero in usuarios:

            u = usuarios[numero]

            # NOME
            if u["etapa"] == "nome":
                u["nome"] = texto
                u["etapa"] = "cidade"

                enviar(numero, """📍 Escolha uma cidade:

1 São José
2 Palhoça
3 Biguaçu
4 Florianópolis / Continente
5 Florianópolis / Ilha
""")
                return "ok"

            # CIDADE
            if u["etapa"] == "cidade" and texto in CIDADES:

                cidade = CIDADES[texto]

                if cidade not in u["cidades"]:
                    u["cidades"].append(cidade)

                u["etapa"] = "cidade_mais"

                enviar(numero, "Deseja adicionar mais cidades? (S/N)")
                return "ok"

            if u["etapa"] == "cidade_mais":

                if texto == "s":
                    lista = ""

                    for k, v in CIDADES.items():
                        if v not in u["cidades"]:
                            lista += f"{k} {v}\n"

                    u["etapa"] = "cidade"
                    enviar(numero, "📍 Escolha outra cidade:\n\n" + lista)
                    return "ok"

                else:
                    u["etapa"] = "tipo"

                    enviar(numero, """⚽ Tipo:

1 Goleiro
2 Linha
3 Árbitro
""")
                    return "ok"

            # TIPOS
            if u["etapa"] == "tipo" and texto in TIPOS:

                tipo = TIPOS[texto]

                if tipo not in u["tipos"]:
                    u["tipos"].append(tipo)

                u["etapa"] = "tipo_mais"

                enviar(numero, "Deseja adicionar mais tipos? (S/N)")
                return "ok"

            if u["etapa"] == "tipo_mais":

                if texto == "s":
                    lista = ""

                    for k, v in TIPOS.items():
                        if v not in u["tipos"]:
                            lista += f"{k} {v}\n"

                    u["etapa"] = "tipo"
                    enviar(numero, "⚽ Escolha outro tipo:\n\n" + lista)
                    return "ok"

                else:

                    conn = sqlite3.connect("lendarios.db")
                    cursor = conn.cursor()

                    cursor.execute("""
                    INSERT INTO atletas (numero, nome, cidades, tipos)
                    VALUES (?, ?, ?, ?)
                    """, (
                        numero,
                        u["nome"],
                        ",".join(u["cidades"]),
                        ",".join(u["tipos"])
                    ))

                    conn.commit()
                    conn.close()

                    enviar(numero, "🏆 Cadastro concluído com sucesso!")

                    del usuarios[numero]
                    return "ok"

        # =========================
        # SOLICITAÇÃO (CORRIGIDA)
        # =========================
        if texto == "2":
            solicitacoes[numero] = {"etapa": "cidade"}

            lista = ""
            for k, v in CIDADES.items():
                lista += f"{k} {v}\n"

            enviar(numero, "📍 Escolha a cidade do jogo:\n\n" + lista)
            return "ok"

        if numero in solicitacoes:

            s = solicitacoes[numero]

            if s["etapa"] == "cidade" and texto in CIDADES:

                s["cidade"] = CIDADES[texto]
                s["etapa"] = "tipo"

                enviar(numero, """⚽ Tipo de atleta:

1 Goleiro
2 Linha
3 Árbitro
""")
                return "ok"

            if s["etapa"] == "tipo" and texto in TIPOS:

                s["tipo"] = TIPOS[texto]
                s["etapa"] = "final"

                enviar(numero, "📅 Digite a data do jogo (DD/MM):")
                return "ok"

            if s["etapa"] == "final":

                conn = sqlite3.connect("lendarios.db")
                cursor = conn.cursor()

                cursor.execute("""
                INSERT INTO solicitacoes (numero, cidade, tipo, data, hora, quantidade, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    numero,
                    s["cidade"],
                    s["tipo"],
                    texto,
                    "",
                    "",
                    "aberto"
                ))

                conn.commit()
                conn.close()

                enviar(numero, "✅ Solicitação criada com sucesso!")

                del solicitacoes[numero]
                return "ok"

        # =========================
        # DEFAULT
        # =========================
        enviar(numero, "Digite MENU para começar.")
        return "ok"

    except Exception as e:
        print("ERRO:", e)

    return "ok", 200

@app.route("/")
def home():
    return "BOT LENDARIOS ONLINE"

if __name__ == "__main__":
    app.run(port=5000)
