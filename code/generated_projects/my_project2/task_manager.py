import json
from storage import load_tasks, save_tasks

class Task:
    def __init__(self, description, due_date=None):
        if not description:
            raise ValueError("Task description cannot be empty.")
        self.description = description
        self.due_date = due_date
        self.completed = False

    def mark_as_completed(self):
        self.completed = True

    def is_completed(self):
        return self.completed

    def to_dict(self):
        return {'description': self.description, 'due_date': self.due_date, 'completed': self.completed}

    @classmethod
    def from_dict(cls, task_dict):
        return cls(task_dict['description'], task_dict['due_date'])

class TaskManager:
    def __init__(self):
        self.tasks = self.load_tasks()

    def load_tasks(self):
        tasks = load_tasks()
        return [Task.from_dict(task) for task in tasks]

    def save_tasks(self):
        tasks = [task.to_dict() for task in self.tasks]
        save_tasks(tasks)

    def add_task(self, description):
        if not description:
            print("Error: Task description cannot be empty.")
            return
        new_task = Task(description)
        self.tasks.append(new_task)
        self.save_tasks()

    def list_tasks(self):
        if not self.tasks:
            print("No tasks available.")
            return
        for i, task in enumerate(self.tasks):
            status = 'Completed' if task.is_completed() else 'Pending'
            print(f"{i+1}. {task.description} - {status}")

    def complete_task(self, index):
        try:
            task = self.tasks[index-1]
            task.mark_as_completed()
            self.save_tasks()
        except IndexError:
            print("Error: Invalid task index.")

    def delete_task(self, index):
        try:
            del self.tasks[index-1]
            self.save_tasks()
        except IndexError:
            print("Error: Invalid task index.")