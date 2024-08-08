#!/bin/bash

/usr/bin/python3 /mnt/c/Users/tadej/Documents/Projects/free/productivity/scripts/sync_all_three.py
/usr/bin/python3 /mnt/c/Users/tadej/Documents/Projects/free/productivity/scripts/convert/todo_to_taskwarrior.py
/usr/bin/python3 /mnt/c/Users/tadej/Documents/Projects/free/productivity/scripts/sync_todoist_taskwarrior.py
task export > /mnt/c/Users/tadej/Documents/Projects/free/productivity/todo/export.json
/usr/bin/python3 /mnt/c/Users/tadej/Documents/Projects/free/productivity/scripts/convert/taskwarrior_to_todo.py -i /mnt/c/Users/tadej/Documents/Projects/free/productivity/todo/export.json -o /mnt/c/Users/tadej/Documents/Projects/free/productivity/todo/todo.txt -a /mnt/c/Users/tadej/Documents/Projects/free/productivity/todo/done.txt
task sync
/mnt/c/Users/tadej/Documents/Projects/free/productivity/scripts/backup/backup_to_vault.sh
/usr/bin/python3 /mnt/c/Users/tadej/Documents/Projects/free/productivity/scripts/backup/backup_obsidian.py