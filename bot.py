from flask import Flask, request
import requests
import sqlite3

app = Flask(__name__)

TOKEN = "EAAsCShhhFUoBRPk9DXcKuP2pAgMNYtisyw1faSleZATjR5d3H0aKPhZAU7zN7HUNVHr75cO4Q6c3Xw6LkQZCKasVsu8r8DTMsQyhFVBD3cX5Xbpjs0GxHoK7d0nsxbtoOXgctVZCyvuN9vG58LKfA0pdrAH5jR0CIow5x3zjxpDZByw5ZB3kvePEOtVFxFwinaSrNO9HGGpU2r53ZBVsLs1EdIA8xERcJrACtFO9cR86kABjua0YYTg2Yu6ZBZAinbeYEcuBu2kJCCZCA53UPh2zAL6R0M"
PHONE_NUMBER_ID = "1094450353745202"
VERIFY_TOKEN = "lendarios_token"

usuarios = {}
solicitacoes = {}

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
        quantidade INTEGER,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# =========================
# NORMALIZAR
# =========================
def normalizar_numero(numero):
    numero = "".join(filter(str.isdigit, numero))
    if numero.startswith("55") and len(numero) == 12:
        numero = numero[:4] + "9" + numero[4:]
    return numero

# =========================
# DADOS
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
# ENVIAR
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

    r = requests.post(url, headers=headers, json=payload)
    print("ENVIO:", r.status_code, r.text)

# =========================
# MENU
# =========================
def menu(numero):
    enviar(numero, """🏆 LENDÁRIOS

1 🧤 Cadastro de atleta
2 ⚽ Solicitar atleta
3 📋 Meus jogos
4 👑 Admin
5 🚪 Sair
""")

# =========================
# WEBHOOK
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

        if "messages" not in value:
            return "ok"

        msg = value["messages"][0]

        if msg["type"] != "text":
            return "ok"

        numero = normalizar_numero(msg["from"])
        texto = msg["text"]["body"].strip().lower()

        print("DEBUG:", numero, texto)

        # =========================
        # INICIO
        # =========================
        if numero not in usuarios and numero not in solicitacoes:

            if texto == "1":
                usuarios[numero] = {"etapa": "nome", "cidades": [], "tipos": []}
                enviar(numero, "⚽ Digite seu nome:")
                return "ok"

            if texto == "2":
                solicitacoes[numero] = {"etapa": "cidade"}
                lista = "\n".join([f"{k} {v}" for k,v in CIDADES.items()])
                enviar(numero, "📍 Escolha cidade:\n\n" + lista)
                return "ok"

            menu(numero)
            return "ok"

        # =========================
        # CADASTRO (mantido igual)
        # =========================
        if numero in usuarios:

            u = usuarios[numero]

            if u["etapa"] == "nome":
                u["nome"] = texto
                u["etapa"] = "cidade"
                enviar(numero, "📍 Escolha cidade:\n" + "\n".join([f"{k} {v}" for k,v in CIDADES.items()]))
                return "ok"

            if u["etapa"] == "cidade":
                if texto not in CIDADES:
                    enviar(numero, "❌ Escolha válida")
                    return "ok"

                u["cidades"].append(CIDADES[texto])
                u["etapa"] = "tipo"
                enviar(numero, "⚽ Tipo:\n1 Goleiro\n2 Linha\n3 Árbitro")
                return "ok"

            if u["etapa"] == "tipo":
                if texto not in TIPOS:
                    enviar(numero, "❌ Escolha válida")
                    return "ok"

                u["tipos"].append(TIPOS[texto])

                conn = sqlite3.connect("lendarios.db")
                cursor = conn.cursor()

                cursor.execute("""
                INSERT INTO atletas (numero,nome,cidades,tipos)
                VALUES (?,?,?,?)
                """, (numero, u["nome"], ",".join(u["cidades"]), ",".join(u["tipos"])))

                conn.commit()
                conn.close()

                enviar(numero, "🏆 Cadastro concluído!")
                del usuarios[numero]
                return "ok"

        # =========================
        # SOLICITAÇÃO COMPLETA
        # =========================
        if numero in solicitacoes:

            s = solicitacoes[numero]

            if s["etapa"] == "cidade":
                if texto not in CIDADES:
                    enviar(numero, "❌ Escolha válida")
                    return "ok"

                s["cidade"] = CIDADES[texto]
                s["etapa"] = "tipo"
                enviar(numero, "⚽ Tipo:\n1 Goleiro\n2 Linha\n3 Árbitro")
                return "ok"

            if s["etapa"] == "tipo":
                if texto not in TIPOS:
                    enviar(numero, "❌ Escolha válida")
                    return "ok"

                s["tipo"] = TIPOS[texto]
                s["etapa"] = "data"
                enviar(numero, "📅 Digite a data (DD/MM)")
                return "ok"

            if s["etapa"] == "data":
                s["data"] = texto
                s["etapa"] = "hora"
                enviar(numero, "⏰ Digite a hora (HH:MM)")
                return "ok"

            if s["etapa"] == "hora":
                s["hora"] = texto
                s["etapa"] = "qtd"
                enviar(numero, "👥 Quantos atletas?")
                return "ok"

            if s["etapa"] == "qtd":

                try:
                    qtd = int(texto)
                except:
                    enviar(numero, "❌ Digite um número válido")
                    return "ok"

                s["qtd"] = qtd

                conn = sqlite3.connect("lendarios.db")
                cursor = conn.cursor()

                cursor.execute("""
                INSERT INTO solicitacoes (numero,cidade,tipo,data,hora,quantidade,status)
                VALUES (?,?,?,?,?,?,?)
                """, (numero, s["cidade"], s["tipo"], s["data"], s["hora"], qtd, "aberto"))

                conn.commit()
                conn.close()

                enviar(numero, f"""✅ Solicitação criada!

Cidade: {s['cidade']}
Tipo: {s['tipo']}
Data: {s['data']}
Hora: {s['hora']}
Qtd: {s['qtd']}
""")

                del solicitacoes[numero]
                return "ok"

        menu(numero)
        return "ok"

    except Exception as e:
        print("ERRO:", e)

    return "ok", 200

@app.route("/")
def home():
    return "BOT LENDARIOS OK"

if __name__ == "__main__":
    app.run(port=5000)
