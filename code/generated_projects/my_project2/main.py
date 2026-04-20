import sys
import os
from task_manager import TaskManager

TASKS_FILE = os.environ.get('TASKS_FILE', 'tasks.json')

def parse_args():
    if len(sys.argv) < 2:
        print("Error: No action specified.\nUsage: python main.py <action> [arguments]")
        return None
    action = sys.argv[1]
    if action == 'add':
        if len(sys.argv) < 3:
            print("Error: No task description specified.\nUsage: python main.py add <task_description>")
            return None
        task_description = ' '.join(sys.argv[2:])
        if not task_description:
            print("Error: Task description cannot be empty.\nUsage: python main.py add <task_description>")
            return None
        return {'action': 'add', 'task_description': task_description}
    elif action == 'list':
        return {'action': 'list'}
    elif action == 'complete':
        if len(sys.argv) < 3:
            print("Error: No task index specified.\nUsage: python main.py complete <task_index>")
            return None
        try:
            task_index = int(sys.argv[2])
            return {'action': 'complete', 'task_index': task_index}
        except ValueError:
            print("Error: Invalid task index.\nUsage: python main.py complete <task_index>")
            return None
    elif action == 'delete':
        if len(sys.argv) < 3:
            print("Error: No task index specified.\nUsage: python main.py delete <task_index>")
            return None
        try:
            task_index = int(sys.argv[2])
            return {'action': 'delete', 'task_index': task_index}
        except ValueError:
            print("Error: Invalid task index.\nUsage: python main.py delete <task_index>")
            return None
    else:
        print("Error: Unknown action.\nAvailable actions: add, list, complete, delete.")
        return None

def main():
    try:
        args = parse_args()
        if args is None:
            return
        task_manager = TaskManager()
        if args['action'] == 'add':
            task_manager.add_task(args['task_description'])
        elif args['action'] == 'list':
            task_manager.list_tasks()
        elif args['action'] == 'complete':
            task_manager.complete_task(args['task_index'])
        elif args['action'] == 'delete':
            task_manager.delete_task(args['task_index'])
    except Exception as e:
        print(f"Error: An unexpected error occurred - {str(e)}")

if __name__ == '__main__':
    main()