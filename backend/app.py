from datetime import datetime
from flask import send_from_directory
from flask import Flask, jsonify, request
from configs.database import db
from configs.config import Config
from services.getTracketsProject import getDataProject
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError
from configs.models import (
    Project,
    Device,
    Worker,
    Subtracker,
    DeviceSubtracker,
    Response,
    Question  
)
from flask_cors import CORS

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, resources={r"/*": {"origins": ["http://localhost:3000", "http://127.0.0.1"]}})
db.init_app(app)

migrate = Migrate(app, db)


@app.route('/issues.json')
def get_issues():
    return send_from_directory('', 'salida.json')

@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()

@app.route("/ping")
def testping():
    return "pong"

@app.route('/data', methods=['POST'])
def handle_data():
    data = request.get_json()
    url, user, password = data.get('url'), data.get('user'), data.get('pass')

    if not url or not user or not password:
        return jsonify({'success': False, 'message': 'Faltan datos en el formulario'}), 400

    try:
        project_data = getDataProject(url, user, password)
        if not project_data or not isinstance(project_data, list):
            return jsonify({'success': False, 'message': 'Datos del proyecto no válidos'}), 400

        project_name = project_data[0].get('project_name')
        worker_name = project_data[0].get('worker_name')
        trackers = project_data[0].get('trackers', [])

        if not project_name or not worker_name:
            raise ValueError("Faltan datos obligatorios: project_name o worker_name")

        project_id = insert_project(project_name)
        worker_id = insert_worker(worker_name)
        tracker_results = []

        for tracker in trackers:
            tracker_name = tracker.get('tracker_name')
            subjects = tracker.get('subjects', [])
            device = Device.query.filter_by(name=tracker_name).first()
            if not device:
                continue

            device_id = device.id
            tracker_info = {'tracker_name': tracker_name, 'subjects': []}

            for subject in subjects:
                subtracker_id = insert_subtracker(project_id, subject)
                insert_device_subtracker(device_id, subtracker_id)
                
                questions = get_questions_for_subtracker_and_device(subtracker_id, device_id)

                # Inserta o actualiza respuestas
                for question_block in questions.get('subjects', []):
                    for question in question_block['questions']:
                        question_id = question['id']
                        insert_response(
                            subtracker_id=subtracker_id,
                            device_id=device_id,
                            question_id=question_id,
                            project_id=project_id,
                            worker_id=worker_id
                        )

                tracker_info['subjects'].append({'subject': subject, 'questions': questions})

            tracker_results.append(tracker_info)

        return jsonify({'success': True, 'project_name': project_name, 'trackers': tracker_results, 'worker_name': worker_name})

    except IntegrityError as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error de integridad: {str(e.orig)}'}), 500

    except Exception as e:
        print(f"Error en handle_data: {str(e)}")
        return jsonify({'success': False, 'message': f'Error al procesar los datos: {str(e)}'}), 500
    


def insert_response(subtracker_id, device_id, question_id, project_id, worker_id, response_text=None, status='pending', comments=None):
    try:
        existing_response = Response.query.filter_by(
            subtracker_id=subtracker_id,
            device_id=device_id,
            question_id=question_id,
            project_id=project_id,
            worker_id=worker_id
        ).first()

        if existing_response:
            existing_response.response_text = response_text
            existing_response.status = status
            existing_response.comments = comments
            print(f"Actualizando respuesta existente: {existing_response.id}")
        else:
            new_response = Response(
                subtracker_id=subtracker_id,
                device_id=device_id,
                question_id=question_id,
                project_id=project_id,
                worker_id=worker_id,
                response_text=response_text,
                status=status,
                comments=comments
            )
            db.session.add(new_response)
            print(f"Insertando nueva respuesta para question_id={question_id}")

        db.session.commit()

    except IntegrityError as e:
        db.session.rollback()
        print(f"Error de integridad al insertar respuesta: {str(e.orig)}")
        raise
    except Exception as e:
        db.session.rollback()
        print(f"Error al insertar respuesta: {str(e)}")
        raise

def get_questions_for_subtracker_and_device(subtracker_id, device_id):
    subtracker = db.session.get(Subtracker, subtracker_id)
    device = db.session.get(Device, device_id)

    result = {'tracker_name': subtracker.name, 'subjects': []}
    for question_block in device.question_blocks:
        questions = [{'id': q.id, 'question_text': q.question_text, 'expected_result': q.expected_result} for q in question_block.questions]
        if questions:
            result['subjects'].append({'question_block': question_block.name, 'questions': questions})
    return result

def insert_worker(worker_name):
    worker = Worker.query.filter_by(name=worker_name).first()
    if worker: 
        return worker.id
    new_worker = Worker(name=worker_name)
    db.session.add(new_worker)
    db.session.commit()
    return new_worker.id

def insert_device_subtracker(device_id, subtracker_id):
    if not DeviceSubtracker.query.filter_by(device_id=device_id, subtracker_id=subtracker_id).first():
        db.session.add(DeviceSubtracker(device_id=device_id, subtracker_id=subtracker_id))
        db.session.commit()

def insert_project(project_name):
    project = Project.query.filter_by(name=project_name).first()
    if project: 
        return project.id
    new_project = Project(name=project_name)
    db.session.add(new_project)
    db.session.commit()
    return new_project.id

def insert_subtracker(project_id, subject):
    subtracker = Subtracker.query.filter_by(name=subject).first()
    if subtracker: 
        return subtracker.id
    new_subtracker = Subtracker(name=subject, project_id=project_id)
    db.session.add(new_subtracker)
    db.session.commit()
    return new_subtracker.id

if __name__ == '__main__':
    with app.app_context(): 
        db.create_all()
    app.run(host='0.0.0.0', port=7575, debug=True)