import os

class Config:
    DATABASE_HOST = os.getenv('DB_HOST', 'host.docker.internal')  # Cambia a 'localhost' si está dentro de Docker
    DATABASE_PORT = os.getenv('DB_PORT', '5432')
    DATABASE_NAME = os.getenv('DB_NAME', 'validacion_fabricacion')
    DATABASE_USER = os.getenv('DB_USER', 'root')
    DATABASE_PASSWORD = os.getenv('DB_PASSWORD', 'root')

    # Configuración de la URI de la base de datos de SQLAlchemy
    SQLALCHEMY_DATABASE_URI = f'postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}'   

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    def __init__(self):
        print(f"Connecting to database at: {self.SQLALCHEMY_DATABASE_URI}")
