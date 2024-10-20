from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base
from .config import Config
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
# Crear el motor (engine) de la base de datos
DATABASE_URL = Config.SQLALCHEMY_DATABASE_URI
engine = create_engine(DATABASE_URL)


# Crear una sesion con scoped_session para manejar  multiples hilos
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# Crear el modelo base para las clases declarativas
Base = declarative_base()
Base.query = db_session.query_property()

# Función para inicializar la base de datos
def init_db():
    from models import Scenario, Device, Question, Project, Validation, Worker
    # Crea las tablas si no existen
    Base.metadata.create_all(bind=engine) 