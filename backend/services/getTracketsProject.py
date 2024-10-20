import requests
from requests.auth import HTTPBasicAuth
from flask import Flask
from flask import jsonify

def getDataProject(url, user, passw):
    offset = 0
    limit = 100
    grouped_projects = {}
    duplicados = []
    seen = set()

    while True:
        try:
            r = requests.get(f"{url}/issues.json?limit={limit}&offset={offset}", auth=HTTPBasicAuth(user, passw))
            r.raise_for_status()

            issues = r.json()

            for issue in issues['issues']:
                nombre_proyecto = issue['project']['name']
                id_proyecto = issue['project']['id']
                tracker_name = issue['tracker']['name']
                issue_subject = issue['subject']

                if tracker_name.startswith('P_'):
                    # Si el proyecto no existe aún, lo creamos
                    if id_proyecto not in grouped_projects:
                        grouped_projects[id_proyecto] = {
                            'worker_name': user,  
                            'project_id': id_proyecto,
                            'project_name': nombre_proyecto,
                            'trackers': {}
                        }

                    # Si el tracker_name no existe aún en este proyecto, lo creamos
                    if tracker_name not in grouped_projects[id_proyecto]['trackers']:
                        grouped_projects[id_proyecto]['trackers'][tracker_name] = {
                            'tracker_name': tracker_name,
                            'subjects': []
                        }

                    # Añadir el subject al tracker, si no está ya en la lista
                    if issue_subject not in grouped_projects[id_proyecto]['trackers'][tracker_name]['subjects']:
                        grouped_projects[id_proyecto]['trackers'][tracker_name]['subjects'].append(issue_subject)

                    # Comprobación de duplicados
                    if tracker_name in seen:
                        duplicados.append(tracker_name)
                    else:
                        seen.add(tracker_name)

            if len(issues['issues']) < limit:
                break

            offset += limit

        except requests.exceptions.HTTPError as http_err:
            return {'error': f"Errorr: {http_err}", 'status_code': r.status_code}
        except Exception as err:
            return {'error': f"Errror: {err}"}

    all_trackers = [
        {
            'worker_name': project['worker_name'],  
            'project_id': project['project_id'],
            'project_name': project['project_name'],
            'trackers': [
                {
                    'tracker_name': tracker['tracker_name'],
                    'subjects': tracker['subjects']
                } for tracker in project['trackers'].values()
            ]
        } for project in grouped_projects.values()
    ]
    return all_trackers

