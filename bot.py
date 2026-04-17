from flask import Flask, request
import requests
import sqlite3

app = Flask(__name__)

TOKEN = "EAAsCShhhFUoBRNRnA9Y6C45qzxLQKBAI8ONFDHTGQAwPrquuZCZBCQ2IbMuyjzAEQeo711RNSjO01vxzENl8tpazlDOligh6WoZBl3qodphq40niZCcZBDiEmLt5vAEHyMFsG9cy1zU0n4HKwMrQ5qHTxpyxUp5ZCzZB0KsV5ZA9Jdu7zuuZC0GQ5Wqo6rPmcKMtNM8gJ9RHYyJFtyVbhrRlUZBlD2kyuGv59wrJra55JyaxDPuPZABsn50gi8Wv9JNhsetxjJETmMEM0EaK0NU37DH2naK"
PHONE_NUMBER_ID = "1094450353745202"
VERIFY_TOKEN = "lendarios_token"

# 🔥 WEBHOOK DO MAKE
MAKE_WEBHOOK_URL = "https://hook.us2.make.com/gcgl67hj5uaww80orbjetvjrsuz7ya78"

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
# ENVIAR WHATSAPP
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

    requests.post(url, headers=headers, json=payload)

# =========================
# ENVIAR PARA MAKE
# =========================
def enviar_para_make(tipo, dados):
    try:
        requests.post(MAKE_WEBHOOK_URL, json={
            "tipo": tipo,
            "dados": dados
        })
    except:
        pass

# =========================
# DADOS
# =========================
CIDADES = {
    "1": "São José",
    "2": "Palhoça",
    "3": "Biguaçu",
    "4": "Florianópolis Continente",
    "5": "Florianópolis Ilha"
}

TIPOS = {
    "1": "Goleiro",
    "2": "Jogador Linha",
    "3": "Árbitro"
}

CAMPOS = {
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
3 📋 Jogos
4 ⭐ Avaliações
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

        print("MSG:", numero, texto)

        # =========================
        # MENU
        # =========================
        if numero not in usuarios and numero not in solicitacoes:

            if texto == "1":
                usuarios[numero] = {"etapa": "cpf"}
                enviar(numero, "Digite seu CPF:")
                return "ok"

            if texto == "2":
                solicitacoes[numero] = {"etapa": "cpf"}
                enviar(numero, "Digite seu CPF:")
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
                enviar(numero, "Digite seu nome:")
                return "ok"

            if u["etapa"] == "nome":
                u["nome"] = texto
                u["etapa"] = "cidade"
                lista = "\n".join([f"{k} {v}" for k,v in CIDADES.items()])
                enviar(numero, "Escolha cidade:\n" + lista)
                return "ok"

            if u["etapa"] == "cidade" and texto in CIDADES:
                u["cidade"] = CIDADES[texto]
                u["etapa"] = "tipo"
                lista = "\n".join([f"{k} {v}" for k,v in TIPOS.items()])
                enviar(numero, "Escolha tipo:\n" + lista)
                return "ok"

            if u["etapa"] == "tipo" and texto in TIPOS:
                u["tipo"] = TIPOS[texto]
                u["etapa"] = "pix"
                enviar(numero, "Digite sua chave PIX:")
                return "ok"

            if u["etapa"] == "pix":
                u["pix"] = texto

                enviar(numero, f"""✅ Cadastro realizado!

Nome: {u['nome']}
Cidade: {u['cidade']}
Tipo: {u['tipo']}
PIX: {u['pix']}
""")

                # 🔥 ENVIA PARA MAKE
                enviar_para_make("cadastro", u)

                del usuarios[numero]
                return "ok"

        # =========================
        # SOLICITAÇÃO
        # =========================
        if numero in solicitacoes:
            s = solicitacoes[numero]

            if s["etapa"] == "cpf":
                s["cpf"] = texto
                s["etapa"] = "cidade"
                lista = "\n".join([f"{k} {v}" for k,v in CIDADES.items()])
                enviar(numero, "Cidade:\n" + lista)
                return "ok"

            if s["etapa"] == "cidade" and texto in CIDADES:
                s["cidade"] = CIDADES[texto]
                s["etapa"] = "campo"
                enviar(numero, "Nome do campo:")
                return "ok"

            if s["etapa"] == "campo":
                s["campo"] = texto
                s["etapa"] = "tipo_campo"
                lista = "\n".join([f"{k} {v}" for k,v in CAMPOS.items()])
                enviar(numero, "Tipo de campo:\n" + lista)
                return "ok"

            if s["etapa"] == "tipo_campo" and texto in CAMPOS:
                s["tipo_campo"] = CAMPOS[texto]
                s["etapa"] = "tipo"
                lista = "\n".join([f"{k} {v}" for k,v in TIPOS.items()])
                enviar(numero, "Tipo atleta:\n" + lista)
                return "ok"

            if s["etapa"] == "tipo" and texto in TIPOS:
                s["tipo"] = TIPOS[texto]
                s["etapa"] = "qtd"
                enviar(numero, "Quantidade de atletas:")
                return "ok"

            if s["etapa"] == "qtd":
                s["qtd"] = int(texto)

                valores = {
                    "Goleiro": 40,
                    "Jogador Linha": 30,
                    "Árbitro": 50
                }

                total = valores[s["tipo"]] * s["qtd"]
                s["valor"] = total

                enviar(numero, f"""✅ Solicitação criada!

Cidade: {s['cidade']}
Campo: {s['campo']}
Tipo: {s['tipo']}
Qtd: {s['qtd']}
Valor: R${total}
""")

                # 🔥 ENVIA PARA MAKE
                enviar_para_make("solicitacao", s)

                del solicitacoes[numero]
                return "ok"

        menu(numero)
        return "ok"

    @app.route("/teste")
def teste():
    try:
        r = requests.post(
            "https://hook.us2.make.com/gcgl67hj5uaww80orbjetvjrsuz7ya78",
            json={"teste": "funcionando"}
        )

        return f"ENVIADO | STATUS: {r.status_code} | RESPOSTA: {r.text}"

    except Exception as e:
        return f"ERRO: {str(e)}"

    except Exception as e:
        print("ERRO:", e)

    return "ok", 200

@app.route("/")
def home():
    return "BOT ONLINE"
