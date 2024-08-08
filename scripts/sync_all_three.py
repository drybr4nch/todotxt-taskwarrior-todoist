#!/usr/bin/python3

import subprocess
import json
import requests
from datetime import datetime
from collections import defaultdict
from dotenv import load_dotenv
import os
from convert.todo_to_taskwarrior import parse_todo_txt_line
import re

load_dotenv()

TODOIST_API_TOKEN = os.getenv('TODOIST_API_TOKEN')
todo_file_path = '/mnt/c/Users/tadej/Documents/Projects/free/productivity/todo/todo.txt'

def sync_tasks():
    todo_txt_tasks = load_from_todo_txt(todo_file_path)
    taskwarrior_tasks = load_from_taskwarrior()
    todoist_tasks = load_done_from_todoist()

    all_tasks = convert_to_common_model(todo_txt_tasks, taskwarrior_tasks, todoist_tasks['items'])

    done_tasks = detect_done_tasks(all_tasks)

    deleted_tasks = detect_deleted_tasks(all_tasks)

    update_todo_txt(done_tasks, deleted_tasks, todo_file_path)
    update_taskwarrior(done_tasks)
    update_todoist(done_tasks, deleted_tasks)

    save_current_state(all_tasks)

def load_from_todo_txt(todo_file):
    tasks = []
    with open(todo_file, 'r') as tf:
        for line in tf:
            line = line.strip()
            if not line:
                continue
            is_complete, completed_date, creation_date, priority, due_date, projects, tags, task = parse_todo_txt_line(line)
            task_data = {
                'description': task,
                'is_completed': is_complete,
                'completed_date': completed_date,
                'creation_date': creation_date,
                'priority': map_todotxt_priority(priority),
                'due_date': due_date,
                'projects': projects,
                'tags': tags
            }
            tasks.append(task_data)
    return tasks

def map_todotxt_priority(priority):
    priority_map = {'C': 'Low', 'B': 'Medium', 'A': 'High'}
    return priority_map.get(priority, 'None')

def load_from_taskwarrior():
    command = ['task', 'export']
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        tasks = json.loads(result.stdout)
        return tasks
    except subprocess.CalledProcessError as e:
        print(f"Error loading tasks from Taskwarrior: {e}")
        return []

