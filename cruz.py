import os
import re
import mysql.connector
from datetime import datetime
from tkinter import Tk, filedialog

# Configuração do banco de dados
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "6071",
    "database": "sped_efd"
}

# Selecionar a pasta onde estão os arquivos
def select_folder():
    root = Tk()
    root.withdraw()
    folder_selected = filedialog.askdirectory(title="Selecione a pasta do SPED")
    return folder_selected

SPED_FOLDER = select_folder()

# Conectar ao MySQL
def connect_db():
    return mysql.connector.connect(**DB_CONFIG)

# Criar banco de dados e tabelas
def setup_database():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS sped_efd;")
    cursor.execute("USE sped_efd;")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transmissao (
            id INT AUTO_INCREMENT PRIMARY KEY,
            cnpj VARCHAR(14) NOT NULL,
            mes_ano VARCHAR(5) NOT NULL,
            data_transmissao DATETIME NOT NULL,
            UNIQUE KEY (cnpj, mes_ano)
        )
    """)
    conn.commit()
    conn.close()

# Extrair informações do SPED
def extract_info(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()
    except UnicodeDecodeError:
        with open(file_path, "r", encoding="latin-1") as file:
            lines = file.readlines()
    
    content = "".join(lines)

    cnpj_match = re.search(r'\|0000\|.*?\|(\d{14})\|', content)
    periodo_match = re.search(r'\|0000\|\d+\|\d+\|(\d{8})\|(\d{8})\|', content)

    # Procurar Data de Transmissão nas últimas 50 linhas
    last_lines = "".join(lines[-50:])

    # Novo padrão de data YYMMDDHHMMSSZ (exemplo: 240412141336Z)
    data_transm_match = re.search(r'(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})Z', last_lines)

    cnpj = cnpj_match.group(1) if cnpj_match else None
    mes_ano = None

    if periodo_match:
        data_inicial = periodo_match.group(1)
        mes_ano = f"{data_inicial[4:6]}/{data_inicial[2:4]}"  # MM/AA

    data_transmissao = None
    if data_transm_match:
        try:
            data_transmissao = datetime.strptime(
                f"20{data_transm_match.group(1)}-{data_transm_match.group(2)}-{data_transm_match.group(3)} "
                f"{data_transm_match.group(4)}:{data_transm_match.group(5)}:{data_transm_match.group(6)}",
                "%Y-%m-%d %H:%M:%S"
            )
        except ValueError:
            data_transmissao = None

    # Log de Debug: salvar últimas 50 linhas caso não encontre a data de transmissão
    if data_transmissao is None:
        debug_log_path = os.path.join(os.path.dirname(file_path), "log_debug.txt")
        with open(debug_log_path, "w", encoding="utf-8") as log_file:
            log_file.write(f"Arquivo: {file_path}\n")
            log_file.write("Últimas 50 linhas:\n")
            log_file.write(last_lines)
        print(f"⚠️ Data de transmissão não encontrada. Verifique o log em: {debug_log_path}")

    return cnpj, mes_ano, data_transmissao

# Importar arquivos do SPED
def import_efd():
    setup_database()
    conn = connect_db()
    cursor = conn.cursor()
    
    for filename in os.listdir(SPED_FOLDER):
        if filename.endswith(".txt"):
            file_path = os.path.join(SPED_FOLDER, filename)
            cnpj, mes_ano, data_transmissao = extract_info(file_path)
            
            if cnpj and mes_ano and data_transmissao:
                cursor.execute("SELECT data_transmissao FROM transmissao WHERE cnpj = %s AND mes_ano = %s", (cnpj, mes_ano))
                existing_record = cursor.fetchone()
                
                if not existing_record or data_transmissao > existing_record[0]:
                    cursor.execute("""
                        INSERT INTO transmissao (cnpj, mes_ano, data_transmissao)
                        VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE data_transmissao = VALUES(data_transmissao)
                    """, (cnpj, mes_ano, data_transmissao))
                    print(f"✅ Arquivo {filename} importado/atualizado com sucesso. CNPJ: {cnpj}, Período: {mes_ano}, Data de Transmissão: {data_transmissao}")
                else:
                    print(f"🔄 Arquivo {filename} já importado com data mais recente.")
            else:
                print(f"⚠️ Arquivo {filename} ignorado por falta de informações. CNPJ: {cnpj}, Período: {mes_ano}, Data de Transmissão: {data_transmissao}")
    
    conn.commit()
    conn.close()

# Executar importação
import_efd()
