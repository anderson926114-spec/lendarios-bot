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
# NORMALIZAR NÚMERO
# =========================
def normalizar_numero(numero):
    numero = "".join(filter(str.isdigit, numero))
    if numero.startswith("55") and len(numero) == 12:
        numero = numero[:4] + "9" + numero[4:]
    return numero

# =========================
# DADOS FIXOS
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
# MENU GLOBAL (QUALQUER TEXTO)
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
        msg = data["entry"][0]["changes"][0]["value"]["messages"][0]

        numero = normalizar_numero(msg["from"])
        texto = msg["text"]["body"].strip().lower()

        print("DEBUG:", numero, texto)

        # =========================
        # MENU GLOBAL INTELIGENTE
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
        # CADASTRO ATLETA
        # =========================
        if numero in usuarios:

            u = usuarios[numero]

            if u["etapa"] == "nome":
                u["nome"] = texto
                u["etapa"] = "cidade"

                lista = "\n".join([f"{k} {v}" for k,v in CIDADES.items()])
                enviar(numero, "📍 Cidade:\n\n" + lista)
                return "ok"

            if u["etapa"] == "cidade" and texto in CIDADES:
                cidade = CIDADES[texto]

                if cidade not in u["cidades"]:
                    u["cidades"].append(cidade)

                u["etapa"] = "cidade_mais"
                enviar(numero, "Mais cidades? (S/N)")
                return "ok"

            if u["etapa"] == "cidade_mais":

                if texto == "s":
                    lista = "\n".join([f"{k} {v}" for k,v in CIDADES.items() if v not in u["cidades"]])
                    u["etapa"] = "cidade"
                    enviar(numero, "Outra cidade:\n\n" + lista)
                    return "ok"

                u["etapa"] = "tipo"
                enviar(numero, "⚽ Tipo (1/2/3)")
                return "ok"

            if u["etapa"] == "tipo" and texto in TIPOS:
                tipo = TIPOS[texto]

                if tipo not in u["tipos"]:
                    u["tipos"].append(tipo)

                u["etapa"] = "tipo_mais"
                enviar(numero, "Mais tipos? (S/N)")
                return "ok"

            if u["etapa"] == "tipo_mais":

                if texto == "s":
                    lista = "\n".join([f"{k} {v}" for k,v in TIPOS.items() if v not in u["tipos"]])
                    u["etapa"] = "tipo"
                    enviar(numero, "Outro tipo:\n\n" + lista)
                    return "ok"

                conn = sqlite3.connect("lendarios.db")
                cursor = conn.cursor()

                cursor.execute("""
                INSERT INTO atletas (numero,nome,cidades,tipos)
                VALUES (?,?,?,?)
                """, (
                    numero,
                    u["nome"],
                    ",".join(u["cidades"]),
                    ",".join(u["tipos"])
                ))

                conn.commit()
                conn.close()

                enviar(numero, "🏆 Cadastro concluído!")
                del usuarios[numero]
                return "ok"

        # =========================
        # SOLICITAÇÃO (ISOLADA)
        # =========================
        if numero in solicitacoes:

            s = solicitacoes[numero]

            if s["etapa"] == "cidade" and texto in CIDADES:
                s["cidade"] = CIDADES[texto]
                s["etapa"] = "final"

                enviar(numero, "⚽ Solicitação criada para: " + s["cidade"])
                del solicitacoes[numero]
                return "ok"

        # fallback sempre volta menu
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
