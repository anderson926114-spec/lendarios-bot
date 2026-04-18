from flask import Flask, request
import requests

app = Flask(__name__)

# =========================
# CONFIG
# =========================
TOKEN = "EAAsCShhhFUoBRGTZCd2ye7vngDcsXxExbvZAqKDH267WUAwXZCcxtorbo6CyAKqZAt365BSZBdO35b5LCjm3UIR9CymZBRjbZCEgHFgxKeHSkMLDUIAGpByKVqrX0ItzmWpqG8ZAauP4U6VHLdf7IkSUXje5ioms5LWfpWo2YnrsE4UgAMauTaRrTb3tghy14fOVDyvWyZBkFfH93biZAYGQ1iYqSU7ehUwQ1Ksk0xdBGxs7BRn9g75ZAgD0cJYL7pbdRszVMRGSVdiEDwTWLcebHHsL15P"
PHONE_NUMBER_ID = "1094450353745202"
VERIFY_TOKEN = "lendarios_token"

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

    try:
        data = request.get_json()
        msg = data["entry"][0]["changes"][0]["value"]["messages"][0]

        numero = normalizar_numero(msg["from"])
        texto = msg["text"]["body"].strip().lower()

        print("MSG:", numero, texto)

        # =========================
        # MENU INICIAL
        # =========================
        if numero not in usuarios and numero not in solicitacoes:

            if texto == "1":
                usuarios[numero] = {"etapa": "cpf"}
                enviar(numero, "Digite seu CPF:")
                return "ok"

            elif texto == "2":
                solicitacoes[numero] = {"etapa": "cpf"}
                enviar(numero, "Digite seu CPF:")
                return "ok"

            else:
                menu(numero)
                return "ok"

        # =========================
        # CADASTRO
        # =========================
        if numero in usuarios:
            u = usuarios[numero]

            if u["etapa"] == "cpf":
                u["cpf"] = texto
                u["etapa"] = "nome"
                enviar(numero, "Digite seu nome:")
                return "ok"

            elif u["etapa"] == "nome":
                u["nome"] = texto
                u["etapa"] = "cidade"
                lista = "\n".join([f"{k} {v}" for k,v in CIDADES.items()])
                enviar(numero, "Escolha cidade:\n" + lista)
                return "ok"

            elif u["etapa"] == "cidade" and texto in CIDADES:
                u["cidade"] = CIDADES[texto]
                u["etapa"] = "tipo"
                lista = "\n".join([f"{k} {v}" for k,v in TIPOS.items()])
                enviar(numero, "Escolha tipo:\n" + lista)
                return "ok"

            elif u["etapa"] == "tipo" and texto in TIPOS:
                u["tipo"] = TIPOS[texto]
                u["etapa"] = "pix"
                enviar(numero, "Digite sua chave PIX:")
                return "ok"

            elif u["etapa"] == "pix":
                u["pix"] = texto

                enviar(numero, f"""✅ Cadastro realizado!

Nome: {u['nome']}
Cidade: {u['cidade']}
Tipo: {u['tipo']}
PIX: {u['pix']}
""")

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

            elif s["etapa"] == "cidade" and texto in CIDADES:
                s["cidade"] = CIDADES[texto]
                s["etapa"] = "campo"
                enviar(numero, "Nome do campo:")
                return "ok"

            elif s["etapa"] == "campo":
                s["campo"] = texto
                s["etapa"] = "tipo_campo"
                lista = "\n".join([f"{k} {v}" for k,v in CAMPOS.items()])
                enviar(numero, "Tipo de campo:\n" + lista)
                return "ok"

            elif s["etapa"] == "tipo_campo" and texto in CAMPOS:
                s["tipo_campo"] = CAMPOS[texto]
                s["etapa"] = "tipo"
                lista = "\n".join([f"{k} {v}" for k,v in TIPOS.items()])
                enviar(numero, "Tipo atleta:\n" + lista)
                return "ok"

            elif s["etapa"] == "tipo" and texto in TIPOS:
                s["tipo"] = TIPOS[texto]
                s["etapa"] = "qtd"
                enviar(numero, "Quantidade de atletas:")
                return "ok"

            elif s["etapa"] == "qtd":
                try:
                    s["qtd"] = int(texto)
                except:
                    enviar(numero, "Digite apenas números.")
                    return "ok"

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

                enviar_para_make("solicitacao", s)

                del solicitacoes[numero]
                return "ok"

        # fallback
        menu(numero)
        return "ok"

    except Exception as e:
        print("ERRO:", e)
        return "ok", 200

# =========================
# ROTAS EXTRAS
# =========================
@app.route("/")
def home():
    return "BOT ONLINE"

@app.route("/teste")
def teste():
    try:
        r = requests.post(
            MAKE_WEBHOOK_URL,
            json={"teste": "funcionando"}
        )
        return f"ENVIADO | STATUS: {r.status_code} | RESPOSTA: {r.text}"
    except Exception as e:
        return f"ERRO: {str(e)}"

@app.route("/teste")
def teste():
    requests.post("https://hook.us2.make.com/gcgl67hj5uaww80orbjetvjrsuz7ya78",
                  json={"teste": "funcionando"})
    return "enviado"
# =========================
# START
# =========================
if __name__ == "__main__":
    app.run(port=5000)
