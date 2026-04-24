from flask import Flask, request
import requests

app = Flask(__name__)

TOKEN = "EAAsCShhhFUoBRdDdeZCOjR3J6MZB1kxRTsi14AplF0ZAyEa9kRgCo9Y8Xw8ZCspwGU6cr9iJgm6ZARTdTg9dR5mJjUpSeZBCZAkuZBAd191Jb5pT4y2KXA9AgRjtovhDcjGgiCN1Bw2dbzoDwq69wD9iUDMFFHXHjSyAfvBqZBaep1DW4iz6xa4cmyMfEiLX8K2C0xqbZARixrA9QVGaqPxeKrCOGsLmdbzyQZAOin0H8ZAp4ow1apZCspnJLkcZAHqijzKQcmMZCBXYHelAsCZCo7zMkZCdUZCXNq"
PHONE_NUMBER_ID = "1094450353745202"
VERIFY_TOKEN = "lendarios_token"

MAKE_ATLETAS = "SEU_WEBHOOK_ATLETAS"
MAKE_SOLICITACOES = "SEU_WEBHOOK_SOLICITACOES"

usuarios = {}
solicitacoes = {}

CIDADES = {
    "1": "São José",
    "2": "Palhoça",
    "3": "Biguaçu",
    "4": "Florianópolis Continente",
    "5": "Florianópolis Ilha"
}

TIPOS = {
    "1": ("Goleiro", 40),
    "2": ("Jogador Linha", 30),
    "3": ("Árbitro", 50)
}

CAMPOS = {
    "1": "Campo Oficial",
    "2": "Society",
    "3": "Futsal"
}

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

def menu(numero):
    enviar(numero, "🏆 LENDÁRIOS\n\n1 Cadastro\n2 Solicitação\n0 Sair")

def menu_solicitacao(numero):
    enviar(numero, "📋 SOLICITAÇÕES\n\n1 Nova solicitação\n2 Minhas solicitações\n0 Voltar")

def enviar_make(url, dados):
    requests.post(url, json=dados)
    print("ENVIADO:", dados)

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

        # ================= MENU PRINCIPAL =================
        if numero not in usuarios and numero not in solicitacoes:

            if texto == "1":
                usuarios[numero] = {"etapa": "cpf"}
                enviar(numero, "Digite seu CPF:")
                return "ok"

            if texto == "2":
                menu_solicitacao(numero)
                solicitacoes[numero] = {"etapa": "menu"}
                return "ok"

            menu(numero)
            return "ok"

        # ================= MENU SOLICITAÇÃO =================
        if numero in solicitacoes:

            s = solicitacoes[numero]

            if s["etapa"] == "menu":

                if texto == "1":
                    s["etapa"] = "cpf"
                    enviar(numero, "Digite seu CPF:")
                    return "ok"

                if texto == "2":
                    enviar(numero, "📄 Em breve suas solicitações aparecerão aqui")
                    return "ok"

                if texto == "0":
                    del solicitacoes[numero]
                    menu(numero)
                    return "ok"

                menu_solicitacao(numero)
                return "ok"

            # CPF
            if s["etapa"] == "cpf":
                s["cpf"] = texto
                s["etapa"] = "campo_nome"
                enviar(numero, "Digite o nome do campo:")
                return "ok"

            # NOME CAMPO
            if s["etapa"] == "campo_nome":
                s["campo"] = texto
                s["etapa"] = "tipo_campo"

                lista = "\n".join([f"{k} {v}" for k,v in CAMPOS.items()])
                enviar(numero, "Tipo de campo:\n" + lista)
                return "ok"

            # TIPO CAMPO
            if s["etapa"] == "tipo_campo" and texto in CAMPOS:
                s["tipo_campo"] = CAMPOS[texto]
                s["etapa"] = "cidade"

                lista = "\n".join([f"{k} {v}" for k,v in CIDADES.items()])
                enviar(numero, "Cidade:\n" + lista)
                return "ok"

            # CIDADE
            if s["etapa"] == "cidade" and texto in CIDADES:
                s["cidade"] = CIDADES[texto]
                s["etapa"] = "tipo"

                lista = "\n".join([f"{k} {v[0]}" for k,v in TIPOS.items()])
                enviar(numero, "Tipo atleta:\n" + lista)
                return "ok"

            # TIPO
            if s["etapa"] == "tipo" and texto in TIPOS:
                nome_tipo, valor = TIPOS[texto]

                if "itens" not in s:
                    s["itens"] = []

                s["tipo_temp"] = (nome_tipo, valor)
                s["etapa"] = "quantidade"
                enviar(numero, f"Quantidade de {nome_tipo}:")
                return "ok"

            # QUANTIDADE
            if s["etapa"] == "quantidade":
                qtd = int(texto)
                nome_tipo, valor = s["tipo_temp"]

                s["itens"].append({
                    "tipo": nome_tipo,
                    "qtd": qtd,
                    "valor": valor * qtd
                })

                s["etapa"] = "mais_tipo"
                enviar(numero, "Adicionar outro tipo? (S/N)")
                return "ok"

            if s["etapa"] == "mais_tipo":
                if texto in ["s", "sim"]:
                    lista = "\n".join([f"{k} {v[0]}" for k,v in TIPOS.items()])
                    s["etapa"] = "tipo"
                    enviar(numero, "Escolha outro tipo:\n" + lista)
                    return "ok"

                # FINAL
                total = sum(i["valor"] for i in s["itens"])

                resumo = "\n".join([f"{i['tipo']} x{i['qtd']}" for i in s["itens"]])

                enviar(numero,
                    f"📋 SOLICITAÇÃO CONFIRMADA\n\n"
                    f"Campo: {s['campo']}\n"
                    f"Cidade: {s['cidade']}\n"
                    f"Tipo: {s['tipo_campo']}\n\n"
                    f"{resumo}\n\n"
                    f"💰 Total: R$ {total}\n\n"
                    f"✅ Sucesso!"
                )

                enviar_make(MAKE_SOLICITACOES, {
                    "cpf": s["cpf"],
                    "campo": s["campo"],
                    "cidade": s["cidade"],
                    "tipo_campo": s["tipo_campo"],
                    "itens": resumo,
                    "total": total,
                    "telefone": numero
                })

                del solicitacoes[numero]
                return "ok"

        # fallback
        menu(numero)
        return "ok"

    except Exception as e:
        print("ERRO:", e)

    return "ok"

@app.route("/")
def home():
    return "BOT ONLINE"

if __name__ == "__main__":
    app.run(port=5000)
