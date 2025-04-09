import streamlit as st
import sys
import os

# Adiciona caminho para importar das pastas
sys.path.append(os.path.join(os.path.dirname(__file__), 'paginas'))

st.set_page_config(page_title="Sistema Tributário", layout="wide")

# === MENU LATERAL ===
with st.sidebar:
    st.markdown("## 🧾 Sistema Tributário")
    st.markdown("Bem-vindo ao painel inteligente de NF-e")

    st.markdown("---")
    pagina = st.radio("📌 Selecione o módulo:", [
        "📊 Painel Geral",
        "📄 Relatório por CNPJ",
        "🗺️ Mapa de Importações",
        "📑 Relatório EFD ICMS"  # Nova opção para Relatório EFD ICMS
    ], label_visibility="collapsed")

    st.markdown("---")
    st.caption("Desenvolvido por Ítalo • CasiTech ⚙️")

# === NAVEGAÇÃO ENTRE PÁGINAS ===
if pagina == "📊 Painel Geral":
    from painel import runpainel
    runpainel()

elif pagina == "📄 Relatório por CNPJ":
    from relatorio import runrelatorio
    runrelatorio()

elif pagina == "🗺️ Mapa de Importações":
    from mapa import runmapa
    runmapa()

elif pagina == "📑 Relatório EFD ICMS":  # Nova navegação para o Relatório EFD ICMS
    from efd_icms import run_efd_icms  # Função que exibe os dados EFD ICMS
    run_efd_icms()
