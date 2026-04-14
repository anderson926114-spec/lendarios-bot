from flask import Flask, request
import requests
import sqlite3

app = Flask(__name__)

TOKEN = "EAAsCShhhFUoBREHsyailbQZBqBS7QeWfgyS9Uxbswl1uZCPIgWZA1WpW9YzZAvMzSkr5quYG6Kmu05xbpgMK0ScBojsZC5jznykBlg6Eem8AyWM0tysQv4EcL4Wd0EDsnZBbv4udRIxs90V6yhPYZAF6y63TaaCG4NJ1czQwTennVCYETJ3Ka5XhRewrPXPVO5ngWddUA782hn5ldMqBTLjo4tvO0pLl8Snd8HZCHDJV4x49PrZCuZBZAXmOevp65WbRcyaVcyZB32eXAZBNT3ZCYVULPI6jPAQgZDZD"
PHONE_NUMBER_ID = "1094450353745202"
VERIFY_TOKEN = "lendarios_token"

usuarios = {}
solicitacoes_fluxo = {}
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
def conectar():
    return sqlite3.connect("lendarios.db")

# =========================
# MATCH AUTOMÁTICO
# =========================
def buscar_atletas(cidade, tipo):
    conn = conectar()
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

def disparar_match(solicitacao_id, cidade, tipo, quantidade):

    atletas = buscar_atletas(cidade, tipo)

    if not atletas:
        return

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
# MENU
# =========================
def menu(numero):
    enviar(numero, """🏆 LENDÁRIOS

1 Cadastro atleta
2 Solicitar atleta
3 Avaliações
4 Admin
5 Sair
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

                enviar(numero, "✅ Confirmado!")

                if len(controle["aceitos"]) == controle["total"]:
                    for n in controle["aceitos"]:
                        enviar(n, "🏆 Time completo!")

                return "ok"

            if texto == "2":
                enviar(numero, "❌ Recusado")
                return "ok"

        # =========================
        # MENU
        # =========================
        if numero not in solicitacoes_fluxo:

            if texto == "2":
                solicitacoes_fluxo[numero] = {"etapa": "cidade"}
                enviar(numero, "📍 Cidade:")
                return "ok"

            menu(numero)
            return "ok"

        # =========================
        # FLUXO SOLICITAÇÃO
        # =========================
        s = solicitacoes_fluxo[numero]

        if s["etapa"] == "cidade":
            s["cidade"] = texto
            s["etapa"] = "tipo"
            enviar(numero, "⚽ Tipo (Goleiro/Jogador Linha/Árbitro):")
            return "ok"

        if s["etapa"] == "tipo":
            s["tipo"] = texto
            s["etapa"] = "qtd"
            enviar(numero, "👥 Quantidade:")
            return "ok"

        if s["etapa"] == "qtd":

            qtd = int(texto)

            conn = conectar()
            cursor = conn.cursor()

            cursor.execute("""
            INSERT INTO solicitacoes (cidade,tipo,quantidade)
            VALUES (?,?,?)
            """, (s["cidade"], s["tipo"], qtd))

            solicitacao_id = cursor.lastrowid

            conn.commit()
            conn.close()

            # 🚀 AQUI A MÁGICA
            disparar_match(solicitacao_id, s["cidade"], s["tipo"], qtd)

            enviar(numero, "🚀 Solicitação criada e jogadores acionados!")

            del solicitacoes_fluxo[numero]
            return "ok"

    except Exception as e:
        print("ERRO:", e)

    return "ok"

@app.route("/")
def home():
    return "LENDARIOS FULL ONLINE"

if __name__ == "__main__":
    app.run(port=5000)
