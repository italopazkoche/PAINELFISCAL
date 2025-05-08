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
        "📈 Resumo de XMLs por Mês",
        "🛍️ Resumo Venda por Item",
        "📄 Relatório por CNPJ",
        "🗺️ Mapa de Importações",
        "📑 Relatório EFD ICMS",
        "⚡ Energia Elétrica",
        "💼 Serviços Tomados",
        "🏭 CIAP",
        "🎯 Créditos Especiais PIS e COFINS",
        "📦 Bloco H",
        "🧾 Apuração do ICMS",
        "💰 Apuração do PIS e COFINS"
    ], label_visibility="collapsed")

    st.markdown("---")
    st.caption("Desenvolvido por Ítalo • CasiTech ⚙️")

# === NAVEGAÇÃO ENTRE PÁGINAS ===
if pagina == "📊 Painel Geral":
    from painel import runpainel
    runpainel()

elif pagina == "📈 Resumo de XMLs por Mês":
    from resumo_por_item import run_resumo_por_item
    run_resumo_por_item()

elif pagina == "🛍️ Resumo Venda por Item":
    from xml_saida_mes import run_xml_saida_mes
    run_xml_saida_mes()

elif pagina == "📄 Relatório por CNPJ":
    from relatorio import runrelatorio
    runrelatorio()

elif pagina == "🗺️ Mapa de Importações":
    from mapa import runmapa
    runmapa()

elif pagina == "📑 Relatório EFD ICMS":
    from efd_icms import run_efd_icms
    run_efd_icms()

# === Módulos ainda em desenvolvimento ===
elif pagina == "⚡ Energia Elétrica":
    st.title("⚡ Em breve: Análise de Energia Elétrica")

elif pagina == "💼 Serviços Tomados":
    st.title("💼 Em breve: Análise de Serviços Tomados")

elif pagina == "🏭 CIAP":
    st.title("🏭 Em breve: Controle de Crédito CIAP")

elif pagina == "🎯 Créditos Especiais PIS e COFINS":
    st.title("🎯 Em breve: Créditos Especiais de PIS e COFINS")

elif pagina == "📦 Bloco H":
    st.title("📦 Em breve: Análise do Bloco H - Inventário")

elif pagina == "🧾 Apuração do ICMS":
    st.title("🧾 Em breve: Apuração do ICMS")

elif pagina == "💰 Apuração do PIS e COFINS":
    st.title("💰 Em breve: Apuração do PIS e COFINS")
