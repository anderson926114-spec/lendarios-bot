from flask import Flask, request
import requests

app = Flask(__name__)

# ================= CONFIG =================
TOKEN = "from flask import Flask, request
import requests

app = Flask(__name__)

# ================= CONFIG =================
TOKEN = "EAAsCShhhFUoBRaqmytO9xz3dxxCXgaTnHPLy26EfCbAP9JIStDc4PV8ozPqEb63K1ZCp9V7mi6ZA4QG0kpdx2wYkWZBZBVadfZAZBQIj3rYruIJFNZA11PH9hixbLnGP5y0Q849oSgauJweKr7V5dTrm7hqriqNLZAp8SaGRYtI5KUKou7WBkVQUH4OjOEG3AeOWwgvMFd1mpySf0UEoRW7yY7WmeePSbOHBmvdMvcE8GemrH1PQZC6xgHV08ueLpLAwPXY5shWZAl6zPuFnIgHNFaaNvb"
PHONE_NUMBER_ID = "1094450353745202"
VERIFY_TOKEN = "lendarios_token"


# 🔗 APENAS 1 WEBHOOK (MAKE)
MAKE_WEBHOOK = "https://hook.us2.make.com/pcgibko4cd3yqr5375q4nsy5fgpip4m2"

usuarios = {}
solicitacoes = {}

# ================= DADOS =================
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

# ================= FUNÇÕES =================
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

def enviar_make(dados):
    try:
        requests.post(MAKE_WEBHOOK, json=dados)
        print("ENVIADO PARA MAKE:", dados)
    except Exception as e:
        print("ERRO AO ENVIAR:", e)

def menu(numero):
    enviar(numero,
        "🏆 LENDÁRIOS\n\n"
        "1 Cadastro\n"
        "2 Solicitação\n"
        "0 Sair"
    )

def menu_solicitacao(numero):
    enviar(numero,
        "📋 SOLICITAÇÕES\n\n"
        "1 Nova solicitação\n"
        "2 Minhas solicitações\n"
        "0 Voltar"
    )

