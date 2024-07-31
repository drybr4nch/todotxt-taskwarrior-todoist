#!/bin/bash

/usr/bin/python3 /mnt/c/Users/tadej/Documents/Projects/free/productivity/scripts/convert/todo_to_taskwarrior.py
/usr/bin/python3 /mnt/c/Users/tadej/Documents/Projects/free/productivity/scripts/sync_todoist_taskwarrior.py
/usr/bin/python3 /mnt/c/Users/tadej/Documents/Projects/free/productivity/scripts/convert/taskwarrior_to_todo.py -i /mnt/c/Users/tadej/Documents/Projects/free/productivity/todo/export.json -o /mnt/c/Users/tadej/Documents/Projects/free/productivity/todo/todo.txt -a ../todo/done.txt
/usr/bin/python3 /mnt/c/Users/tadej/Documents/Projects/free/productivity/scripts/sync_all_three.py
task sync