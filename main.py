import io
import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, make_response, session
import requests
from flask_mail import Mail, Message # NOVO: Importando Mail
import random 

import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.colors import blue
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from flask_mail import Mail, Message
import cloudinary
import cloudinary.uploader

from dotenv import load_dotenv


load_dotenv()

# =========================
# CONFIG CLOUDINARY
# =========================
cloudinary.config(
  cloud_name = os.getenv("CLOUD_NAME"),
  api_key = os.getenv("API_KEY"),
  api_secret = os.getenv("API_SECRET"),
  secure = True
)

# =========================
# SETUP BASE
# =========================
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

BASE_DIR = '/data/data/com.termux/files/home'
load_dotenv(os.path.join(BASE_DIR, '.env'))


#---------------------------------------------------------------------------
#---------------------------------------------------------------------------
# 1. ROTAS DO SITE
@app.route('/')
def index():
    return render_template("index.html", form=form)
    
#---------------------------------------------------------------------------
@app.route('/formulario')
def form():
    return render_template("form_receita.html", api_autenticacao=api_autenticacao, api_verificacao=api_verificacao)
#---------------------------------------------------------------------------
#---------------------------------------------------------------------------
#---------------------------------------------------------------------------
form = os.getenv('FORM')
api_payment = os.getenv("API")
api_autenticacao = os.getenv("API_AUTENTICACAO")
api_verificacao = os.getenv("API_VERIFICACAO_CODIGO")
CLOUDINARY_URL= os.getenv("CLOUDINARY_URL")
CLOUD_NAME = os.getenv("CLOUD_NAME")
UPLOAD_PRESED = os.getenv("UPLOAD_PRESED")
#---------------------------------------------------------------------------

@app.route("/api")
def api():
    return render_template("pagamento.html", api_payment=api_payment)
