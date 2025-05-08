import mysql.connector

def conectar_mysql():
    return mysql.connector.connect(
        host="172.16.40.90",
        user="root",
        password="6071",
        database="nfce_db",
        auth_plugin="mysql_native_password"
    )

def chave_periodo_ja_importada(chave_periodo, nome_tabela='efd_icms_bloco_0000'):
    conn = conectar_mysql()
    cursor = conn.cursor()
    query = f"SELECT COUNT(*) FROM {nome_tabela} WHERE chave_periodo = %s"
    cursor.execute(query, (chave_periodo,))
    resultado = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return resultado > 0
