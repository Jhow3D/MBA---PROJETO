import os
import streamlit as st
import docx
import fitz  # PyMuPDF
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
import smtplib
import ssl
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

openai_api_key = st.secrets["OPENAI_API_KEY"]
groq_api_key = st.secrets["GROQ_API_KEY"]
huggingface_token = st.secrets["HUGGINGFACEHUB_API_TOKEN"]
email_sender = st.secrets["EMAIL_SENDER"]
email_password = st.secrets["EMAIL_PASSWORD"]

TEMPLATE_PROMPT = """Você será responsável por avaliar essa redação: {redacao} do aluno {nome_usuario} com base nos critérios do Exame Nacional do Ensino Médio (ENEM). A redação será avaliada em cinco competências, cada uma com pontuação de 0 a 200 pontos, totalizando uma nota final de 0 a 1000. Siga as orientações abaixo para atribuir a nota em cada competência:

Competência I: Domínio da Modalidade Escrita Formal da Língua Portuguesa
Avalie o domínio da norma padrão da língua portuguesa, incluindo gramática, ortografia, pontuação e concordância.

Atribua uma nota de acordo com os seguintes critérios:

0 ponto: Desconhecimento da modalidade escrita formal.

40 pontos: Domínio precário, com desvios frequentes e diversificados.

80 pontos: Domínio insuficiente, com muitos desvios.

120 pontos: Domínio mediano, com alguns desvios.

160 pontos: Bom domínio, com poucos desvios.

200 pontos: Excelente domínio, com desvios apenas excepcionais.

Competência II: Compreensão da Proposta de Redação e Desenvolvimento do Tema
Verifique se o texto desenvolve o tema proposto de forma clara e coerente, dentro da estrutura dissertativo-argumentativa.

Atribua uma nota de acordo com os seguintes critérios:

0 ponto: Fuga ao tema ou não atendimento à estrutura dissertativo-argumentativa.

40 pontos: Tangencia o tema ou apresenta domínio precário da estrutura.

80 pontos: Desenvolve o tema com cópia de trechos dos textos motivadores ou domínio insuficiente da estrutura.

120 pontos: Desenvolve o tema com argumentação previsível e domínio mediano da estrutura.

160 pontos: Desenvolve o tema com argumentação consistente e bom domínio da estrutura.

200 pontos: Desenvolve o tema com argumentação consistente e excelente domínio da estrutura.

Competência III: Seleção, Relação e Organização de Informações e Argumentos
Avalie a organização das ideias e a consistência da argumentação em defesa de um ponto de vista.

Atribua uma nota de acordo com os seguintes critérios:

0 ponto: Informações, fatos e opiniões não relacionados ao tema.

40 pontos: Informações, fatos e opiniões pouco relacionados ou incoerentes.

80 pontos: Informações, fatos e opiniões relacionados, mas desorganizados ou contraditórios.

120 pontos: Informações, fatos e opiniões relacionados, mas pouco organizados.

160 pontos: Informações, fatos e opiniões relacionados e organizados, com indícios de autoria.

200 pontos: Informações, fatos e opiniões relacionados, consistentes e organizados, configurando autoria.

Competência IV: Conhecimento dos Mecanismos Linguísticos para a Construção da Argumentação
Avalie o uso de conectivos e recursos coesivos para garantir a fluidez e a lógica do texto.

Atribua uma nota de acordo com os seguintes critérios:

0 ponto: Não articula as informações.

40 pontos: Articulação precária das partes do texto.

80 pontos: Articulação insuficiente, com muitas inadequações.

120 pontos: Articulação mediana, com algumas inadequações.

160 pontos: Articulação com poucas inadequações e repertório diversificado de recursos coesivos.

200 pontos: Articulação excelente e repertório diversificado de recursos coesivos.

Competência V: Proposta de Intervenção
Verifique se o texto apresenta uma proposta de intervenção clara, detalhada e respeitosa aos direitos humanos.

Atribua uma nota de acordo com os seguintes critérios:

0 ponto: Não apresenta proposta ou proposta não relacionada ao tema.

40 pontos: Proposta vaga, precária ou relacionada apenas ao assunto.

80 pontos: Proposta insuficiente, relacionada ao tema, mas não articulada com a discussão.

120 pontos: Proposta mediana, relacionada ao tema e articulada à discussão.

160 pontos: Proposta bem elaborada, relacionada ao tema e articulada à discussão.

200 pontos: Proposta muito bem elaborada, detalhada, relacionada ao tema e articulada à discussão.

Formato de Resposta Esperado:
A IA deve fornecer:

Uma nota de 0 a 200 para cada competência.

A nota total da redação (soma das cinco competências, máximo de 1000 pontos) em formato de tabela."""

