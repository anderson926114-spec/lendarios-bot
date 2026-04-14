from flask import Flask, request
import requests
import sqlite3

app = Flask(__name__)

TOKEN = "EAAsCShhhFUoBRMVYMngwgCD7vB7jGGPUMDApntojl1njuCiQ4AF39p0l3Lqe5ZA3WVczxMkZC3LZBqEXVwKbQko6jtjZADcws56SnaeG1XEL3F0Jbdpv8Q0Nt1W77cZBJZCJACz9WrE7SMN5pOTQ51Yvr0lVGjxnWcyAjnZC4UFGKxglskyzOh1ZBqKoq7RkZBxPfwJCfH9uVJvABDdOX1ZBqNEAdBW4QTCR0ak8sIKXhtFXkeb35ZAoZCgR8t1G4zq61IZA26A4OyW19ia73Df1mSpZCcI0NluAZDZD"
PHONE_NUMBER_ID = "1094450353745202"
VERIFY_TOKEN = "lendarios_token"

usuarios = {}
solicitacoes = {}

# =========================
# FUNÇÕES
# =========================
def sn(texto):
    return texto.strip().lower()

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
def init_db():
    conn = sqlite3.connect("lendarios.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS atletas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT,
        cpf TEXT UNIQUE,
        nome TEXT,
        cidades TEXT,
        tipos TEXT,
        campo TEXT,
        pix TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

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
    "2": "Jogador Linha",
    "3": "Árbitro"
}

TIPO_CAMPO = {
    "1": "Campo Oficial",
    "2": "Society",
    "3": "Futsal"
}

# =========================
# MENU
# =========================
def menu(numero):
    enviar(numero, """🏆 LENDÁRIOS

1 🧤 Cadastro de atleta
2 ⚽ Solicitar atleta
3 ⭐ Avaliações
4 👑 Admin
5 🚪 Sair
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

        print("DEBUG:", numero, texto)

        # =========================
        # MENU INICIAL
        # =========================
        if numero not in usuarios:

            if texto == "1":
                usuarios[numero] = {
                    "etapa": "cpf",
                    "cidades": [],
                    "tipos": []
                }
                enviar(numero, "🧾 Digite seu CPF:")
                return "ok"

            elif texto == "2":
                enviar(numero, "⚽ Solicitação em breve disponível.")
                return "ok"

            elif texto == "3":
                enviar(numero, "⭐ Sistema de avaliações em breve.")
                return "ok"

            elif texto == "4":
                enviar(numero, "👑 Área do administrador.")
                return "ok"

            elif texto == "5":
                enviar(numero, "👋 Até mais!")
                return "ok"

            else:
                menu(numero)
                return "ok"

        # =========================
        # FLUXO CADASTRO
        # =========================
        u = usuarios[numero]

        if u["etapa"] == "cpf":

            conn = sqlite3.connect("lendarios.db")
            cursor = conn.cursor()
            cursor.execute("SELECT nome FROM atletas WHERE cpf=?", (texto,))
            existe = cursor.fetchone()
            conn.close()

            if existe:
                enviar(numero, "⚠ CPF já cadastrado!")
                del usuarios[numero]
                return "ok"

            u["cpf"] = texto
            u["etapa"] = "nome"
            enviar(numero, "⚽ Digite seu nome:")
            return "ok"

        if u["etapa"] == "nome":
            u["nome"] = texto
            u["etapa"] = "cidade"

            opcoes = {k:v for k,v in CIDADES.items() if v not in u["cidades"]}
            lista = "\n".join([f"{k} {v}" for k,v in opcoes.items()])

            enviar(numero, "📍 Escolha cidade:\n" + lista)
            return "ok"

        if u["etapa"] == "cidade":

            if texto not in CIDADES:
                enviar(numero, "❌ Opção inválida")
                return "ok"

            cidade = CIDADES[texto]

            if cidade not in u["cidades"]:
                u["cidades"].append(cidade)

            u["etapa"] = "cidade_mais"
            enviar(numero, "Adicionar outra cidade? (S/N)")
            return "ok"

        if u["etapa"] == "cidade_mais":

            resposta = sn(texto)

            if resposta not in ["s","n"]:
                enviar(numero, "❌ Digite S ou N")
                return "ok"

            if resposta == "s":
                u["etapa"] = "cidade"

                opcoes = {k:v for k,v in CIDADES.items() if v not in u["cidades"]}
                lista = "\n".join([f"{k} {v}" for k,v in opcoes.items()])

                enviar(numero, "📍 Escolha outra cidade:\n" + lista)
                return "ok"

            else:
                u["etapa"] = "tipo"

                opcoes = {k:v for k,v in TIPOS.items() if v not in u["tipos"]}
                lista = "\n".join([f"{k} {v}" for k,v in opcoes.items()])

                enviar(numero, "⚽ Escolha tipo:\n" + lista)
                return "ok"

        if u["etapa"] == "tipo":

            if texto not in TIPOS:
                enviar(numero, "❌ Opção inválida")
                return "ok"

            tipo = TIPOS[texto]

            if tipo not in u["tipos"]:
                u["tipos"].append(tipo)

            u["etapa"] = "tipo_mais"
            enviar(numero, "Adicionar outro tipo? (S/N)")
            return "ok"

        if u["etapa"] == "tipo_mais":

            resposta = sn(texto)

            if resposta not in ["s","n"]:
                enviar(numero, "❌ Digite S ou N")
                return "ok"

            if resposta == "s":
                u["etapa"] = "tipo"

                opcoes = {k:v for k,v in TIPOS.items() if v not in u["tipos"]}
                lista = "\n".join([f"{k} {v}" for k,v in opcoes.items()])

                enviar(numero, "⚽ Escolha outro tipo:\n" + lista)
                return "ok"

            else:
                u["etapa"] = "campo"
                enviar(numero, "🏟 Tipo de campo:\n1 Campo Oficial\n2 Society\n3 Futsal")
                return "ok"

        if u["etapa"] == "campo":

            if texto not in TIPO_CAMPO:
                enviar(numero, "❌ Opção inválida")
                return "ok"

            u["campo"] = TIPO_CAMPO[texto]
            u["etapa"] = "pix"
            enviar(numero, "💰 Digite sua chave PIX:")
            return "ok"

        if u["etapa"] == "pix":

            conn = sqlite3.connect("lendarios.db")
            cursor = conn.cursor()

            cursor.execute("""
            INSERT INTO atletas (numero,cpf,nome,cidades,tipos,campo,pix)
            VALUES (?,?,?,?,?,?,?)
            """, (
                numero,
                u["cpf"],
                u["nome"],
                ",".join(u["cidades"]),
                ",".join(u["tipos"]),
                u["campo"],
                texto
            ))

            conn.commit()
            conn.close()

            enviar(numero, "🏆 Cadastro realizado com sucesso!")
            del usuarios[numero]
            return "ok"

    except Exception as e:
        print("ERRO:", e)

    return "ok"

@app.route("/")
def home():
    return "LENDARIOS ONLINE"

if __name__ == "__main__":
    app.run(port=5000)
