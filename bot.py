from flask import Flask, request
import requests
import sqlite3

app = Flask(__name__)

# =========================
# CONFIGURAÇÕES
# =========================
VERIFY_TOKEN = "lendarios_token"
TOKEN = "EAAsCShhhFUoBRISmZCf37gdC2gfiMOb9aWTCCEnkwcCofT79wFvj8hZAdZCOLXTOate715vcocRqo3L3GevMZCp1mdt0tNWLxuDyfBU1ywbPCIMZCZBL6QARaZBd8kS4WSbUkkILrFde5zEuZBMSPuI3bYWvRztvSFZA1INAiPev9WWzus8tPrKZAqVvZAJkxGKsgWfTh86mu4PjWIs5dXbrUN04WqXg6zFfzArQPd9qZALUQGChz7KMPvt3KtlbbZBpxiuCLyRYBJWWnfkJvbAWQ8dKa7hZBm"
PHONE_NUMBER_ID = "1094450353745202"

# =========================
# CONTROLE DE FLUXO
# =========================
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

    # VERIFICAÇÃO META
    if request.method == "GET":
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if token == VERIFY_TOKEN:
            return challenge
        return "erro", 403

    # MENSAGENS
    if request.method == "POST":

        data = request.get_json()

        try:
            msg = data["entry"][0]["changes"][0]["value"]["messages"][0]
            numero = msg["from"]
            texto = msg["text"]["body"].strip().lower()

            print(numero, texto)

            # =========================
            # CADASTRO ATLETA
            # =========================
            if numero in usuarios:

                etapa = usuarios[numero]["etapa"]

                # -------------------------
                # NOME
                # -------------------------
                if etapa == "nome":
                    usuarios[numero]["nome"] = texto
                    usuarios[numero]["cidades"] = []
                    usuarios[numero]["tipos"] = []
                    usuarios[numero]["etapa"] = "cidade"

                    enviar(numero, """📍 Escolha uma cidade:

1 São José
2 Palhoça
3 Biguaçu
4 Florianópolis/Continente
5 Florianópolis/Ilha
""")
                    return "ok"

                # -------------------------
                # CIDADES
                # -------------------------
                if etapa == "cidade":

                    opcoes = {
                        "1": "São José",
                        "2": "Palhoça",
                        "3": "Biguaçu",
                        "4": "Florianópolis/Continente",
                        "5": "Florianópolis/Ilha"
                    }

                    if texto in opcoes:

                        cidade = opcoes[texto]

                        if cidade not in usuarios[numero]["cidades"]:
                            usuarios[numero]["cidades"].append(cidade)

                        usuarios[numero]["etapa"] = "cidade_mais"

                        enviar(numero, f"""✅ {cidade} adicionada!

Deseja adicionar mais cidades? (S/N)
""")
                        return "ok"

                if etapa == "cidade_mais":

                    if texto == "s":

                        escolhidas = usuarios[numero]["cidades"]

                        opcoes = {
                            "1": "São José",
                            "2": "Palhoça",
                            "3": "Biguaçu",
                            "4": "Florianópolis/Continente",
                            "5": "Florianópolis/Ilha"
                        }

                        lista = ""
                        novo_map = {}
                        i = 1

                        for k, v in opcoes.items():
                            if v not in escolhidas:
                                novo_map[str(i)] = v
                                lista += f"{i} {v}\n"
                                i += 1

                        usuarios[numero]["map_cidades"] = novo_map
                        usuarios[numero]["etapa"] = "cidade"

                        enviar(numero, "📍 Escolha outra cidade:\n\n" + lista)
                        return "ok"

                    else:
                        usuarios[numero]["etapa"] = "tipo"

                        enviar(numero, """⚽ Escolha o tipo:

1 Goleiro
2 Linha
3 Árbitro
""")
                        return "ok"

                # -------------------------
                # TIPOS
                # -------------------------
                if etapa == "tipo":

                    opcoes = {
                        "1": "Goleiro",
                        "2": "Linha",
                        "3": "Árbitro"
                    }

                    if texto in opcoes:

                        tipo = opcoes[texto]

                        if tipo not in usuarios[numero]["tipos"]:
                            usuarios[numero]["tipos"].append(tipo)

                        usuarios[numero]["etapa"] = "tipo_mais"

                        enviar(numero, f"""✅ {tipo} adicionado!

Deseja adicionar mais tipos? (S/N)
""")
                        return "ok"

                if etapa == "tipo_mais":

                    if texto == "s":

                        escolhidos = usuarios[numero]["tipos"]

                        opcoes = {
                            "1": "Goleiro",
                            "2": "Linha",
                            "3": "Árbitro"
                        }

                        lista = ""
                        novo_map = {}
                        i = 1

                        for k, v in opcoes.items():
                            if v not in escolhidos:
                                novo_map[str(i)] = v
                                lista += f"{i} {v}\n"
                                i += 1

                        usuarios[numero]["map_tipos"] = novo_map
                        usuarios[numero]["etapa"] = "tipo"

                        enviar(numero, "⚽ Escolha outro tipo:\n\n" + lista)
                        return "ok"

                    else:

                        dados = usuarios[numero]

                        conn = sqlite3.connect("lendarios.db")
                        cursor = conn.cursor()

                        cursor.execute("""
                        INSERT INTO atletas (numero, nome, cidades, tipos)
                        VALUES (?, ?, ?, ?)
                        """, (
                            numero,
                            dados["nome"],
                            ",".join(dados["cidades"]),
                            ",".join(dados["tipos"])
                        ))

                        conn.commit()
                        conn.close()

                        enviar(numero, f"""🏆 Cadastro concluído!

Nome: {dados['nome']}
Cidades: {', '.join(dados['cidades'])}
Tipos: {', '.join(dados['tipos'])}
""")

                        del usuarios[numero]
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

            else:
                enviar(numero, """🏆 LENDÁRIOS

1️⃣ Cadastro de atleta
2️⃣ Solicitar atleta
3️⃣ Ver jogos
4️⃣ Falar com administrador
""")
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
# START
# =========================
if __name__ == "__main__":
    app.run(port=5000)