def extrair_texto(uploaded_file):
    """Extrai texto de um PDF ou arquivo Word."""
    if uploaded_file.type == "application/pdf":
        pdf_document = fitz.open(uploaded_file)
        return "\n".join(page.get_text() for page in pdf_document)
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = docx.Document(uploaded_file)
        return "\n".join(para.text for para in doc.paragraphs)
    return ""

def gerar_analise(redacao, nome_usuario, modelo):
    """Executa a análise da redação usando o modelo escolhido."""
    llm = {
        "GPT 3.5 Turbo": ChatOpenAI(),
        "GPT 4o 2024": ChatOpenAI(model='gpt-4o-2024-08-06'),
        "LLAMA 3.3 70B": ChatGroq(temperature=0, model_name='llama-3.3-70b-versatile')
    }.get(modelo)

    if not llm:
        return "Erro: Modelo não encontrado!"

    prompt = PromptTemplate(input_variables=["redacao", "nome_usuario"], template=TEMPLATE_PROMPT)
    chain = LLMChain(llm=llm, prompt=prompt)
    return chain.run(redacao=redacao, nome_usuario=nome_usuario)

def envio_email(nome_usuario, email_usuario, result):
    """Envia o resultado por e-mail."""
    if not email_usuario:
        st.error("⚠️ Por favor, insira um e-mail válido.")
        return

    msg = EmailMessage()
    msg["Subject"] = f"Relatório de Avaliação - {nome_usuario}"
    msg["From"] = os.getenv("EMAIL_SENDER")
    msg["To"] = email_usuario
    msg.set_content(result)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(os.getenv("EMAIL_SENDER"), os.getenv("EMAIL_PASSWORD"))
            server.send_message(msg)
        st.success("✅ E-mail enviado com sucesso!")
    except Exception as e:
        st.error(f"❌ Erro ao enviar e-mail: {e}")

# Interface Streamlit
st.set_page_config(
    page_title="CORRIGE.AI",
    page_icon="📃",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
    }
)


st.title("📑 Avaliador de Redação do ENEM")
with st.sidebar:
    #st.image(r'imagens/logov2.png')
    modelo_llm = st.sidebar.radio("Escolha o LLM:", ["GPT 3.5 Turbo", "GPT 4o 2024", "LLAMA 3.3 70B"])
nome_usuario = st.text_input("Nome:")
email_usuario = st.text_input("E-mail:")
uploaded = st.file_uploader("Carregue sua redação (PDF ou Word)", type=["pdf", "docx"])
texto_redacao = st.text_area("Ou digite sua redação:")

if st.button("📊 Gerar Análise"):
    if not nome_usuario:
        st.error("⚠️ Insira seu nome.")
    elif not texto_redacao and not uploaded:
        st.error("⚠️ Insira o texto da redação ou faça o upload.")
    else:
        if uploaded:
            texto_redacao = extrair_texto(uploaded)
        resultado = gerar_analise(texto_redacao, nome_usuario, modelo_llm)
        st.subheader("📌 Relatório de Avaliação")
        st.markdown(resultado, unsafe_allow_html=True)
        envio_email(nome_usuario, email_usuario, resultado)


      




