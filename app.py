# Mini Sistema de Monitoramento de Fundos (CVM) - APP READY
# Versão evoluída para acesso via APP (web + mobile)

# Requisitos:
# pip install streamlit requests beautifulsoup4 pandas openpyxl

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
import streamlit as st

URL = "https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/CPublica/ResultBuscaPartic.aspx"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/x-www-form-urlencoded"
}


def limpar_cnpj(cnpj):
    return cnpj.replace(".", "").replace("/", "").replace("-", "")


@st.cache_data(ttl=3600)
def consultar_fundo(cnpj):
    cnpj = limpar_cnpj(cnpj)

    payload = {
        "TpConsulta": "1",
        "CNPJ": cnpj,
        "COMPTC_INI": "",
        "COMPTC_FIM": ""
    }

    session = requests.Session()
    response = session.post(URL, data=payload, headers=HEADERS)

    soup = BeautifulSoup(response.text, "html.parser")
    tabelas = soup.find_all("table")

    if not tabelas:
        return None

    tabela = tabelas[-1]
    linhas = tabela.find_all("tr")

    dados = []

    for linha in linhas[1:]:
        colunas = linha.find_all("td")
        if len(colunas) >= 2:
            try:
                data = datetime.strptime(colunas[0].text.strip(), "%d/%m/%Y")
                cota = float(colunas[1].text.strip().replace(",", "."))
                dados.append((data, cota))
            except:
                continue

    if len(dados) < 2:
        return None

    dados.sort(reverse=True)

    data_atual, cota_atual = dados[0]
    data_ant, cota_ant = dados[1]

    variacao = ((cota_atual / cota_ant) - 1) * 100

    return {
        "data": data_atual,
        "cota": cota_atual,
        "variacao": variacao
    }


# ---------------- UI APP ----------------

st.set_page_config(
    page_title="Monitor de Fundos CVM",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 Monitor de Fundos CVM (App)")

# Sidebar (experiência tipo app)
st.sidebar.header("⚙️ Configurações")
cnpjs_input = st.sidebar.text_area(
    "CNPJs (um por linha)",
    "33.588.607/0001-93"
)

executar = st.sidebar.button("▶️ Consultar")

if executar:

    lista_cnpjs = [c.strip() for c in cnpjs_input.split("\n") if c.strip()]

    resultados = []

    with st.spinner("Consultando CVM..."):
        for cnpj in lista_cnpjs:
            res = consultar_fundo(cnpj)
            if res:
                resultados.append({
                    "CNPJ": cnpj,
                    "Data": res["data"],
                    "Cota": res["cota"],
                    "Variação (%)": res["variacao"]
                })

    if resultados:
        df = pd.DataFrame(resultados)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📋 Dados")
            st.dataframe(df, use_container_width=True)

        with col2:
            st.subheader("📈 Variação")
            st.bar_chart(df.set_index("CNPJ")["Variação (%)"])

        # Exportação
        file = "relatorio_fundos.xlsx"
        df.to_excel(file, index=False)

        st.download_button(
            "📥 Baixar Excel",
            open(file, "rb"),
            file_name=file
        )

    else:
        st.warning("Nenhum dado encontrado.")


# ---------------- COMO TRANSFORMAR EM APP ----------------

# OPÇÃO 1 (RECOMENDADO - MAIS RÁPIDO)
# Deploy no Streamlit Cloud:
# 1. Suba esse código no GitHub
# 2. Acesse: https://streamlit.io/cloud
# 3. Conecte o repositório
# 4. Deploy
# → Resultado: URL pública acessível no celular

# OPÇÃO 2 (APP MOBILE REAL)
# Use wrapper como:
# - Streamlit + PWA (Progressive Web App)
# - Ou converter com ferramentas como:
#   - PyInstaller + Electron
#   - Flutter (consumindo API Python)

# OPÇÃO 3 (ARQUITETURA PROFISSIONAL)
# Separar backend e frontend:
# - Backend: FastAPI (consulta CVM)
# - Frontend: React / Flutter
# - Hospedagem: AWS / Azure

# ---------------- RESULTADO FINAL ----------------
# Você terá um "app" acessível via:
# - Desktop
# - Celular
# - Tablet
# sem necessidade de instalar nada