# ================= WEBHOOK =================
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

        # ================= MENU PRINCIPAL =================
        if numero not in usuarios and numero not in solicitacoes:

            if texto == "1":
                usuarios[numero] = {
                    "etapa": "cpf",
                    "cidades": [],
                    "tipos": []
                }
                enviar(numero, "Digite seu CPF:")
                return "ok"

            elif texto == "2":
                solicitacoes[numero] = {"etapa": "menu"}
                menu_solicitacao(numero)
                return "ok"

            else:
                menu(numero)
                return "ok"

        # ================= CADASTRO =================
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
                cidade = CIDADES[texto]

                if cidade not in u["cidades"]:
                    u["cidades"].append(cidade)

                u["etapa"] = "cidade_mais"
                enviar(numero, "Adicionar mais cidade? (S/N)")
                return "ok"

            if u["etapa"] == "cidade_mais":

                if texto in ["s", "sim"]:
                    lista = "\n".join([
                        f"{k} {v}" for k,v in CIDADES.items()
                        if v not in u["cidades"]
                    ])
                    u["etapa"] = "cidade"
                    enviar(numero, "Escolha outra cidade:\n" + lista)
                    return "ok"

                u["etapa"] = "tipo"
                lista = "\n".join([f"{k} {v[0]}" for k,v in TIPOS.items()])
                enviar(numero, "Escolha tipo:\n" + lista)
                return "ok"

            if u["etapa"] == "tipo" and texto in TIPOS:
                tipo = TIPOS[texto][0]

                if tipo not in u["tipos"]:
                    u["tipos"].append(tipo)

                u["etapa"] = "tipo_mais"
                enviar(numero, "Adicionar mais tipo? (S/N)")
                return "ok"

            if u["etapa"] == "tipo_mais":

                if texto in ["s", "sim"]:
                    lista = "\n".join([
                        f"{k} {v[0]}" for k,v in TIPOS.items()
                        if v[0] not in u["tipos"]
                    ])
                    u["etapa"] = "tipo"
                    enviar(numero, "Escolha outro tipo:\n" + lista)
                    return "ok"

                u["etapa"] = "pix"
                enviar(numero, "Digite sua chave PIX:")
                return "ok"

            if u["etapa"] == "pix":
                u["pix"] = texto

                enviar(numero, "✅ Cadastro realizado com sucesso!")

                enviar_make({
                    "tipo": "cadastro",
                    "cpf": u["cpf"],
                    "nome": u["nome"],
                    "cidades": ",".join(u["cidades"]),
                    "tipos": ",".join(u["tipos"]),
                    "pix": u["pix"],
                    "telefone": numero
                })

                del usuarios[numero]
                return "ok"

        # ================= SOLICITAÇÃO =================
        if numero in solicitacoes:
            s = solicitacoes[numero]

            if s["etapa"] == "menu":

                if texto == "1":
                    s["etapa"] = "cpf"
                    enviar(numero, "Digite seu CPF:")
                    return "ok"

                elif texto == "2":
                    enviar(numero, "📄 Em breve suas solicitações aparecerão aqui")
                    return "ok"

                elif texto == "0":
                    del solicitacoes[numero]
                    menu(numero)
                    return "ok"

                else:
                    menu_solicitacao(numero)
                    return "ok"

            if s["etapa"] == "cpf":
                s["cpf"] = texto
                s["etapa"] = "campo"
                enviar(numero, "Digite o nome do campo:")
                return "ok"

            if s["etapa"] == "campo":
                s["campo"] = texto
                s["etapa"] = "tipo_campo"

                lista = "\n".join([f"{k} {v}" for k,v in CAMPOS.items()])
                enviar(numero, "Tipo de campo:\n" + lista)
                return "ok"

            if s["etapa"] == "tipo_campo" and texto in CAMPOS:
                s["tipo_campo"] = CAMPOS[texto]
                s["etapa"] = "cidade"

                lista = "\n".join([f"{k} {v}" for k,v in CIDADES.items()])
                enviar(numero, "Cidade:\n" + lista)
                return "ok"

            if s["etapa"] == "cidade" and texto in CIDADES:
                s["cidade"] = CIDADES[texto]
                s["etapa"] = "tipo"

                lista = "\n".join([f"{k} {v[0]}" for k,v in TIPOS.items()])
                enviar(numero, "Tipo atleta:\n" + lista)
                return "ok"

            if s["etapa"] == "tipo" and texto in TIPOS:
                nome, valor = TIPOS[texto]

                if "itens" not in s:
                    s["itens"] = []

                s["temp"] = (nome, valor)
                s["etapa"] = "qtd"
                enviar(numero, f"Quantidade de {nome}:")
                return "ok"

            if s["etapa"] == "qtd":
                try:
                    qtd = int(texto)
                except:
                    enviar(numero, "Digite um número válido")
                    return "ok"

                nome, valor = s["temp"]

                s["itens"].append({
                    "tipo": nome,
                    "qtd": qtd,
                    "valor": qtd * valor
                })

                s["etapa"] = "mais"
                enviar(numero, "Adicionar outro tipo? (S/N)")
                return "ok"

            if s["etapa"] == "mais":

                if texto in ["s", "sim"]:
                    lista = "\n".join([f"{k} {v[0]}" for k,v in TIPOS.items()])
                    s["etapa"] = "tipo"
                    enviar(numero, "Escolha outro tipo:\n" + lista)
                    return "ok"

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

                enviar_make({
                    "tipo": "solicitacao",
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
"
PHONE_NUMBER_ID = "1094450353745202"
VERIFY_TOKEN = "lendarios_token"


# 🔗 APENAS 1 WEBHOOK (MAKE)
MAKE_WEBHOOK = "https://hook.us2.make.com/pcgibko4cd3yqr5375q4nsy5fgpip4m2"

usuarios = {}
solicitacoes = {}

# ================= DADOS =================
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

# ================= FUNÇÕES =================
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

def enviar_make(dados):
    try:
        requests.post(MAKE_WEBHOOK, json=dados)
        print("ENVIADO PARA MAKE:", dados)
    except Exception as e:
        print("ERRO AO ENVIAR:", e)

def menu(numero):
    enviar(numero,
        "🏆 LENDÁRIOS\n\n"
        "1 Cadastro\n"
        "2 Solicitação\n"
        "0 Sair"
    )

def menu_solicitacao(numero):
    enviar(numero,
        "📋 SOLICITAÇÕES\n\n"
        "1 Nova solicitação\n"
        "2 Minhas solicitações\n"
        "0 Voltar"
    )

# ================= WEBHOOK =================
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

        # ================= MENU PRINCIPAL =================
        if numero not in usuarios and numero not in solicitacoes:

            if texto == "1":
                usuarios[numero] = {
                    "etapa": "cpf",
                    "cidades": [],
                    "tipos": []
                }
                enviar(numero, "Digite seu CPF:")
                return "ok"

            elif texto == "2":
                solicitacoes[numero] = {"etapa": "menu"}
                menu_solicitacao(numero)
                return "ok"

            else:
                menu(numero)
                return "ok"

        # ================= CADASTRO =================
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
                cidade = CIDADES[texto]

                if cidade not in u["cidades"]:
                    u["cidades"].append(cidade)

                u["etapa"] = "cidade_mais"
                enviar(numero, "Adicionar mais cidade? (S/N)")
                return "ok"

            if u["etapa"] == "cidade_mais":

                if texto in ["s", "sim"]:
                    lista = "\n".join([
                        f"{k} {v}" for k,v in CIDADES.items()
                        if v not in u["cidades"]
                    ])
                    u["etapa"] = "cidade"
                    enviar(numero, "Escolha outra cidade:\n" + lista)
                    return "ok"

                u["etapa"] = "tipo"
                lista = "\n".join([f"{k} {v[0]}" for k,v in TIPOS.items()])
                enviar(numero, "Escolha tipo:\n" + lista)
                return "ok"

            if u["etapa"] == "tipo" and texto in TIPOS:
                tipo = TIPOS[texto][0]

                if tipo not in u["tipos"]:
                    u["tipos"].append(tipo)

                u["etapa"] = "tipo_mais"
                enviar(numero, "Adicionar mais tipo? (S/N)")
                return "ok"

            if u["etapa"] == "tipo_mais":

                if texto in ["s", "sim"]:
                    lista = "\n".join([
                        f"{k} {v[0]}" for k,v in TIPOS.items()
                        if v[0] not in u["tipos"]
                    ])
                    u["etapa"] = "tipo"
                    enviar(numero, "Escolha outro tipo:\n" + lista)
                    return "ok"

                u["etapa"] = "pix"
                enviar(numero, "Digite sua chave PIX:")
                return "ok"

            if u["etapa"] == "pix":
                u["pix"] = texto

                enviar(numero, "✅ Cadastro realizado com sucesso!")

                enviar_make({
                    "tipo": "cadastro",
                    "cpf": u["cpf"],
                    "nome": u["nome"],
                    "cidades": ",".join(u["cidades"]),
                    "tipos": ",".join(u["tipos"]),
                    "pix": u["pix"],
                    "telefone": numero
                })

                del usuarios[numero]
                return "ok"

        # ================= SOLICITAÇÃO =================
        if numero in solicitacoes:
            s = solicitacoes[numero]

            if s["etapa"] == "menu":

                if texto == "1":
                    s["etapa"] = "cpf"
                    enviar(numero, "Digite seu CPF:")
                    return "ok"

                elif texto == "2":
                    enviar(numero, "📄 Em breve suas solicitações aparecerão aqui")
                    return "ok"

                elif texto == "0":
                    del solicitacoes[numero]
                    menu(numero)
                    return "ok"

                else:
                    menu_solicitacao(numero)
                    return "ok"

            if s["etapa"] == "cpf":
                s["cpf"] = texto
                s["etapa"] = "campo"
                enviar(numero, "Digite o nome do campo:")
                return "ok"

            if s["etapa"] == "campo":
                s["campo"] = texto
                s["etapa"] = "tipo_campo"

                lista = "\n".join([f"{k} {v}" for k,v in CAMPOS.items()])
                enviar(numero, "Tipo de campo:\n" + lista)
                return "ok"

            if s["etapa"] == "tipo_campo" and texto in CAMPOS:
                s["tipo_campo"] = CAMPOS[texto]
                s["etapa"] = "cidade"

                lista = "\n".join([f"{k} {v}" for k,v in CIDADES.items()])
                enviar(numero, "Cidade:\n" + lista)
                return "ok"

            if s["etapa"] == "cidade" and texto in CIDADES:
                s["cidade"] = CIDADES[texto]
                s["etapa"] = "tipo"

                lista = "\n".join([f"{k} {v[0]}" for k,v in TIPOS.items()])
                enviar(numero, "Tipo atleta:\n" + lista)
                return "ok"

            if s["etapa"] == "tipo" and texto in TIPOS:
                nome, valor = TIPOS[texto]

                if "itens" not in s:
                    s["itens"] = []

                s["temp"] = (nome, valor)
                s["etapa"] = "qtd"
                enviar(numero, f"Quantidade de {nome}:")
                return "ok"

            if s["etapa"] == "qtd":
                try:
                    qtd = int(texto)
                except:
                    enviar(numero, "Digite um número válido")
                    return "ok"

                nome, valor = s["temp"]

                s["itens"].append({
                    "tipo": nome,
                    "qtd": qtd,
                    "valor": qtd * valor
                })

                s["etapa"] = "mais"
                enviar(numero, "Adicionar outro tipo? (S/N)")
                return "ok"

            if s["etapa"] == "mais":

                if texto in ["s", "sim"]:
                    lista = "\n".join([f"{k} {v[0]}" for k,v in TIPOS.items()])
                    s["etapa"] = "tipo"
                    enviar(numero, "Escolha outro tipo:\n" + lista)
                    return "ok"

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

                enviar_make({
                    "tipo": "solicitacao",
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
