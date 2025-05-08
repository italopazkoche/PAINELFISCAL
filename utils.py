from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
import os
import json

# Lê as credenciais do segredo no ambiente
def conectar_bigquery():
    info = json.loads(os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
    credentials = service_account.Credentials.from_service_account_info(info)
    return bigquery.Client(credentials=credentials, project=info["project_id"])

# Executa query SQL no BigQuery e retorna um DataFrame
def consultar(query):
    client = conectar_bigquery()
    df = client.query(query).to_dataframe()
    return df

# Formata valores monetários em estilo brasileiro
def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Lê arquivos .txt ou .csv da pasta ICMS
def ler_efd_icms(pasta="C:\\DIARIO\\ICMS"):
    arquivos = []
    for arquivo in os.listdir(pasta):
        if arquivo.endswith('.txt') or arquivo.endswith('.csv'):
            caminho_arquivo = os.path.join(pasta, arquivo)
            try:
                dados = pd.read_csv(caminho_arquivo, sep=';', encoding='latin1', header=None)
                dados['nome_arquivo'] = arquivo
                arquivos.append(dados)
            except Exception as e:
                print(f"Erro ao ler o arquivo {arquivo}: {e}")
    return pd.concat(arquivos, ignore_index=True) if arquivos else pd.DataFrame()

# Filtra os blocos C100 e C170 e trata os dados
def filtrar_blocos(dados):
    dados_filtrados = dados[dados[0].str.startswith('|C100|') | dados[0].str.startswith('|C170|')]
    dados_divididos = dados_filtrados[0].str.split('|', expand=True)

    colunas_esperadas = max(12, dados_divididos.shape[1])
    dados_divididos = dados_divididos.reindex(columns=range(colunas_esperadas), fill_value='')

    dados_divididos.columns = [f"col_{i}" for i in range(colunas_esperadas)]

    dados_extraidos = pd.DataFrame()
    dados_extraidos["tipo_bloco"] = dados_divididos["col_1"]
    dados_extraidos["cfop"] = dados_divididos["col_11"]
    dados_extraidos["valor_icms"] = pd.to_numeric(dados_divididos["col_8"], errors='coerce')
    dados_extraidos["valor_pis"] = pd.to_numeric(dados_divididos["col_10"], errors='coerce')
    dados_extraidos["valor_cofins"] = pd.to_numeric(dados_divididos["col_12"], errors='coerce')
    dados_extraidos["ncm"] = dados_divididos["col_7"]
    dados_extraidos["aliquota_icms"] = pd.to_numeric(dados_divididos["col_9"], errors='coerce')

    return dados_extraidos
