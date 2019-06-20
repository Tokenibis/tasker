#!/usr/bin/python3

import json
import textwrap
import argparse

import numpy as np
import matplotlib.pyplot as plt

from collections import OrderedDict
from datetime import datetime, date

WINDOW = 60
PROPORTION = 0.60


def run(offset, window):

    with open('record.json') as fd:
        data = json.load(fd, object_pairs_hook=OrderedDict)

    # Fixing random state for reproducibility
    np.random.seed(0)

    plt.rcdefaults()
    fig, ax = plt.subplots()

    # team member names
    team = [data[x]['info']['nick_name'] for x in data]
    y_pos = np.arange(len(team))

    # create 2-D array of tasks
    tasks = [data[x]['tasks'] for x in data]
    max_len = max([len(t) for t in tasks])
    min_date = min(
        [data[x]['tasks'][0]['start'] for x in data if data[x]['tasks']])
    null_task = {
        'name': '',
        'start': min_date,
        'end': min_date,
        'target': min_date
    }
    tasks = [t + [null_task] * (max_len - len(t)) for t in tasks]
    layers = list(map(list, zip(*tasks)))

    bars = []

    for layer in layers:
        start = [
            datetime.strptime(x['start'], '%Y-%m-%d').date() for x in layer
        ]
        target = [
            datetime.strptime(x['target'], '%Y-%m-%d').date() for x in layer
        ]
        end = [
            datetime.strptime(x['end'], '%Y-%m-%d').date()
            if x['end'] else datetime.strptime(x['start'], '%Y-%m-%d').date()
            for x in layer
        ]

        left = [(x - date.today()).days for x in start]
        target_width = [(x[1] - x[0]).days for x in zip(start, target)]
        actual_width = [(x[1] - x[0]).days for x in zip(start, end)]

        bars.append(
            ax.barh(
                y_pos,
                target_width,
                left=left,
                edgecolor='white',
                linewidth=2,
                color='#85aa00',
                height=0.6,
            ))
        ax.barh(
            y_pos,
            actual_width,
            left=left,
            edgecolor='white',
            linewidth=2,
            color='#3b3b3b',
            height=0.3,
        )
        for i, task in enumerate(layer):
            ax.text(
                left[i] + 1,
                i + 0.05,
                task['name'],
                color='white',
                size=8,
                fontweight='bold',
            )

    annot = ax.annotate(
        '',
        xy=(0, 0),
        xytext=(-20, 20),
        textcoords='offset points',
        color='#9b9b9b',
        bbox=dict(fc='white', ec='#9b9b9b'))

    annot.set_visible(False)

    def make_text(task):
        text = task['name']
        text += '\n\n' + textwrap.fill('Brief: ' + task['brief'])
        if task['debrief']:
            text += '\n\n' + textwrap.fill('Debrief: ' + task['debrief'])
        return text

    def update_annot(bar, i, j):
        x = bar.get_x() + 1
        y = bar.get_y()
        annot.xy = (x, y)
        text = make_text(layers[i][j])
        annot.set_text(text)
        annot.get_bbox_patch().set_alpha(1)

    def select(event):
        vis = annot.get_visible()
        if event.inaxes == ax:
            for i, layer in enumerate(bars):
                for j, bar in enumerate(layer):
                    cont, ind = bar.contains(event)
                    if cont:
                        update_annot(bar, i, j)
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                        return
        if vis:
            annot.set_visible(False)
            fig.canvas.draw_idle()

    ax.set_yticks(y_pos)
    ax.set_yticklabels(team)
    ax.invert_yaxis()  # labels read top-to-bottom
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.set_xlim(
        [offset - PROPORTION * window, offset + (1 - PROPORTION) * window])

    fig.canvas.mpl_connect('button_press_event', select)

    plt.axvline(
        x=0, linewidth=1, linestyle='dashed', color='#3b3b3b', zorder=-1)
    plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-o',
        '--offset',
        type=int,
        default=0,
        help='Number of days (from today) to offset the display',
    )
    parser.add_argument(
        '-w',
        '--window',
        type=int,
        default=WINDOW,
        help='Total number of days to display',
    )
    args = parser.parse_args()

    run(args.offset, args.window)