def load_done_from_todoist():
    headers = {
        'Authorization': f'Bearer {TODOIST_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    try:
        response = requests.get('https://api.todoist.com/sync/v9/completed/get_all', headers=headers)
        response.raise_for_status()
        tasks = response.json()
        return tasks
    except requests.exceptions.RequestException as e:
        print(f"Error loading tasks from Todoist: {e}")
        return []

def load_from_todoist():
    headers = {
        'Authorization': f'Bearer {TODOIST_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    try:
        response = requests.get('https://api.todoist.com/rest/v3/tasks', headers=headers)
        response.raise_for_status()
        tasks = response.json()
        return tasks
    except requests.exceptions.RequestException as e:
        print(f"Error loading tasks from Todoist: {e}")
        return []

def convert_to_common_model(todo_txt_tasks, taskwarrior_tasks, todoist_tasks):
    common_tasks = []

    for task in todo_txt_tasks:
        common_tasks.append({
            'id': task.get('id') or task.get('uuid', ''),
            'description': task.get('description', '').strip().lower(),
            'is_completed': task.get('is_completed', False),
            'priority': task.get('priority', 'None'),
            'due_date': task.get('due_date', ''),
            'projects': task.get('projects', []),
            'tags': task.get('tags', '').split(),
            'source': 'todo_txt'
        })

    for task in taskwarrior_tasks:
        common_tasks.append({
            'id': task.get('uuid', ''),
            'description': task.get('description', '').strip().lower(),
            'is_completed': task.get('status') == 'completed',
            'priority': task.get('priority', ''),
            'due_date': task.get('due', ''),
            'projects': [task.get('project', '')],
            'tags': task.get('tags', []),
            'source': 'taskwarrior'
        })

    for task in todoist_tasks:
        common_tasks.append({
            'id': task.get('id', ''),
            'description': task.get('content', '').strip().lower(),
            'is_completed': True,
            'priority': task.get('priority', ''),
            'due_date': task.get('due', {}).get('date', '') if task.get('due') else '',
            'projects': [task.get('project_id', '')],
            'tags': task.get('labels', []),
            'source': 'todoist'
        })

    return common_tasks

def detect_done_tasks(all_tasks):
    done_tasks = []

    for task in all_tasks:
        if task['is_completed']:
            done_tasks.append(task)
    
    return done_tasks

def detect_deleted_tasks(all_tasks):
    previous_tasks = load_previous_state()

    previous_task_descriptions = {task['description'] for task in previous_tasks}
    current_task_descriptions = {task['description'] for task in all_tasks}

    deleted_tasks = previous_task_descriptions - current_task_descriptions
    return list(deleted_tasks)

def update_todo_txt(done_tasks, deleted_tasks, todo_file):
    """Update Todo.txt with completed and deleted tasks."""
    with open(todo_file, 'r') as file:
        lines = file.readlines()

    updated_tasks = []
    processed_tasks = set()
    
     # Ensure done_tasks and deleted_tasks are lists of dictionaries with 'description' keys
    done_tasks_set = set()
    for task in done_tasks:
        if isinstance(task, dict) and 'description' in task:
            done_tasks_set.add(task['description'].strip())
        else:
            print(f"Warning: Expected dict in done_tasks, got {type(task)}")

    deleted_tasks_set = set()
    for task in deleted_tasks:
        if isinstance(task, dict) and 'description' in task:
            deleted_tasks_set.add(task['description'].strip())
        else:
            print(f"Warning: Expected dict in deleted_tasks, got {type(task)}")

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        is_complete = line_stripped.startswith('x ')
        has_project = line_stripped.startswith("(")
        task_priority = line_stripped[:2]
        created_date = ""
        if is_complete:
            created_date = line_stripped.split(" ")[3]
        else:
            created_date = line_stripped.split(" ")[1]
        task_description = re.split(r'[+@]|due:', line_stripped)[0]
        if is_complete and not has_project:
            task_description = task_description[3:]
        elif is_complete and has_project:
            task_description = task_description[5:]
        elif not is_complete and has_project:
            task_description = task_description[1:]
        elif not is_complete and not has_project:
            task_description = task_description

        task_description = task_description.strip()
        if task_description in processed_tasks or task_description in deleted_tasks_set:
            continue
        
        if done_tasks_set.__contains__(task_description):
            if not is_complete:
                completion_date = datetime.now().strftime("%Y-%m-%d")
                updated_tasks.append(f"x {task_priority} {completion_date} {created_date} {task_description}\n")
            else:
                updated_tasks.append(line_stripped + '\n')
            done_tasks_set.remove(task_description)
        elif task_description not in done_tasks_set and task_description not in deleted_tasks_set:
            updated_tasks.append(line_stripped + '\n')

        processed_tasks.add(task_description)

    with open(todo_file, 'w') as file:
        file.writelines(updated_tasks)

    print(f"Updated {len(updated_tasks)} tasks in Todo.txt.")

def is_task_completed(task):
    """Check if a task is marked as completed."""
    return task.get('status', '') == 'completed'

def update_taskwarrior(tasks):
    for task in tasks:
        description = task['description']
        if task['is_completed']:
            try:
                result = subprocess.run(['task', description, 'done'], check=True, text=True, capture_output=True)
                print(f"Marked task '{description}' as completed in Taskwarrior")
            except subprocess.CalledProcessError as e:
                print(f"Error marking task '{description}' as completed in Taskwarrior: {e}")
        else:
            return

def update_todoist(done_tasks, deleted_tasks):
    headers = {
        'Authorization': f'Bearer {TODOIST_API_TOKEN}',
        'Content-Type': 'application/json'
    }

    for task in done_tasks:
        todoist_tasks = load_from_todoist()
        task_id = next((t['id'] for t in todoist_tasks if t['description']== task['description'] or t['content'] == task['description']), None)

        if task_id:
            try:
                response = requests.post(f'https://api.todoist.com/rest/v3/tasks/{task_id}/close', headers=headers)
                response.raise_for_status()
                print(f"Marked task '{task_id}' as completed in Todoist")
            except requests.exceptions.RequestException as e:
                print(f"Error marking task '{task_id}' as completed in Todoist: {e}")

    for task in deleted_tasks:
        print(f"updating task {task} in todoist (is deleted)")
        todoist_tasks = load_from_todoist()
        task_id = next((t['id'] for t in todoist_tasks if t['description'] == task['description'] or t['content'] == task['description']), None)

        if task_id:
            try:
                response = requests.delete(f'https://api.todoist.com/rest/v3/tasks/{task_id}', headers=headers)
                response.raise_for_status()
                print(f"Deleted task '{task_id}' from Todoist")
            except requests.exceptions.RequestException as e:
                print(f"Error deleting task '{task_id}' from Todoist: {e}")

def save_current_state(all_tasks):
    with open('tasks_state.json', 'w') as f:
        json.dump(all_tasks, f)

def load_previous_state():
    if os.path.exists('tasks_state.json'):
        with open('tasks_state.json', 'r') as f:
            return json.load(f)
    return []

if __name__ == '__main__':
    sync_tasks()