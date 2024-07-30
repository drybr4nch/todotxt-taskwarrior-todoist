#!/usr/bin/env python3
import re
import subprocess
import json

# Define a mapping from todo.txt priorities to Taskwarrior priorities
PRIORITY_MAP = {
    'A': 'H',  # High
    'B': 'M',  # Medium
    'C': 'L',  # Low
    'D': 'L',  # Default for D to Z as Low
    'E': 'L', 'F': 'L', 'G': 'L', 'H': 'L', 'I': 'L',
    'J': 'L', 'K': 'L', 'L': 'L', 'M': 'L', 'N': 'L',
    'O': 'L', 'P': 'L', 'Q': 'L', 'R': 'L', 'S': 'L',
    'T': 'L', 'U': 'L', 'V': 'L', 'W': 'L', 'X': 'L',
    'Y': 'L', 'Z': 'L'
}

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
    
    # Match priority enclosed in parentheses (single uppercase letter)
    priority_match = re.match(r'\(([A-Z])\)', line)
    priority = priority_match.group(1) if priority_match else ''
    line = line[priority_match.end():].strip() if priority_match else line
    
    creation_date_match = re.match(r'(\d{4}-\d{2}-\d{2})', line)
    creation_date = creation_date_match.group(1) if creation_date_match else ''
    line = re.sub(r'\d{4}-\d{2}-\d{2}', '', line).strip() if creation_date_match else line

    due_date_match = re.search(r'due:(\d{4}-\d{2}-\d{2})', line)
    due_date = due_date_match.group(1) if due_date_match else ''
    line = re.sub(r'due:\d{4}-\d{2}-\d{2}', '', line).strip() if due_date_match else line

    # Extract projects (+Project)
    projects = re.findall(r'\+(\w+)', line)
    line = re.sub(r'\+\w+', '', line).strip()

    # Extract tags (@tag)
    tags = re.findall(r'\@(\w+)', line)
    line = re.sub(r'\@\w+', '', line).strip()

    # Extract description (after " -- ")
    parts = line.split(' -- ', 1)
    task = parts[0].strip()
    description = parts[1].strip() if len(parts) > 1 else ''

    return is_complete, completed_date, creation_date, priority, due_date, projects, tags, task, description

def map_priority(todo_priority):
    """Map todo.txt priority to Taskwarrior priority."""
    return PRIORITY_MAP.get(todo_priority, '')  # Default to Low priority if not found

def get_existing_tasks():
    """Fetch existing tasks from Taskwarrior."""
    try:
        result = subprocess.run(['task', 'export'], capture_output=True, text=True, check=True)
        tasks = json.loads(result.stdout)
        return {task['description']: (task['id'], task['status'], task) for task in tasks}
    except subprocess.CalledProcessError as e:
        print(f"Error fetching existing tasks: {e}")
        return {}

def insert_task_into_taskwarrior(description, priority, tags, is_complete, completed_date, due_date, projects):
    """Insert a task into Taskwarrior."""
    cmd = ['task', 'add', description]
    if priority:
        cmd.append(f'priority:{priority}')
    if tags:
        cmd.append(f'tags:{" ".join(tags)}')
    if projects:
        cmd.append(f'project:{" ".join(projects)}')
    if due_date:
        cmd.append(f'due:{due_date}')
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if is_complete:
            task_id = re.search(r'Created task (\d+)', result.stdout).group(1)
            complete_cmd = ['task', str(task_id), 'done']
            if completed_date:
                complete_cmd.extend(['--', f'end:{completed_date}'])
            subprocess.run(complete_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error adding task: {e}")

def update_task_in_taskwarrior(task_id, description, completed_date, due_date, priority, tags, projects):
    """Update an existing task in Taskwarrior."""
    try:
        cmd = ['task', str(task_id), 'modify']
        cmd.append(f'end:{completed_date}')
        cmd.append(f'due:{due_date}')
        cmd.append(f'priority:{priority}')
        cmd.append(f'tags:{" ".join(tags)}')
        cmd.append(f'project:{" ".join(projects)}')
        cmd.append(f'description:{description}')
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error updating task: {e}")

def convert_and_insert_tasks(todo_file):
    """Convert tasks from todo.txt format and insert or update in Taskwarrior."""
    existing_tasks = get_existing_tasks()
    with open(todo_file, 'r') as tf:
        for line in tf:
            line = line.strip()
            if not line:
                continue
            is_complete, completed_date, creation_date, priority, due_date, projects, tags, task, description = parse_todo_txt_line(line)
            full_description = f"{task} -- {description}" if description else task
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

# Example Usage
convert_and_insert_tasks('/mnt/c/Users/tadej/Documents/Projects/free/productivity/todo/todo.txt')