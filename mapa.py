import streamlit as st
from utils import consultar, formatar_moeda
import plotly.express as px
import requests

def runmapa():
    st.title("🗺️ Mapa de Importações por Estado")

    # === FILTRO POR MÊS ===
    meses_df = consultar("""
        SELECT DISTINCT DATE_FORMAT(data_emissao, '%Y-%m') AS mes
        FROM nfce
        ORDER BY mes DESC;
    """)
    meses_disponiveis = meses_df["mes"].tolist()

    if not meses_disponiveis:
        st.warning("Nenhum mês disponível nos dados.")
        st.stop()

    mes_selecionado = st.selectbox("📅 Selecione o mês de referência:", ["Todos"] + meses_disponiveis)

    filtro_mes = ""
    if mes_selecionado != "Todos":
        filtro_mes = f"AND DATE_FORMAT(data_emissao, '%Y-%m') = '{mes_selecionado}'"

    # === BAIXAR GEOJSON DO BRASIL ===
    geojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    geojson_data = requests.get(geojson_url).json()

    # === CONSULTAR DADOS ===
    dados_mapa = consultar(f"""
        SELECT 
            uf_origem AS estado,
            razao_social_emitente,
            cnpj_emitente,
            SUM(valor_total) AS valor_total
        FROM nfce
        WHERE uf_origem IS NOT NULL AND uf_origem != ''
        {filtro_mes}
        GROUP BY estado, cnpj_emitente, razao_social_emitente
        ORDER BY estado, valor_total DESC;
    """)

    if dados_mapa.empty:
        st.warning("Nenhum dado encontrado para o mês selecionado.")
        return

    # === AGRUPAR DADOS POR ESTADO ===
    resumo = dados_mapa.groupby("estado").agg({
        "valor_total": "sum"
    }).reset_index()

    resumo["clientes"] = resumo["estado"].apply(lambda uf: "<br>".join(
        f"{row['razao_social_emitente']} — {formatar_moeda(row['valor_total'])}"
        for _, row in dados_mapa[dados_mapa["estado"] == uf].iterrows()
    ))

    # === MAPEAR SIGLAS PARA NOMES COMPLETOS DOS ESTADOS ===
    sigla_to_nome = {
        "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas", "BA": "Bahia",
        "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás",
        "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais",
        "PA": "Pará", "PB": "Paraíba", "PR": "Paraná", "PE": "Pernambuco", "PI": "Piauí",
        "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul",
        "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina", "SP": "São Paulo",
        "SE": "Sergipe", "TO": "Tocantins"
    }
    resumo["estado_nome"] = resumo["estado"].map(sigla_to_nome)

    # === CRIAR MAPA COROPLÉTICO ===
    fig = px.choropleth(
        resumo,
        geojson=geojson_data,
        locations="estado_nome",
        featureidkey="properties.name",
        color="valor_total",
        hover_name="estado_nome",
        hover_data={"clientes": True, "valor_total": True, "estado_nome": False},
        color_continuous_scale="YlGnBu"
    )

    # === MELHORAR VISUAL DO MAPA ===
    fig.update_geos(
        visible=False,
        fitbounds="locations",
        showlakes=True,
        lakecolor="white",
        landcolor="white",
        showcountries=True,
        showsubunits=True,
        subunitcolor="gray",
        countrycolor="black"
    )

    fig.update_layout(
        title="Importações por Estado",
        title_x=0.5,
        margin={"r":0,"t":30,"l":0,"b":0},
        height=750,
        font=dict(family="Arial, sans-serif", size=14, color="black"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        geo=dict(
            showframe=False,
            showcoastlines=False,
            projection_type="mercator",
            center=dict(lat=-14.2350, lon=-51.9253),
            projection_scale=6
        )
    )

    # === EXIBIR O GRÁFICO ===
    st.plotly_chart(fig, use_container_width=True)
