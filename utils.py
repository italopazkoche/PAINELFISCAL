import mysql.connector
import pandas as pd
import os

# Conexão com o banco de dados MySQL
def conectar_mysql():
    return mysql.connector.connect(
        host="172.16.40.90",
        user="root",
        password="6071",
        database="nfce_db"
    )

# Função para consultar dados no MySQL
def consultar(query):
    con = conectar_mysql()
    df = pd.read_sql(query, con)
    con.close()
    return df

# Função para formatação de valores monetários
def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Função para ler os arquivos EFD ICMS na pasta
def ler_efd_icms(pasta="C:\\DIARIO\\ICMS"):
    arquivos = []
    # Percorrer todos os arquivos na pasta
    for arquivo in os.listdir(pasta):
        if arquivo.endswith('.txt') or arquivo.endswith('.csv'):
            caminho_arquivo = os.path.join(pasta, arquivo)
            try:
                # Lendo o arquivo e concatenando os dados
                dados = pd.read_csv(caminho_arquivo, sep=';', encoding='latin1', header=None)
                dados['nome_arquivo'] = arquivo  # Adiciona o nome do arquivo
                arquivos.append(dados)
            except Exception as e:
                print(f"Erro ao ler o arquivo {arquivo}: {e}")
    return pd.concat(arquivos, ignore_index=True) if arquivos else pd.DataFrame()

# Função para filtrar e processar os dados com base no bloco
def filtrar_blocos(dados):
    # Filtrar os blocos de interesse
    dados_filtrados = dados[dados[0].str.startswith('|C100|') | dados[0].str.startswith('|C170|')]

    # Dividir as colunas usando o delimitador '|'
    dados_divididos = dados_filtrados[0].str.split('|', expand=True)

    # Renomear as colunas
    dados_divididos.columns = ["Bloco", "CST", "CFOP", "Valor ICMS", "Valor PIS", "Valor COFINS", "NCM", "Aliquota ICMS"]

    # Converter as colunas de valores monetários para tipo numérico
    dados_divididos["Valor ICMS"] = pd.to_numeric(dados_divididos["Valor ICMS"], errors='coerce')
    dados_divididos["Valor PIS"] = pd.to_numeric(dados_divididos["Valor PIS"], errors='coerce')
    dados_divididos["Valor COFINS"] = pd.to_numeric(dados_divididos["Valor COFINS"], errors='coerce')
    dados_divididos["Aliquota ICMS"] = pd.to_numeric(dados_divididos["Aliquota ICMS"], errors='coerce')

    return dados_divididos
