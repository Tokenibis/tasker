#!/usr/bin/python3

import sys
import json
import argparse
import textwrap

from collections import OrderedDict
from datetime import datetime, date, timedelta


class Manage:
    def __init__(self):
        parser = argparse.ArgumentParser(
            description='Manage tasking records',
            usage='''./manage.py <command> [<args>]
            view      view single task
            list      list all tasks for volunteer
            add       add new task
            close     close out a task
            open      reopen a task
            edit      edit a task
            delete    delete task
            ''',
        )
        parser.add_argument('command', help='subcommand to run')
        args = parser.parse_args(sys.argv[1:2])

        if not hasattr(self, args.command):
            print('Command not found')
            parser.print_help()
            exit(1)

        with open('record.json') as fd:
            self._data = json.load(fd, object_pairs_hook=OrderedDict)

        getattr(self, args.command)()

        with open('record.json', 'w') as fd:
            json.dump(self._data, fd, indent=2)

    def view(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('volunteer', help='id of volunteer')
        parser.add_argument('index', type=int, help='task index')
        args = parser.parse_args(sys.argv[2:])

        task = self._data[args.volunteer]['tasks'][args.index]

        self._print_task(args.volunteer, args.index, task)

    def list(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('volunteer', help='id of volunteer')
        args = parser.parse_args(sys.argv[2:])

        print('\nTasks:')
        print(
            '------------------------------------------------------------------------'
        )
        for i, task in enumerate(self._data[args.volunteer]['tasks']):
            print('{} (id: {}, started: {}, {})'.format(
                task['name'],
                i,
                task['start'],
                'closed' if task['end'] else 'open',
            ))
        print()

    def add(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('volunteer', help='ibis id of assignee')
        parser.add_argument('name', help='name of the task')
        parser.add_argument('target', type=int, help='target days to finish')
        parser.add_argument('brief', help='description of task')
        parser.add_argument(
            '-s',
            '--start',
            type=int,
            default=0,
            help='number of days to offset start date',
        )
        args = parser.parse_args(sys.argv[2:])

        today = date.today()

        task = OrderedDict()

        task['name'] = args.name
        task['brief'] = args.brief
        task['start'] = str(today + timedelta(args.start))
        task['target'] = str(today + timedelta(args.target))

        task['debrief'] = ''
        task['end'] = ''

        self._data[args.volunteer]['tasks'].append(task)
        index = len(self._data[args.volunteer]['tasks']) - 1

        print('\nCreated Task')
        self._print_task(args.volunteer, index, task)

    def close(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('volunteer', help='id of volunteer')
        parser.add_argument('index', type=int, help='task index')
        parser.add_argument('debrief', help='closing notes for task')
        parser.add_argument(
            '-e',
            '--end',
            help='number of days to offset close date',
        )
        args = parser.parse_args(sys.argv[2:])

        task = self._data[args.volunteer]['tasks'][args.index]

        task['debrief'] = args.debrief
        task['end'] = str(date.today() +
                          timedelta(args.end if args.end else 0))

        print('\nTask Closed')
        self._print_task(args.volunteer, args.index, task)

    def open(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('volunteer', help='id of volunteer')
        parser.add_argument('index', type=int, help='task index')
        args = parser.parse_args(sys.argv[2:])

        task = self._data[args.volunteer]['tasks'][args.index]

        task['debrief'] = ''
        task['end'] = ''

        print('\nTask Opened')
        self._print_task(args.volunteer, args.index, task)

    def edit(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('volunteer', help='id of volunteer')
        parser.add_argument('index', type=int, help='task index')
        parser.add_argument(
            '-r',
            '--reassignment',
            help='new volunteer assignment',
        )
        parser.add_argument(
            '-n',
            '--name',
            help='new task name',
        )
        parser.add_argument(
            '-b',
            '--brief',
            help='new brief description',
        )
        parser.add_argument(
            '-d',
            '--debrief',
            help='new debrief description',
        )
        parser.add_argument(
            '-s',
            '--start',
            type=int,
            help='new start date (from today)',
        )
        parser.add_argument(
            '-t',
            '--target',
            type=int,
            help='new target date (from today)',
        )
        parser.add_argument(
            '-e',
            '--end',
            type=int,
            help='new target date (from today)',
        )
        args = parser.parse_args(sys.argv[2:])

        task = self._data[args.volunteer]['tasks'][args.index]
        today = date.today()

        if args.reassignment:
            self._data[args.volunteer]['tasks'].append(task)
            del self._data[args.volunteer]['tasks'][args.index]
        if args.name:
            task['name'] = args.name
        if args.brief:
            task['brief'] = args.brief
        if args.debrief:
            task['debrief'] = args.debrief
        if args.start:
            task['start'] = str(today + timedelta(args.start))
        if args.target:
            task['target'] = str(today + timedelta(args.target))
        if args.end:
            task['end'] = str(today + timedelta(args.close))

        print('\nEdited Task')
        self._print_task(args.volunteer, args.index, task)

    def delete(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('volunteer', help='id of volunteer')
        parser.add_argument('index', type=int, help='task index')
        args = parser.parse_args(sys.argv[2:])

        task = self._data[args.volunteer]['tasks'][args.index]
        del self._data[args.volunteer]['tasks'][args.index]

        print('\nDeleted Task')
        self._print_task(args.volunteer, args.index, task)

    def _print_task(self, volunteer, index, task):
        print(
            '\n------------------------------------------------------------------------'
        )
        print('Volunteer: {}'.format(
            self._data[volunteer]['info']['nick_name']))
        print('Task #:    {}'.format(index))
        print('Name:      {}'.format(task['name']))
        print('Projected: {} to {}'.format(task['start'], task['target']))
        if task['end']:
            print('Actual:    {} to {}'.format(task['start'], task['end']))

        print('\nBrief:')
        print('{}'.format(textwrap.fill(task['brief'], 70)))

        if task['debrief']:
            print('\nDebrief:')
            print('{}'.format(textwrap.fill(task['debrief'], 70)))

        print(
            '------------------------------------------------------------------------\n'
        )


if __name__ == '__main__':
    Manage()
