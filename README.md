# drybranch digital task management system
This repository includes scripts that I (chat GPT) have made to enable me more efficient task management.
The taskwarrior_to_todo script has been taken from [this repository](https://github.com/juzim/taskwarrior2todo.txt).

# Features
- parsing todo.txt and inserting tasks into taskwarrior
- parsing taskwarrior tasks and inserting into todo.txt
- backing up taskwarrior tasks to a seperate todo.txt file
- two way synchronization between taskwarrior and todoist
- backing up everything to OneDrive

# Prerequisites
- install taskwarrior
- install todoist
- install required python dependencie (will add requirements.txt in the future)
- add your todoist api key in the ./scripts/sync_todoist_taskwarrior.py file
- change paths to your own local paths so scripts work
- have fun :)

# Rant section
Basically I made this out of an obsession with productivity apps.
Feel free to fork, expand, yada yada, still a work in progress.
Might seem overly enginnered, that is because it is, I could literally just use one app for everything I myself struggle to find the usefuleness of this but hey at least my tasks are organized.
Please share if you find this useful, feel free to recommend me a calendar app that would have good integrations with this system.
You can reach me at jneelson08@gmail.com if you have anything to say.

# To Do
- [ ] add support to mark tasks as done from one application across all 4
- [ ] figure out a way to integrate this with some kind of calendar
- [ ] possibly code a ms todo obsidian plugin