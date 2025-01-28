import streamlit as st
import docx
import fitz  # PyMuPDF
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

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

# Função para gerar o relatório com LangChain
def gerar_analise(redacao, nome_usuario):
    prompt = PromptTemplate(
        input_variables=["redacao", "nome_usuario"],
        template="""
        Analise a redação fornecida abaixo de acordo com os seguintes critérios: Organização e Seleção das Ideias, Argumentação Consistente e Propostas de Intervenção.
        O feedback deve ser detalhado, com pontos positivos, aspectos a melhorar e sugestões para aprimorar a redação. O formato de resposta deve ser o seguinte:

        *Relatório de Avaliação da Redação de {nome_usuario}*

        ---

        *Título da Redação:* [Título da Redação]

        ---

        *1. Organizar e selecionar as ideias*

        - *Pontos positivos:*
          - A estrutura da redação está bem definida, apresentando introdução, desenvolvimento e conclusão de maneira clara.
        - *Aspectos a melhorar:*
          - Algumas repetições no texto poderiam ser eliminadas para melhorar a objetividade.

        *Sugestão:*
        Reorganizar algumas frases para evitar redundâncias e usar conectivos que promovam uma transição mais natural entre os parágrafos.

        ---

        *2. Argumentar de forma consistente*

        - *Pontos positivos:*
          - A utilização de dados concretos fortaleceu a argumentação.
        - *Aspectos a melhorar:*
          - O texto poderia incluir mais exemplos práticos ou referências a outros autores.

        *Sugestão:*
        Adicionar citações de especialistas e exemplos concretos de iniciativas que já foram bem-sucedidas no combate ao racismo.

        ---

        *3. Elaborar propostas de intervenção*

        - *Pontos positivos:*
          - As propostas apresentadas são pertinentes e viáveis, como a implantação de aulas temáticas e palestras para conscientização racial.
        - *Aspectos a melhorar:*
          - As propostas poderiam ser mais detalhadas.

        *Sugestão:*
        Expandir o detalhamento das propostas, incluindo planos de execução, possíveis parceiros e exemplos de projetos semelhantes.

        ---

        *Resumo Geral*

        {nome_usuario} apresentou uma redação bem estruturada e com dados concretos, demonstrando compreensão do tema e preocupação em propor soluções.

        Parabéns pelo esforço, {nome_usuario}! Continue desenvolvendo suas ideias e aprimorando sua escrita.

        Redação para análise:
        {redacao}
        """
    )

    llm = OpenAI()
    chain = LLMChain(llm=llm, prompt=prompt)
    analise = chain.run(redacao=redacao, nome_usuario=nome_usuario)
    
    return analise

# Configuração do Streamlit
st.title('Analisador de Redação')

# Solicitar o nome do usuário
nome_usuario = st.text_input("Digite seu nome:")

# Opções de entrada para a redação (Upload ou Caixa de Texto)
uploaded = st.file_uploader("Carregue sua redação (PDF ou Word)", type=["pdf", "docx"])
texto_redacao = st.text_area("Ou digite sua redação aqui:")

# Botão para gerar análise
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
            result = gerar_analise(texto_redacao, nome_usuario)
            st.subheader("Relatório de Avaliação")
            st.text_area("Resultado da análise", result, height=2000)
        else:
            st.error("Por favor, insira o texto da redação.")
    else:
        st.error("Por favor, insira seu nome.")