#---------------------------------------------------------------------------
@app.route('/receitas')
def gerar_receita():
    # Puxa os dados que salvamos na sessão
    dados_paciente = session.get('dados_paciente', {})
    nome_paciente = dados_paciente.get('nome', 'Paciente não identificado')
    
    # Calcula a idade automaticamente com base na data de nascimento
    idade = ""
    nascimento = dados_paciente.get('nascimento')
    if nascimento:
        try:
            # Pega só o ano do nascimento (formato YYYY-MM-DD)
            ano_nasc = int(nascimento.split('-')[0])
            ano_atual = datetime.now().year
            idade = str(ano_atual - ano_nasc)
        except:
            idade = "N/A"

    dados_receita = {
        "medico": "Dr. Gustavo Sá",
        "crm": "CRM SP 218406",
        "paciente": nome_paciente,
        "idade": idade,
        "data": datetime.now().strftime("%d/%m/%Y"),
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
import io
import qrcode
from PIL import Image  # Usado para garantir nitidez máxima salvando como pixel art
import urllib.request
from flask import make_response, session
from fpdf import FPDF
from datetime import datetime, timedelta

# ENVIAR DOCUMENTOS
#---------------------------------------------------------------------------

#--------------------------------------------------------------------------
# Configurações do servidor SMTP do Gmail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

# Correção para o Apache/mod_wsgi: Garante que haja um remetente padrão caso o env falhe
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

# Inicializa o Mail após as configurações estarem completamente definidas
mail = Mail(app)

@app.route("/enviar-imagem", methods=["POST"])
def enviar_imagem():
    dados_paciente = {
        "nome": request.form.get("nome"),
        "nascimento": request.form.get("nascimento"),
        "telefone": request.form.get("telefone"),
        "email": request.form.get("email"),
        "tipo_documento": request.form.get("tipo_documento"),
    }

    # SALVANDO NA SESSÃO PARA USAR NO PDF E NA RECEITA DEPOIS
    session['dados_paciente'] = dados_paciente

    if "frente" not in request.files or "verso" not in request.files:
        return jsonify({"erro": "Ambos os lados do documento são obrigatórios"}), 400

    arquivo_frente = request.files["frente"]
    arquivo_verso = request.files["verso"]

    if arquivo_frente.filename == "" or arquivo_verso.filename == "":
        return jsonify({"erro": "Por favor, capture a frente e o verso"}), 400

    try:
        # 1. FAZ O UPLOAD (Se der erro aqui, suas chaves do Cloudinary estão erradas no .env)
        upload_frente = cloudinary.uploader.upload(arquivo_frente, tags=["documento_frente", dados_paciente["nome"]])
        upload_verso = cloudinary.uploader.upload(arquivo_verso, tags=["documento_verso", dados_paciente["nome"]])

        # 2. GERA O CÓDIGO E SALVA NA SESSÃO
        codigo_verificacao = str(random.randint(1000, 9999))
        session['codigo_verificacao'] = codigo_verificacao

        # 3. TENTA ENVIAR O EMAIL COM SISTEMA ANTI-FALHA
        if dados_paciente["email"]:
            try:
                msg = Message(
                    "Seu Código de Verificação - Clínica",
                    recipients=[dados_paciente["email"]]
                )
                msg.body = f"Olá {dados_paciente['nome']},\n\nSeu código de verificação é: {codigo_verificacao}"
                mail.send(msg)
                print(f"Email enviado com sucesso para {dados_paciente['email']}")
            except Exception as erro_email:
                # SE O GOOGLE BLOQUEAR, O SERVIDOR NÃO CAI MAIS.
                print("\n=======================================================")
                print("[FALHA NO EMAIL] O Google bloqueou o envio. Você precisa criar uma 'Senha de Aplicativo' no Gmail.")
                print(f"[CÓDIGO SALVO] Use este código na tela para passar: {codigo_verificacao}")
                print("=======================================================\n")

        return jsonify({
            "sucesso": True,
            "mensagem": "Arquivos processados."
        }), 200

    except Exception as e:
        # Se cair aqui, o erro foi no Cloudinary.
        print(f"ERRO FATAL (Cloudinary): {str(e)}")
        return jsonify({"erro": f"Erro no servidor: {str(e)}"}), 500
#---------------------------------------------------------------------------
#---------------------------------------------------------------------------
#---------------------------------------------------------------------------
#---------------------------------------------------------------------------
# VERIFICAR O CÓDIGO
@app.route("/verificar-codigo", methods=["POST"])
def verificar_codigo():
    dados = request.get_json()
    codigo_digitado = dados.get("codigo")
    codigo_real = session.get("codigo_verificacao")

    if not codigo_digitado or not codigo_real:
        return jsonify({"sucesso": False, "erro": "Código não encontrado"}), 400

    if codigo_digitado == codigo_real:
        return jsonify({"sucesso": True, "mensagem": "Código verificado com sucesso!"})
    else:
        return jsonify({"sucesso": False, "erro": "Código incorreto"}), 400
#---------------------------------------------------------------------------


@app.route('/gerar-pdf')
def gerar_pdf():
    dados_paciente = session.get('dados_paciente', {})
    nome = dados_paciente.get('nome', 'Não informado')
    nascimento = dados_paciente.get('nascimento', 'N/A')
    autenticacao = os.getenv("AUTENTICACAO")
    
    # 1. Cálculos de Tempo
    data_criacao = datetime.now()
    data_validade = data_criacao + timedelta(hours=2)
    
    # 2. Geração do QR Code em Alta Resolução Sem Submódulos Problemáticos
    conteudo_qr = f"Paciente: {nome}\nValidade: {data_validade.strftime('%d/%m/%Y %H:%M')} Autenticacao: {autenticacao}"
    
    # Configuração com box_size maior para gerar muitos pixels nativos
    qr = qrcode.QRCode(version=3, box_size=20, border=1)
    qr.add_data(conteudo_qr)
    qr.make(fit=True)
    
    # Cria a imagem padrão usando PIL
    img_qr = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    
    # Converte a imagem do QR Code em bytes garantindo anti-aliasing desligado (NEAREST)
    qr_bytes = io.BytesIO()
    img_qr.save(qr_bytes, format='PNG', compress_level=0)
    qr_bytes.seek(0)
    
    # 3. Configuração do PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(15, 15, 15)
    
    # === INSERINDO A LOGO ===
    url_logo = "https://res.cloudinary.com/doik0qtfr/image/upload/v1782936465/images_1_vuskae.jpg"
    try:
        req = urllib.request.Request(url_logo, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response_url:
            logo_bytes = io.BytesIO(response_url.read())
        pdf.image(logo_bytes, x=15, y=10, w=25)
    except Exception as e:
        print("Aviso: Não foi possível carregar a logo via rede.", e)
    
    # Cabeçalho Profissional
    pdf.set_font("helvetica", "B", 18)
    pdf.set_text_color(20, 50, 90)
    pdf.cell(0, 10, "Consultório Gustavo Sá", align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, "Endereço: Rua Exemplo, 123 - São Paulo, SP", align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_draw_color(20, 50, 90)
    pdf.set_line_width(0.5)
    pdf.line(15, 32, 195, 32)
    
    # Datas
    pdf.ln(8)
    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 5, f"Data Emissão: {data_criacao.strftime('%d/%m/%Y %H:%M')}", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, f"Data Validade: {data_validade.strftime('%d/%m/%Y %H:%M')}", align="R", new_x="LMARGIN", new_y="NEXT")
    
    # DADOS PACIENTE
    pdf.ln(5)
    pdf.set_fill_color(240, 245, 250)
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(20, 50, 90)
    pdf.cell(0, 8, "  DADOS DO PACIENTE", fill=True, new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(2)
    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 7, f"Nome: {nome}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Data de Nascimento: {nascimento}", new_x="LMARGIN", new_y="NEXT")
    
    # PRESCRIÇÃO
    pdf.ln(8)
    pdf.set_font("helvetica", "B", 13)
    pdf.set_text_color(20, 50, 90)
    pdf.cell(0, 8, "PRESCRIÇÃO MÉDICA", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(2)
    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 7, "Uso Subcutâneo:\n\n1. TG 15mg / 0,5ml ..................................................................................... 1 Caixa\n   Administração: Injetável de forma subcutânea conforme orientação.")
    
    # ASSINATURA E QR CODE
    pdf.ln(35)
    posicao_y_bloco = pdf.get_y()
    
    # Insere o QR Code de alta densidade na memória
    try:
        pdf.image(qr_bytes, x=15, y=posicao_y_bloco, w=35)
    except Exception as e:
        print("Aviso: Falha ao renderizar o QR Code.", e)
        
    pdf.set_xy(55, posicao_y_bloco + 5)
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(20, 50, 90)
    pdf.cell(140, 6, "Dr. Gustavo Sá", align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_x(55)
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(140, 5, "Nutrólogo - CRM SP 218406", align="C", new_x="LMARGIN", new_y="NEXT")
    
    # 4. GERA OS BYTES
    pdf_conteudo = pdf.output()
    
    if isinstance(pdf_conteudo, str):
        pdf_bytes = pdf_conteudo.encode('latin1')
    else:
        pdf_bytes = bytes(pdf_conteudo)
        
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename="receita_medica.pdf"'
    
    return response

application = app

        
# =========================
# RUN (LOCAL ONLY)
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
