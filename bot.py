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
        cpf TEXT,
        nome TEXT,
        cidades TEXT,
        tipos TEXT,
        pix TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS solicitacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT,
        cpf TEXT,
        endereco TEXT,
        cidade TEXT,
        campo TEXT,
        tipo TEXT,
        data TEXT,
        hora TEXT,
        quantidade INTEGER,
        valor TEXT,
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

    requests.post(url, headers=headers, json=payload)

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
                usuarios[numero] = {"etapa": "cpf", "cidades": [], "tipos": []}
                enviar(numero, "🧾 Digite seu CPF:")
                return "ok"

            if texto == "2":
                solicitacoes[numero] = {"etapa": "cpf"}
                enviar(numero, "🧾 Digite seu CPF:")
                return "ok"

            menu(numero)
            return "ok"

        # =========================
        # CADASTRO ATLETA
        # =========================
        if numero in usuarios:

            u = usuarios[numero]

            if u["etapa"] == "cpf":
                u["cpf"] = texto
                u["etapa"] = "nome"
                enviar(numero, "⚽ Digite seu nome:")
                return "ok"

            if u["etapa"] == "nome":
                u["nome"] = texto
                u["etapa"] = "cidade"
                enviar(numero, "📍 Escolha cidade:\n" + "\n".join([f"{k} {v}" for k,v in CIDADES.items()]))
                return "ok"

            if u["etapa"] == "cidade":
                if texto not in CIDADES:
                    enviar(numero, "❌ Escolha válida")
                    return "ok"

                cidade = CIDADES[texto]
                if cidade not in u["cidades"]:
                    u["cidades"].append(cidade)

                u["etapa"] = "cidade_mais"
                enviar(numero, "Adicionar outra cidade? (S/N)")
                return "ok"

            if u["etapa"] == "cidade_mais":

                if texto == "s":
                    u["etapa"] = "cidade"
                    enviar(numero, "Escolha outra cidade:\n" + "\n".join([f"{k} {v}" for k,v in CIDADES.items()]))
                    return "ok"

                u["etapa"] = "tipo"
                enviar(numero, "⚽ Tipo:\n1 Goleiro\n2 Linha\n3 Árbitro")
                return "ok"

            if u["etapa"] == "tipo":
                if texto not in TIPOS:
                    enviar(numero, "❌ Escolha válida")
                    return "ok"

                tipo = TIPOS[texto]
                if tipo not in u["tipos"]:
                    u["tipos"].append(tipo)

                u["etapa"] = "tipo_mais"
                enviar(numero, "Adicionar outro tipo? (S/N)")
                return "ok"

            if u["etapa"] == "tipo_mais":

                if texto == "s":
                    u["etapa"] = "tipo"
                    enviar(numero, "Escolha outro tipo:\n1 Goleiro\n2 Linha\n3 Árbitro")
                    return "ok"

                u["etapa"] = "pix"
                enviar(numero, "💰 Digite sua chave PIX:")
                return "ok"

            if u["etapa"] == "pix":

                conn = sqlite3.connect("lendarios.db")
                cursor = conn.cursor()

                cursor.execute("""
                INSERT INTO atletas (numero,cpf,nome,cidades,tipos,pix)
                VALUES (?,?,?,?,?,?)
                """, (
                    numero,
                    u["cpf"],
                    u["nome"],
                    ",".join(u["cidades"]),
                    ",".join(u["tipos"]),
                    texto
                ))

                conn.commit()
                conn.close()

                enviar(numero, "🏆 Cadastro concluído!")
                del usuarios[numero]
                return "ok"

        # =========================
        # SOLICITAÇÃO
        # =========================
        if numero in solicitacoes:

            s = solicitacoes[numero]

            if s["etapa"] == "cpf":
                s["cpf"] = texto
                s["etapa"] = "endereco"
                enviar(numero, "📍 Digite o endereço do jogo:")
                return "ok"

            if s["etapa"] == "endereco":
                s["endereco"] = texto
                s["etapa"] = "cidade"
                enviar(numero, "Escolha cidade:\n" + "\n".join([f"{k} {v}" for k,v in CIDADES.items()]))
                return "ok"

            if s["etapa"] == "cidade":
                if texto not in CIDADES:
                    enviar(numero, "❌ Escolha válida")
                    return "ok"

                s["cidade"] = CIDADES[texto]
                s["etapa"] = "campo"
                enviar(numero, "🏟 Nome do campo:")
                return "ok"

            if s["etapa"] == "campo":
                s["campo"] = texto
                s["etapa"] = "tipo"
                enviar(numero, "⚽ Tipo:\n1 Goleiro\n2 Linha\n3 Árbitro")
                return "ok"

            if s["etapa"] == "tipo":
                if texto not in TIPOS:
                    enviar(numero, "❌ Escolha válida")
                    return "ok"

                s["tipo"] = TIPOS[texto]
                s["etapa"] = "data"
                enviar(numero, "📅 Data (DD/MM)")
                return "ok"

            if s["etapa"] == "data":
                s["data"] = texto
                s["etapa"] = "hora"
                enviar(numero, "⏰ Hora (HH:MM)")
                return "ok"

            if s["etapa"] == "hora":
                s["hora"] = texto
                s["etapa"] = "qtd"
                enviar(numero, "👥 Quantos atletas?")
                return "ok"

            if s["etapa"] == "qtd":
                s["qtd"] = texto
                s["etapa"] = "valor"
                enviar(numero, "💰 Valor da solicitação:")
                return "ok"

            if s["etapa"] == "valor":

                conn = sqlite3.connect("lendarios.db")
                cursor = conn.cursor()

                cursor.execute("""
                INSERT INTO solicitacoes 
                (numero,cpf,endereco,cidade,campo,tipo,data,hora,quantidade,valor,status)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    numero,
                    s["cpf"],
                    s["endereco"],
                    s["cidade"],
                    s["campo"],
                    s["tipo"],
                    s["data"],
                    s["hora"],
                    s["qtd"],
                    texto,
                    "aberto"
                ))

                conn.commit()
                conn.close()

                enviar(numero, "✅ Solicitação criada com sucesso!")
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
