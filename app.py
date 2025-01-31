import streamlit as st
import docx
import fitz  # PyMuPDF #fpdf
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_openai import OpenAI,ChatOpenAI
from langchain_groq import ChatGroq
from langchain_community.llms import huggingface_hub
import smtplib
import ssl
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

template_prompt = """
Você será responsável por avaliar essa redação: {redacao} do aluno {nome_usuario} com base nos critérios do Exame Nacional do Ensino Médio (ENEM). A redação será avaliada em cinco competências, cada uma com pontuação de 0 a 200 pontos, totalizando uma nota final de 0 a 1000. Siga as orientações abaixo para atribuir a nota em cada competência:

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

A nota total da redação (soma das cinco competências, máximo de 1000 pontos) em formato de tabela.

"""

def envio_email(nome_usuario,email_usuario,result):
    # Criando a mensagem do e-mail
    msg = EmailMessage()
    msg["Subject"] = f"Relatório de Avaliação de: {nome_usuario}"
    msg["From"] = 'corrigeai.red@gmail.com'
    msg["To"] = email_usuario
    msg.set_content(f"{result}")

    # Conectar-se ao servidor SMTP e enviar o e-mail
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login('corrigeai.red@gmail.com', 'frtovnzkuidduhcf')
            server.send_message(msg)
        st.write("✅ E-mail enviado com sucesso!")
    except Exception as e:
        st.write(f"❌ Erro ao enviar e-mail: {e}")




# Função para extrair texto de arquivos PDF
def extrair_texto_pdf(uploaded_file):
    pdf_document = fitz.open(uploaded_file)
    text = ""
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        text += page.get_text()
    return text

# Função para extrair texto de arquivos Word (docx)
def extrair_doc_txt(uploaded_file):
    doc = docx.Document(uploaded_file)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

# def gerar_analise_DeepSeek(redacao, nome_usuario):
#     model_name = 'deepseek-ai/DeepSeek-V3'
#     prompt = PromptTemplate(
#         input_variables=["redacao", "nome_usuario"],
#         template="""
#         Gere uma análise da redação fornecida nessa variável {redacao} e essa avaliação precisa citar o nome do usuário que é {nome_usuario},
#         também gere uma tabela com pontuações a seu critério avaliando o texto, e também conte as palavras da rendação, verifique também se tem erros de ortografia e pontuação e modismo (girias).  
#         """
#     )
#     llm = huggingface_hub(repo_id="deepseek-ai/DeepSeek-V3",task="text-generation",model_kwargs={
#         "max_new_tokens": 512,
#         "top_k": 30,
#         "temperature": 0.1,
#         "repetition_penalty": 1.03,
#     },
#     )
#     chain = LLMChain(llm=llm, prompt=prompt)
#     analise = chain.run(redacao=redacao, nome_usuario=nome_usuario)
    
#     return analise


# Função para gerar o relatório com LangChain
def gerar_analise_gpt_3_5(redacao, nome_usuario):
    global template_prompt
    prompt = PromptTemplate(
        input_variables=["redacao", "nome_usuario"],
        template= template_prompt
    )
    llm = ChatOpenAI()
    chain = LLMChain(llm=llm, prompt=prompt)
    analise = chain.run(redacao=redacao, nome_usuario=nome_usuario)
    
    return analise

def gerar_analise_gpt_4(redacao, nome_usuario):
    global template_prompt
    prompt = PromptTemplate(
        input_variables=["redacao", "nome_usuario"],
        template = template_prompt
    )
    llm = ChatOpenAI(model='gpt-4o-2024-08-06')
    chain = LLMChain(llm=llm, prompt=prompt)
    analise = chain.run(redacao=redacao, nome_usuario=nome_usuario)
    
    return analise

def gerar_analise_llama3(redacao, nome_usuario):
    global template_prompt
    prompt = PromptTemplate(
        input_variables=["redacao", "nome_usuario"],
        template= template_prompt
    )
    llm_groq = ChatGroq(temperature=0, model_name='llama-3.3-70b-versatile')
    chain_groq = LLMChain(llm=llm_groq, prompt=prompt)
    analise = chain_groq.run(redacao=redacao, nome_usuario=nome_usuario)
    
    return analise



# Configuração do Streamlit
st.title('Avaliador de Redação do ENEM')

