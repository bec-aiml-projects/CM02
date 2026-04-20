import json
import os

TASKS_FILE = os.environ.get('TASKS_FILE', 'tasks.json')

def load_tasks():
    try:
        with open(TASKS_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        print(f"Error: Unable to parse tasks file - {str(e)}")
        return []

def save_tasks(tasks):
    try:
        with open(TASKS_FILE, 'w') as file:
            json.dump(tasks, file)
    except Exception as e:
        print(f"Error: Unable to save tasks - {str(e)}")