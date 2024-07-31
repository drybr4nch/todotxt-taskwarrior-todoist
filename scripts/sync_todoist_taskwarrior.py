#!/usr/bin/python3

import requests
import subprocess
import json
from datetime import datetime
import pytz
from dotenv import load_dotenv
import os

load_dotenv()

# Todoist Authentication
TODOIST_API_TOKEN = os.getenv('TODOIST_API_TOKEN')

# Priority mapping function
def map_priority(taskwarrior_priority):
    priority_map = {
        'H': 4,  # High priority
        'M': 3,  # Medium priority
        'L': 2,  # Low priority
        None: 1  # No priority
    }
    return priority_map.get(taskwarrior_priority, 1)

def priority_map(todoist_priority):
    map_priority = {
        4: 'H',  # High priority
        3: 'M',  # Medium priority
        2: 'L',  # Low priority
        1: None  # No priority
    }
    return map_priority.get(todoist_priority, None)

# Fetch projects from Todoist and create a mapping
def fetch_projects():
    headers = {
        'Authorization': f'Bearer {TODOIST_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    try:
        response = requests.get('https://api.todoist.com/rest/v2/projects', headers=headers)
        response.raise_for_status()
        projects = response.json()
        name_to_id = {project['name']: project['id'] for project in projects}
        id_to_name = {project['id']: project['name'] for project in projects}
        return name_to_id, id_to_name
    except requests.exceptions.RequestException as e:
        print(f"Error fetching projects from Todoist: {e}")
        return {}, {}

# Fetch labels from Todoist
def fetch_labels():
    headers = {
        'Authorization': f'Bearer {TODOIST_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    try:
        response = requests.get('https://api.todoist.com/rest/v2/labels', headers=headers)
        response.raise_for_status()
        labels = response.json()
        id_to_name = {label['id']: label['name'] for label in labels}
        name_to_id = {label['name']: label['id'] for label in labels}
        return name_to_id, id_to_name
    except requests.exceptions.RequestException as e:
        print(f"Error fetching labels from Todoist: {e}")
        return {}, {}

# Fetch tasks from Todoist
def fetch_tasks():
    headers = {
        'Authorization': f'Bearer {TODOIST_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    tasks = []
    url = 'https://api.todoist.com/rest/v2/tasks'
    
    while url:
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            tasks.extend(data)
            
            # Check for next page
            url = response.links.get('next', {}).get('url', None)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching tasks from Todoist: {e}")
            break
    
    return tasks

# Fetch tasks from Taskwarrior
def fetch_taskwarrior_tasks():
    try:
        result = subprocess.run(['task', 'export'], capture_output=True, text=True)
        tasks = json.loads(result.stdout)
        return tasks
    except Exception as e:
        print(f"Error fetching Taskwarrior tasks: {e}")
        return []

# Convert Taskwarrior due date to Todoist formats
def convert_due_date(due_date_str):
    if due_date_str is None:
        return None, None

    try:
        if len(due_date_str) == 16 and due_date_str[8] == 'T' and due_date_str[-1] == 'Z':
            parsed_date = datetime.strptime(due_date_str, '%Y%m%dT%H%M%SZ')
            parsed_date = pytz.utc.localize(parsed_date)  # Localize to UTC

            ljubljana_tz = pytz.timezone('Europe/Ljubljana')
            parsed_date = parsed_date.astimezone(ljubljana_tz)
            
            due_date = parsed_date.strftime('%Y-%m-%d')
            due_datetime = parsed_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            return due_date, due_datetime
        else:
            return None, None
    except ValueError:
        return None, None

# Add a task to Taskwarrior
def add_task_to_taskwarrior(task):
    command = ['task', 'add', task['description']]
    
    if task.get('due'):
        if not task.get('due') is None:
            command.append(f'due:{task["due"]}')
    
    if task.get('priority'):
        if not priority_map(task["priority"]) is None:
            command.append(f'priority:{priority_map(task["priority"])}')
    
    if task.get('project'):
        if not task.get('project') is None:
            command.append(f'project:{task["project"]}')
    
    if task.get('tags'):
        if not task.get('tags') is None:
            tags = ','.join(task['tags'])
            command.append(f'tags:{tags}')
    
    try:
        subprocess.run(command, capture_output=True, text=True, check=True)
        print(f"Added task to Taskwarrior: {task['description']}")
    except subprocess.CalledProcessError as e:
        print(f"Error adding task to Taskwarrior: {e}")

# Add a task to Todoist
def add_task_to_todoist(task, project_mapping, label_mapping):
    headers = {
        'Authorization': f'Bearer {TODOIST_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    try:
        due_date, due_datetime = convert_due_date(task.get('due'))

        task_project_name = task.get('project', 'Default Project')
        project_id = project_mapping.get(task_project_name, None)

        task_priority = task.get('priority', None)
        todoist_priority = map_priority(task_priority)

        task_labels = task.get('tags', [])
        label_ids = [label_mapping.get(label, None) for label in task_labels if label_mapping.get(label, None) is not None]

        data = {
            'content': task['description'],
            'project_id': project_id,
            'due_date': due_date,
            'due_datetime': due_datetime,
            'priority': todoist_priority,
            'labels': label_ids
        }
        response = requests.post('https://api.todoist.com/rest/v2/tasks', headers=headers, json=data)
        response.raise_for_status()
        print(f"Added task to Todoist: {task['description']}")
    except requests.exceptions.RequestException as e:
        print(f"Error adding task to Todoist: {e}")

# Sync tasks between Todoist and Taskwarrior
def sync_tasks(todoist_tasks, taskwarrior_tasks):
    name_to_id, id_to_name = fetch_projects()
    if not name_to_id:
        print("No projects found in Todoist. Please create a project first.")
        return

    label_mapping, _ = fetch_labels()
    if not label_mapping:
        print("No labels found in Todoist. Please create labels first.")
        return

    todoist_task_descriptions = {task['content'] for task in todoist_tasks}

    for task in taskwarrior_tasks:
        if task['description'] not in todoist_task_descriptions:
            try:
                due_date, due_datetime = convert_due_date(task.get('due'))

                task_project_name = task.get('project', 'Default Project')
                project_id = name_to_id.get(task_project_name, None)

                task_priority = task.get('priority', None)
                todoist_priority = map_priority(task_priority)

                task_tags = task.get('tags', [])

                data = {
                    'content': task['description'],
                    'project_id': project_id,
                    'due_date': due_date,
                    'due_datetime': due_datetime,
                    'priority': todoist_priority,
                    'labels': task_tags
                }
                headers = {
                    'Authorization': f'Bearer {TODOIST_API_TOKEN}',
                    'Content-Type': 'application/json'
                }
                response = requests.post('https://api.todoist.com/rest/v2/tasks', headers=headers, json=data)
                response.raise_for_status()
                print(f"Added task to Todoist: {task['description']}")
            except requests.exceptions.RequestException as e:
                print(f"Error adding task to Todoist: {e}")

    taskwarrior_tasks_set = {task['description'] for task in taskwarrior_tasks}

    for task in todoist_tasks:
        if task['content'] not in taskwarrior_tasks_set:
            task_data = {
                'description': task['content'],
                'due': task.get('due_date', None),
                'priority': task.get('priority', None),
                'project': id_to_name.get(task.get('project_id', None), 'Default Project'),
                'tags': [label for label in task.get('labels', []) if label in label_mapping]
            }
            add_task_to_taskwarrior(task_data)

# Main function
def main():
    todoist_tasks = fetch_tasks()
    taskwarrior_tasks = fetch_taskwarrior_tasks()
    sync_tasks(todoist_tasks, taskwarrior_tasks)

if __name__ == "__main__":
    main()