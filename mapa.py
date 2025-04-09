import streamlit as st
from utils import consultar, formatar_moeda
import plotly.express as px
import requests

def runmapa():
    st.title("🗺️ Mapa de Importações por Estado")

    # Baixar GeoJSON do Brasil
    geojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    geojson_data = requests.get(geojson_url).json()

    # Consulta de clientes e valores por estado
    dados_mapa = consultar("""
        SELECT 
            uf_origem AS estado,
            razao_social_emitente,
            cnpj_emitente,
            SUM(valor_total) AS valor_total
        FROM nfce
        WHERE uf_origem IS NOT NULL AND uf_origem != ''
        GROUP BY estado, cnpj_emitente, razao_social_emitente
        ORDER BY estado, valor_total DESC;
    """)

    # Agrupar os dados para o mapa
    resumo = dados_mapa.groupby("estado").agg({
        "valor_total": "sum"
    }).reset_index()

    resumo["clientes"] = resumo["estado"].apply(lambda uf: "<br>".join(
        f"{row['razao_social_emitente']} — {formatar_moeda(row['valor_total'])}"
        for _, row in dados_mapa[dados_mapa["estado"] == uf].iterrows()
    ))

    # Mapear siglas para nomes
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

    # Criar mapa
    fig = px.choropleth(
        resumo,
        geojson=geojson_data,
        locations="estado_nome",
        featureidkey="properties.name",
        color="valor_total",
        hover_name="estado_nome",
        hover_data={
            "clientes": True,
            "valor_total": True,
            "estado_nome": False
        },
        color_continuous_scale="YlGnBu"
    )

    # Ajustar as geometrias do mapa para mostrar todas as divisões entre estados e países
    fig.update_geos(
        visible=True, 
        showcoastlines=True, 
        coastlinecolor="black",  # Exibir contornos de costa
        showsubunits=True,  # Mostrar divisões entre os estados
        subunitcolor="gray",  # Cor das divisões entre os estados
        showlakes=True,  # Exibir lagos
        lakecolor="white",  # Cor dos lagos
        showland=True,  # Exibir terra
        landcolor="white",  # Cor da terra
        projection_scale=6,  # Ajuste do zoom para o Brasil
        center=dict(lat=-14.2350, lon=-51.9253),  # Centralizar no Brasil
        fitbounds="locations"  # Ajustar o mapa para mostrar apenas as localizações dos estados
    )
    
    # Melhorias no design: ajustando o visual para um estilo mais corporativo
    fig.update_layout(
        title="Importações por Estado - Mapa",
        title_x=0.5,  # Alinhar título ao centro
        margin={"r":0,"t":30,"l":0,"b":0},
        height=750,
        geo=dict(
            projection_scale=6,  # Ajustar o zoom para o Brasil
            center=dict(lat=-14.2350, lon=-51.9253),  # Centralizar no Brasil
            subunitcolor="gray",  # Cor das divisões entre os estados
            countrycolor="black",  # Cor das divisões internacionais
        ),
        font=dict(family="Arial, sans-serif", size=14, color="black"),
        plot_bgcolor="white",  # Fundo branco para o gráfico
        paper_bgcolor="white"  # Fundo branco para o painel
    )

    # Exibir o gráfico
    st.plotly_chart(fig, use_container_width=True)
