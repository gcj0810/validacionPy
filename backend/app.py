from datetime import datetime
from flask import Flask, jsonify, request
from configs.database import db
from configs.config import Config
from services.getTracketsProject import getDataProject
from sqlalchemy.sql import text
from configs.models import Project, Device, Question, QuestionBlock, Validation, Worker, Subtracker ,DeviceSubtracker
from flask_cors import CORS
from sqlalchemy.exc import IntegrityError


# Setup de Flask y PostgreSQL
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
CORS(app, origins="http://localhost:3000")
db.init_app(app)

# Migrations con Flask-Migrate

# Cerrar la sesión de la base de datos después de cada solicitud
@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()


################### RUTAS DE LA API ######################

###### RUTA DE PRUEBA ######
@app.route("/ping")
def testping():
    return "pong"


# Ruta para mostrar preguntas, con filtrado por dispositivo
@app.route('/questions', methods=['GET'])
def show_questions():
    try:
        device_id = request.args.get('device_id')

        # Filtrar por device_id si está presente
        if device_id:
            questions = Question.query.filter_by(device_id=device_id).all()
        else:
            questions = Question.query.all()

        if not questions:
            return jsonify({'message': 'No se encontraron preguntas'}), 404

        # Crear la lista de preguntas
        questions_list = [
            {
                'id': question.id,
                'action': question.action,
                'verify': question.verify,
                'expected_result': question.expected_result,
                'device_id': question.device_id,
                'block_id': question.block_id
            }
            for question in questions
        ]

        return jsonify(questions_list)

    except Exception as e:
        return jsonify({'error': f'No se pudieron obtener las preguntas: {str(e)}'}), 500


# Ruta para manejar datos del proyecto y trackers desde Redmine
@app.route('/data', methods=['POST'])
def handle_data():
    data = request.get_json()
    url = data.get('url')
    user = data.get('user')
    password = data.get('pass')

    # Validar que los datos obligatorios del formulario estén presentes
    if not url or not user or not password:
        return jsonify({'success': False, 'message': 'Faltan datos en el formulario'}), 400

    try:
        # Obtener datos del proyecto desde la API
        project_data = getDataProject(url, user, password)

        # Extraer los datos del proyecto y del trabajador
        project_name = project_data[0].get('project_name')
        worker_name = project_data[0].get('worker_name')
        trackers = project_data[0].get('trackers', [])

        if not project_name or not worker_name:
            raise ValueError("Faltan datos obligatorios: project_name o worker_name")

        # Insertar o recuperar el proyecto
        project_id = insert_project(project_name)
        worker_id = insert_worker(worker_name)
        tracker_results = []

        # Insertar los subjects de cada tracker y asociarlos a devices
        for tracker in trackers:
            tracker_name = tracker.get('tracker_name')
            subjects = tracker.get('subjects', [])

            device = Device.query.filter_by(name=tracker_name).first()

            if not device:
                continue

            device_id = device.id
            tracker_info = {'tracker_name': tracker_name, 'subjects': []}

            for subject in subjects:
                # Insertar el subtracker
                subtracker_id = insert_subtracker(project_id, subject)
                insert_device_subtracker(device_id, subtracker_id)

                # Obtener las preguntas asociadas al subtracker
                questions = get_questions_for_subtracker_and_device(subtracker_id, device_id)

                # Añadir las preguntas al subject
                tracker_info['subjects'].append({
                    'subject': subject,
                    'questions': questions
                })

            # Añadir el tracker_info al resultado final
            tracker_results.append(tracker_info)

        # Devolver el JSON con los trackers, subjects y preguntas
        return jsonify({
            'success': True,
            'project_name': project_name,
            'trackers': tracker_results,
            'worker_name': worker_name
        })

    except IntegrityError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error de integridad: {str(e.orig)}'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al procesar los datos: {str(e)}'
        })


def get_questions_for_subtracker_and_device(subtracker_id, device_id):
    # Buscar el subtracker
    subtracker = db.session.get(Subtracker, subtracker_id)
    if not subtracker:
        return []

    # Obtener el dispositivo
    device = db.session.get(Device, device_id)
    if not device:
        return []

    questions = []

    # Obtener los bloques de preguntas asociados al dispositivo
    for question_block in device.question_blocks:
        # Obtener las preguntas dentro del bloque
        for question in question_block.questions:
            questions.append({
                'question_text': question.question_text,
                'expected_result': question.expected_result
            })
    print(questions)
    # Retornar la lista de preguntas
    return questions


def insert_worker(worker_name):
    worker = Worker.query.filter_by(name=worker_name).first()
    if worker:
        return worker.id
    new_worker = Worker(name=worker_name)
    db.session.add(new_worker)
    db.session.commit()
    return new_worker.id


def insert_device_subtracker(device_id, subtracker_id):
    existing_relation = DeviceSubtracker.query.filter_by(device_id=device_id, subtracker_id=subtracker_id).first()
    if not existing_relation:
        new_relation = DeviceSubtracker(device_id=device_id, subtracker_id=subtracker_id)
        db.session.add(new_relation)
        db.session.commit()


def insert_project(project_name):
    project = Project.query.filter_by(name=project_name).first()

    if project:
        return project.id
    new_project = Project(name=project_name)
    db.session.add(new_project)
    db.session.commit()
    return new_project.id


def insert_subtracker(project_id, subject_name):
    subtracker = Subtracker.query.filter_by(name=subject_name, project_id=project_id).first()

    if subtracker:
        return subtracker.id
    new_subtracker = Subtracker(name=subject_name, project_id=project_id)
    db.session.add(new_subtracker)
    db.session.commit()
    return new_subtracker.id


def check_db_connection():
    try:
        result = db.session.execute(text('SELECT 1'))
        return result.scalar() == 1
    except Exception as e:
        return False


@app.route('/api/check-db', methods=['GET'])
def check_db():
    if check_db_connection():
        return jsonify({'success': True, 'message': 'Conexión a la base de datos exitosa'})
    else:
        return jsonify({'success': False, 'message': 'Error de conexión a la base de datos'}), 500


if __name__ == '__main__':


    app.run(host='0.0.0.0', port=5001, debug=True)
