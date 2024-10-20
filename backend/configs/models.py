from datetime import datetime
from .database import db

# Tabla de proyectos (importados desde Redmine)
class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relación con subtrackers
    subtrackers = db.relationship('Subtracker', backref='project', lazy=True, cascade="all, delete-orphan")
    
    # Relación con validaciones
    validations = db.relationship('Validation', backref='project_validations', lazy=True)

    # Relación con respuestas, añadiendo overlaps para evitar conflicto
    responses = db.relationship('Response', backref='project_responses', lazy=True, overlaps="project_responses")


# Tabla de dispositivos (diferentes tipos de dispositivos en el sistema)
class Device(db.Model):
    __tablename__ = 'devices'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    
    # Relación con los bloques de preguntas específicos de cada dispositivo
    question_blocks = db.relationship('QuestionBlock', secondary='device_question_block', backref=db.backref('devices', lazy='dynamic'))

    # Relación con validaciones
    validations = db.relationship('Validation', backref='device_validations', lazy=True)


# Tabla intermedia para la relación muchos a muchos entre Device y QuestionBlock
class DeviceQuestionBlock(db.Model):
    __tablename__ = 'device_question_block'
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), primary_key=True)
    question_block_id = db.Column(db.Integer, db.ForeignKey('question_blocks.id'), primary_key=True)


class Subtracker(db.Model):
    __tablename__ = 'subtrackers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)

    # Relación con respuestas
    responses = db.relationship('Response', back_populates='subtracker')

    # Relación con validaciones
    validations = db.relationship('Validation', backref='subtracker_validations', lazy=True)


class QuestionBlock(db.Model):
    __tablename__ = 'question_blocks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Relación con preguntas dentro de cada bloque
    questions = db.relationship('Question', backref='question_block', lazy=True)


class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    question_text = db.Column(db.Text, nullable=False)  # Pregunta que será validada
    expected_result = db.Column(db.Text, nullable=False)  # El resultado esperado

    question_block_id = db.Column(db.Integer, db.ForeignKey('question_blocks.id'), nullable=False)
    
    # Asociación de la pregunta con un dispositivo específico
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=True)

    # Relación con respuestas
    responses = db.relationship('Response', back_populates='question')

    # Relación con el dispositivo al que pertenece la pregunta
    device = db.relationship('Device', backref=db.backref('questions', lazy=True))


class Validation(db.Model):
    __tablename__ = 'validations'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    subtracker_id = db.Column(db.Integer, db.ForeignKey('subtrackers.id'), nullable=True)
    worker_id = db.Column(db.Integer, db.ForeignKey('workers.id'), nullable=False)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='in_progress')
    validation_result = db.Column(db.String(100), nullable=True)
    comments = db.Column(db.Text, nullable=True)
    validated_by = db.Column(db.String(100), nullable=True)


# Tabla de trabajadores (personas que realizan las validaciones)
class Worker(db.Model):
    __tablename__ = 'workers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)

    # Relación con las validaciones realizadas por este trabajador
    validations = db.relationship('Validation', backref='worker', lazy=True)

    # Relación con respuestas
    responses = db.relationship('Response', back_populates='worker')


# Tabla de respuestas (cada respuesta es una respuesta dada por un trabajador a una pregunta específica)
class Response(db.Model):
    __tablename__ = 'responses'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    subtracker_id = db.Column(db.Integer, db.ForeignKey('subtrackers.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=True)
    worker_id = db.Column(db.Integer, db.ForeignKey('workers.id'))
    response_text = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    comments = db.Column(db.Text, nullable=True)

    # Relaciones
    question = db.relationship('Question', back_populates='responses')
    subtracker = db.relationship('Subtracker', back_populates='responses')
    project = db.relationship('Project', back_populates='responses', overlaps="project_responses")
    worker = db.relationship('Worker', back_populates='responses')


# Tabla intermedia entre dispositivos y subtrackers
class DeviceSubtracker(db.Model):
    __tablename__= 'devices_subtrackers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    subtracker_id = db.Column(db.Integer, db.ForeignKey('subtrackers.id'), nullable=False)
