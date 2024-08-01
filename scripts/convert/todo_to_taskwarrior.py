#!/usr/bin/env python3
import re
import subprocess
import json
import os

PRIORITY_MAP = {chr(i): 'L' for i in range(ord('D'), ord('Z') + 1)}
PRIORITY_MAP.update({'A': 'H', 'B': 'M', 'C': 'L'})

def parse_todo_txt_line(line):
    """Parse a single line from a todo.txt file."""
    is_complete = line.startswith('x ')
    if is_complete:
        line = line[2:]
        completed_date_match = re.match(r'(\d{4}-\d{2}-\d{2})', line)
        completed_date = completed_date_match.group(1) if completed_date_match else ''
        line = re.sub(r'\d{4}-\d{2}-\d{2}', '', line, 1).strip()
    else:
        completed_date = ''
    
    priority_match = re.match(r'\(([A-Z])\)', line)
    priority = priority_match.group(1) if priority_match else ''
    line = line[priority_match.end():].strip() if priority_match else line
    
    creation_date_match = re.match(r'(\d{4}-\d{2}-\d{2})', line)
    creation_date = creation_date_match.group(1) if creation_date_match else ''
    line = re.sub(r'\d{4}-\d{2}-\d{2}', '', line, 1).strip() if creation_date_match else line

    projects = re.findall(r'\+(\w+)', line)
    line = re.sub(r'\+\w+', '', line).strip()

    tags = re.findall(r'\@(\w+)', line)
    line = re.sub(r'\@\w+', '', line).strip()

    due_date_match = re.search(r'due:(\d{4}-\d{2}-\d{2})', line)
    due_date = due_date_match.group(1) if due_date_match else ''
    line = re.sub(r'due:\d{4}-\d{2}-\d{2}', '', line).strip()

    task = line
    return is_complete, priority, completed_date, creation_date, projects, tags, due_date, task

def map_priority(priority):
    return PRIORITY_MAP.get(priority, 'L')

def get_existing_tasks():
    cmd = ['task', 'export']
    result = subprocess.run(cmd, capture_output=True, text=True)
    tasks = json.loads(result.stdout)
    existing_tasks = {}
    for task in tasks:
        description = task.get('description', '').strip().lower()
        if description:
            existing_tasks[description] = (task['id'], task['status'], task)
    return existing_tasks

def insert_task_into_taskwarrior(description, priority, tags, is_complete, completed_date, due_date, projects):
    try:
        cmd = ['task', 'add', description]
        if priority:
            cmd.append(f'priority:{priority}')
        if tags:
            cmd.append(f'tag:{" ".join(tags)}')
        if due_date:
            cmd.append(f'due:{due_date}')
        if projects:
            cmd.append(f'project:{" ".join(projects)}')
        subprocess.run(cmd, check=True)
        if is_complete:
            cmd = ['task', description, 'done']
            subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error inserting task: {e}")

def update_task_in_taskwarrior(task_id, description, completed_date, due_date, priority, tags, projects):
    try:
        cmd = ['task', str(task_id), 'modify']
        if completed_date:
            cmd.append(f'end:{completed_date}')
        if due_date:
            cmd.append(f'due:{due_date}')
        if priority:
            cmd.append(f'priority:{priority}')
        if tags:
            cmd.append(f'tag:{" ".join(tags)}')
        if projects:
            cmd.append(f'project:{" ".join(projects)}')
        cmd.append(description)
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error updating task: {e}")

def delete_task_from_taskwarrior(task_id):
    try:
        cmd = ['task', str(task_id), 'delete']
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error deleting task: {e}")

def convert_and_insert_tasks(todo_file):
    existing_tasks = get_existing_tasks()
    current_tasks = set()

    with open(todo_file, 'r') as tf:
        for line in tf:
            line = line.strip()
            if not line:
                continue
            is_complete, priority, completed_date, creation_date, projects, tags, due_date, task = parse_todo_txt_line(line)
            full_description = task.lower()
            current_tasks.add(full_description)
            if full_description in existing_tasks:
                task_id, task_status, task_data = existing_tasks[full_description]
                if is_complete and task_status != 'completed':
                    update_task_in_taskwarrior(task_id, full_description, completed_date, due_date, map_priority(priority), tags, projects)
                elif not is_complete and task_status == 'completed':
                    insert_task_into_taskwarrior(full_description, map_priority(priority), tags, is_complete, completed_date, due_date, projects)
                else:
                    update_task_in_taskwarrior(task_id, full_description, completed_date, due_date, map_priority(priority), tags, projects)
            else:
                insert_task_into_taskwarrior(full_description, map_priority(priority), tags, is_complete, completed_date, due_date, projects)
    
    for description, (task_id, task_status, task_data) in existing_tasks.items():
        if description not in current_tasks:
            delete_task_from_taskwarrior(task_id)

convert_and_insert_tasks('/mnt/c/Users/tadej/Documents/Projects/free/productivity/todo/todo.txt')