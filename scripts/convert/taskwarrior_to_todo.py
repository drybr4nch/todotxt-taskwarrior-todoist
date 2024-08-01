import json
import argparse
import logging
from dateutil.parser import parse
import os

def main():
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    parser = argparse.ArgumentParser(
        description='Convert taskwarrior exports to todo.txt format',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-i', '--input', required=True, help='input JSON file')
    parser.add_argument('-o', '--output', required=True, help='output location')
    parser.add_argument('-a', '--archive', help='archive location, otherwise completed tasks are stored in the same file')
    parser.add_argument('-s', '--skipCompleted', help='Ignore already completed tasks', action="store_true")
    parser.add_argument('-ns', '--noSort', help='Do not sort the results', action="store_true")

    args = parser.parse_args()
    priorities = {'L': '(C)', 'M': '(B)', 'H': '(A)'}

    logger.debug('Starting conversion')

    try:
        with open(args.input, 'r') as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f'Could not open or parse input file: {e}')
        return

    logger.debug(f'Found {len(data)} entries')

    result = []
    archive = []

    # Track previously existing tasks
    previous_tasks = load_previous_tasks(args.output)
    current_tasks = {entry['description'].strip() for entry in data if 'description' in entry}
    deleted_tasks = previous_tasks - current_tasks

    for entry in data:
        stringParts = []
        description = entry.get('description', '').strip()
        print(entry)

        if entry['status'] == 'completed':
            if args.skipCompleted:
                continue
            stringParts.append('x')
            stringParts.append(parse(entry.get('end', entry['modified'])).strftime('%Y-%m-%d'))

        if 'priority' in entry:
            stringParts.append(priorities.get(entry['priority'], '(D)'))

        stringParts.append(description)

        # Handle projects
        if 'project' in entry:
            projectName = entry['project']
            stringParts.append('+' + projectName)

        # Handle tags
        if 'tags' in entry:
            for tag in entry['tags']:
                if f'@{tag}' not in description:
                    description += f' @{tag}'

        # Handle due dates
        if 'due' in entry:
            stringParts.append('due:' + parse(entry['due']).strftime("%Y-%m-%d"))


        # Join parts ensuring no double spaces or extra characters
        string = ' '.join(filter(None, stringParts)).strip()
        if not string:
            continue

        if entry['status'] == 'completed' and args.archive:
            archive.append(string)
        else:
            result.append(string)

    if not args.noSort:
        result = sorted(result)
        archive = sorted(archive)

    with open(args.output, 'w') as file:
        file.write("\n".join(result) + "\n")

    if args.archive:
        with open(args.archive, 'w') as file:
            file.write("\n".join(archive) + "\n")
    elif len(archive) > 0:
        with open(args.output, 'a') as file:
            file.write("\n".join(archive) + "\n")

    logger.debug('Done')

def load_previous_tasks(output_file):
    if os.path.exists(output_file):
        with open(output_file, 'r') as file:
            return {line.strip().split(' ', 1)[-1] for line in file.readlines() if line.strip()}
    return set()

if __name__ == '__main__':
    main()