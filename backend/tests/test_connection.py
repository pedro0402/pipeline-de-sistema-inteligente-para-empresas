from core.database import engine

try:
    connection = engine.connect()
    print('conectado ao banco')
    connection.close()
except Exception as e:
    print("erro ao conectar: ", e)