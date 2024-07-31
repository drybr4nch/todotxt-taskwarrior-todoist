#!/usr/bin/python3

import subprocess
import json
import requests
from convert.todo_to_taskwarrior import parse_todo_txt_line
from datetime import date
from dotenv import load_dotenv
import os

load_dotenv()

# Configuration for Todoist API
TODOIST_API_TOKEN = os.getenv('TODOIST_API_TOKEN') 

def sync_tasks():
    # Load tasks from all sources
    todo_txt_tasks = load_from_todo_txt('/mnt/c/Users/tadej/Documents/Projects/free/productivity/todo/todo.txt')
    taskwarrior_tasks = load_from_taskwarrior()
    todoist_tasks = load_from_todoist()
    
    # Convert all tasks to a common model
    all_tasks = convert_to_common_model(todo_txt_tasks, taskwarrior_tasks, todoist_tasks)
    print(all_tasks)
    
    # Detect which tasks are marked as done
    done_tasks = detect_done_tasks(all_tasks)
    print(done_tasks)
    
    # Update all platforms
    update_todo_txt(done_tasks)
    update_taskwarrior(done_tasks)
    update_todoist(done_tasks)

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
    """Map Todo.txt priority to a common format."""
    priority_map = {'C': 'Low', 'B': 'Medium', 'A': 'High'}
    return priority_map.get(priority, 'None')  # Default to 'None' if priority is not found

def load_from_todoist():
    """Fetch tasks from Todoist and return them in a common format."""
    headers = {
        'Authorization': f'Bearer {TODOIST_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Fetch tasks from Todoist API
        response = requests.get('https://api.todoist.com/rest/v2/tasks', headers=headers)
        response.raise_for_status()
        tasks = response.json()
        
        # Convert Todoist tasks to a common model
        task_list = []
        for task in tasks:
            task_data = {
                'id' : task .get('id', ''),
                'description': task.get('content', ''),
                'is_completed': task.get('completed', False),
                'completed_date': task.get('completed_at', ''),
                'creation_date': task.get('created_at', ''),
                'priority': map_todoist_priority(task.get('priority', 0)),
                'due_date': task.get('due', {}),
                'projects': [],  # Projects might need additional handling
                'tags': []       # Tags might need additional handling
            }
            task_list.append(task_data)
        
        return task_list

    except requests.exceptions.RequestException as e:
        print(f"Error fetching tasks from Todoist: {e}")
        return []

def map_todoist_priority(priority):
    """Map Todoist priority to a common format."""
    priority_map = {1: 'Low', 2: 'Medium', 3: 'High', 4: 'Urgent'}
    return priority_map.get(priority, 'None')  # Default to 'None' if priority is not found

def load_from_taskwarrior():
    """Fetch tasks from Taskwarrior and return them in a common format."""
    try:
        # Fetch tasks from Taskwarrior in JSON format
        result = subprocess.run(['task', 'export'], capture_output=True, text=True, check=True)
        tasks = json.loads(result.stdout)
        
        # Convert Taskwarrior tasks to a common model
        task_list = []
        for task in tasks:
            task_data = {
                'description': task.get('description', ''),
                'is_completed': task.get('status') == 'completed',
                'creation_date': task.get('entry', ''),
                'priority': map_taskwarrior_priority(task.get('priority', '')),
                'due_date': task.get('due', ''),
                'projects': task.get('project', '').split(),
                'tags': task.get('tags', [])
            }
            task_list.append(task_data)
        
        return task_list

    except subprocess.CalledProcessError as e:
        print(f"Error fetching tasks from Taskwarrior: {e}")
        return []


def map_taskwarrior_priority(priority):
    """Map Taskwarrior priority to a common format."""
    priority_map = {'L': 'Low', 'M': 'Medium', 'H': 'High'}
    return priority_map.get(priority, 'None')  # Default to 'None' if priority is not found

def convert_to_common_model(todo_txt_tasks, taskwarrior_tasks, todoist_tasks):
    """Convert tasks from all sources to a common model."""
    all_tasks = []
    all_tasks.extend(todo_txt_tasks)
    all_tasks.extend(taskwarrior_tasks)
    all_tasks.extend(todoist_tasks)
    return all_tasks

def detect_done_tasks(all_tasks):
    """Detect tasks that are marked as done."""
    out_tasks = []
    task_counter_dict = {} 
    for task in all_tasks:
        task_counter_dict[task["description"]] = 0
    for task in all_tasks:
        if task in all_tasks:
            task_counter_dict[task["description"]] += 1
    for k, v in task_counter_dict.items():
        if v < 3:
            if k not in out_tasks:
                out_tasks.append(k)
             
    return out_tasks

def update_todo_txt(done_tasks):
    """Update todo.txt with completed tasks."""
    # Read the current todo.txt
    with open('/mnt/c/Users/tadej/Documents/Projects/free/productivity/todo/todo.txt', 'r') as tf:
        lines = tf.readlines()

    # Write updated content to todo.txt
    with open('/mnt/c/Users/tadej/Documents/Projects/free/productivity/todo/todo.txt', 'w') as tf:
        for line in lines:
            line_stripped = line.strip()
            is_complete, priority, completion_date, creation_date, projects, tags, due_date, task = parse_todo_txt_line(line_stripped)
            if any(task.strip() == done_task.strip() for done_task in done_tasks):
                tags_str = ' '.join(f"@{tag} " for tag in tags)
                tf.write(f"x ({priority}) {date.today()} {creation_date} {task} +{projects[0]} {tags_str} {due_date} \n")
            else:
                tf.write(f"{line_stripped}\n")

def update_taskwarrior(done_tasks):
    """Update Taskwarrior with completed tasks."""
    for task in done_tasks:
        command = ['task', task, 'done']
        try:
            subprocess.run(command, capture_output=True, text=True, check=True)
            print(f"Marked task '{task}' as completed in Taskwarrior")
        except subprocess.CalledProcessError as e:
            print(f"Error marking task '{task}' as completed in Taskwarrior: {e}")

def update_todoist(done_tasks):
    """Update Todoist with completed tasks."""
    headers = {
        'Authorization': f'Bearer {TODOIST_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    for task in done_tasks:
        # Find the task in Todoist
        todoist_tasks = load_from_todoist()
        task_id = next(t['id'] for t in todoist_tasks)
        
        if task_id:
            try:
                response = requests.post(f'https://api.todoist.com/rest/v2/tasks/{task_id}/close', headers=headers)
                response.raise_for_status()
                print(f"Marked task '{task_id}' as completed in Todoist")
            except requests.exceptions.RequestException as e:
                print(f"Error marking task '{task_id}' as completed in Todoist: {e}")

if __name__ == '__main__':
    sync_tasks()