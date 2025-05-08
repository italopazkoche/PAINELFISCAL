def conectar_mysql():
    return mysql.connector.connect(
        host="172.16.40.90",
        user="root",
        password="6071",
        database="nfce_db",
        auth_plugin="mysql_native_password"
    )