# Escolhendo o modelo de LLM
with st.sidebar:

    opcao_llm = st.radio(
        "Escolha o LLM que irá análisar o texto",
        ["GPT 3.5 Turbo","GPT 4o 2024",'LLAMA 3.3 70B']
    )

# Solicitar o nome do usuário
nome_usuario = st.text_input("Digite seu nome:")
email_usuario = st.text_input("Digite aqui o seu e-mail:")

# Opções de entrada para a redação (Upload ou Caixa de Texto)
uploaded = st.file_uploader("Carregue sua redação (PDF ou Word)", type=["pdf", "docx"])
texto_redacao = st.text_area("Ou digite sua redação aqui:")



# Botão para gerar análise
if opcao_llm == 'GPT 3.5 Turbo':

    if st.button("Gerar Análise"):
        if nome_usuario:
            
            if uploaded:
                # Extração de texto com base no tipo de arquivo
                if uploaded.type == "application/pdf":
                    texto_redacao = extrair_texto_pdf(uploaded)
                elif uploaded.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    texto_redacao = extrair_doc_txt(uploaded)
            
            if texto_redacao:
                # Gerar a análise com LangChain
                result = gerar_analise_gpt_3_5(texto_redacao, nome_usuario)
                st.subheader("Relatório de Avaliação")
                #st.text_area("Resultado da análise", result, height=2000)
                with st.expander('',expanded=True):
                    st.markdown(result)
            else:
                st.error("Por favor, insira o texto da redação.")
        else:
            st.error("Por favor, insira seu nome.")

if opcao_llm == 'GPT 4o 2024':

    if st.button("Gerar Análise"):
        if nome_usuario:
            
            if uploaded:
                # Extração de texto com base no tipo de arquivo
                if uploaded.type == "application/pdf":
                    texto_redacao = extrair_texto_pdf(uploaded)
                elif uploaded.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    texto_redacao = extrair_doc_txt(uploaded)
            
            if texto_redacao:
                # Gerar a análise com LangChain
                result = gerar_analise_gpt_4(texto_redacao, nome_usuario)
                st.subheader("Relatório de Avaliação")
                #st.text_area("Resultado da análise", result, height=2000)
                with st.expander('',expanded=True):
                    st.markdown(result)
            else:
                st.error("Por favor, insira o texto da redação.")
        else:
            st.error("Por favor, insira seu nome.")

if opcao_llm == 'LLAMA 3.3 70B':

    if st.button("Gerar Análise"):
        if nome_usuario:
            
            if uploaded:
                # Extração de texto com base no tipo de arquivo
                if uploaded.type == "application/pdf":
                    texto_redacao = extrair_texto_pdf(uploaded)
                elif uploaded.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    texto_redacao = extrair_doc_txt(uploaded)
            
            if texto_redacao:
                # Gerar a análise com LangChain
                result = gerar_analise_llama3(texto_redacao, nome_usuario)
                st.subheader("Relatório de Avaliação")
                #st.text_area("Resultado da análise", result, height=2000)
                with st.expander('',expanded=True):
                    st.markdown(result)
                
            else:
                st.error("Por favor, insira o texto da redação.")
        else:
            st.error("Por favor, insira seu nome.")

if st.button('Enviar para o e-mail'):
    envio_email(nome_usuario,email_usuario,result)

    

# if opcao_llm == 'DeepSeek-V3':

#     if st.button("Gerar Análise"):
#         if nome_usuario:
            
#             if uploaded:
#                 # Extração de texto com base no tipo de arquivo
#                 if uploaded.type == "application/pdf":
#                     texto_redacao = extrair_texto_pdf(uploaded)
#                 elif uploaded.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
#                     texto_redacao = extrair_doc_txt(uploaded)
            
#             if texto_redacao:
#                 # Gerar a análise com LangChain
#                 result = gerar_analise_DeepSeek(texto_redacao, nome_usuario)
#                 st.subheader("Relatório de Avaliação")
#                 #st.text_area("Resultado da análise", result, height=2000)
#                 with st.expander('',expanded=True):
#                     st.markdown(result)
#             else:
#                 st.error("Por favor, insira o texto da redação.")
#         else:
#             st.error("Por favor, insira seu nome.")

            