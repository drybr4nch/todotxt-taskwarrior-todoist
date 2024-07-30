#!/bin/bash
task export > "../todo/export.json"
/usr/bin/python3 /mnt/c/Users/tadej/Documents/Projects/free/productivity/scripts/convert/taskwarrior_to_todo.py -i /mnt/c/Users/tadej/Documents/Projects/free/productivity/todo/export.json -o /mnt/c/Users/tadej/Documents/Projects/free/productivity/todo/todo_backup.txt -a ../todo/done_backup.txt
cp /mnt/c/Users/tadej/Documents/Projects/free/productivity/todo/todo_backup.txt /mnt/c/Users/tadej/OneDrive/Documents/todo/todo.txt
cp /mnt/c/Users/tadej/Documents/Projects/free/productivity/todo/done_backup.txt /mnt/c/Users/tadej/OneDrive/Documents/todo/done.txt