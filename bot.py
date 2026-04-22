from flask import Flask, request
import requests

app = Flask(__name__)

TOKEN = "EAAsCShhhFUoBRVi2959mlqUIZClFAqyEuZAg3DcgOa5VY20QQkJMFjcizZA6Cy3DocNBE3uxRawmaBhXh8kXOKXl9UH9uLEh13tfZAWuqOYtz1LKHhZBLmMfUVUmVPqvaT9Q4ObGCyZB3qYCMZCMmEo5ZCbsdsuEkdhqWIQ8JHrvPzTm6HWgUcxSgTBgW2fAwNVOuKvcZBPmTwHB1Kuwbs0NQekO5jO6M4TvdZArIX9IPoQCjWki2V4uU0deiWuNcML2aRymBXvQ2t7qtJbZCdZBN090KmZCq"
PHONE_NUMBER_ID = "1094450353745202"
VERIFY_TOKEN = "lendarios_token"

MAKE_WEBHOOK_URL = "https://hook.us2.make.com/pcgibko4cd3yqr5375q4nsy5fgpip4m2"

usuarios = {}

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

def normalizar(numero):
    numero = "".join(filter(str.isdigit, numero))
    if numero.startswith("55") and len(numero) == 12:
        numero = numero[:4] + "9" + numero[4:]
    return numero

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

def enviar_make(dados):
    requests.post(MAKE_WEBHOOK_URL, json=dados)
    print("ENVIADO PARA MAKE:", dados)

def menu(numero):
    enviar(numero, "1 Cadastro\n2 Solicitação\n0 Sair")

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
        numero = normalizar(msg["from"])
        texto = msg["text"]["body"].strip().lower()

        print("MSG:", numero, texto)

        # INÍCIO
        if numero not in usuarios:
            if texto == "1":
                usuarios[numero] = {"etapa": "cpf", "cidades": [], "tipos": []}
                enviar(numero, "Digite seu CPF:")
                return "ok"

            menu(numero)
            return "ok"

        u = usuarios[numero]

        # CPF
        if u["etapa"] == "cpf":
            u["cpf"] = texto
            u["etapa"] = "nome"
            enviar(numero, "Digite seu nome:")
            return "ok"

        # NOME
        if u["etapa"] == "nome":
            u["nome"] = texto
            u["etapa"] = "cidade"

            lista = "\n".join([f"{k} {v}" for k,v in CIDADES.items()])
            enviar(numero, "Escolha cidade:\n" + lista)
            return "ok"

        # CIDADE
        if u["etapa"] == "cidade" and texto in CIDADES:
            cidade = CIDADES[texto]

            if cidade not in u["cidades"]:
                u["cidades"].append(cidade)

            u["etapa"] = "cidade_mais"
            enviar(numero, "Deseja adicionar mais cidade? (S/N)")
            return "ok"

        if u["etapa"] == "cidade_mais":
            if texto in ["s", "sim"]:
                lista = "\n".join([f"{k} {v}" for k,v in CIDADES.items() if v not in u["cidades"]])
                u["etapa"] = "cidade"
                enviar(numero, "Escolha outra cidade:\n" + lista)
                return "ok"

            u["etapa"] = "tipo"
            lista = "\n".join([f"{k} {v}" for k,v in TIPOS.items()])
            enviar(numero, "Escolha tipo:\n" + lista)
            return "ok"

        # TIPO
        if u["etapa"] == "tipo" and texto in TIPOS:
            tipo = TIPOS[texto]

            if tipo not in u["tipos"]:
                u["tipos"].append(tipo)

            u["etapa"] = "tipo_mais"
            enviar(numero, "Deseja adicionar mais tipo? (S/N)")
            return "ok"

        if u["etapa"] == "tipo_mais":
            if texto in ["s", "sim"]:
                lista = "\n".join([f"{k} {v}" for k,v in TIPOS.items() if v not in u["tipos"]])
                u["etapa"] = "tipo"
                enviar(numero, "Escolha outro tipo:\n" + lista)
                return "ok"

            u["etapa"] = "pix"
            enviar(numero, "Digite sua chave PIX:")
            return "ok"

        # PIX 
        if u["etapa"] == "pix":
            u["pix"] = texto

            enviar(numero, "Cadastro realizado com sucesso!")

            enviar_make({
                "cpf": u["cpf"],
                "nome": u["nome"],
                "cidades": ",".join(u["cidades"]),
                "tipos": ",".join(u["tipos"]),
                "pix": u["pix"],
                "telefone": numero
            })

            print(">>> ENVIANDO PARA MAKE:", dados)

            requesrs.post(MAKE_WEBHOOK_URL, json=dados)

            del usuarios[numero]
            return "ok"

    except Exception as e:
        print("ERRO:", e)

    return "ok"

@app.route("/")
def home():
    return "BOT ONLINE"

if __name__ == "__main__":
    app.run(port=5000)
