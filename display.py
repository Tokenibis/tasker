#!/usr/bin/python3

import json
import argparse

import numpy as np
import matplotlib.pyplot as plt, mpld3

from collections import OrderedDict
from datetime import datetime, date

WINDOW = 60
PROPORTION = 0.60


def run(offset, window):

    with open('record.json') as fd:
        data = json.load(fd, object_pairs_hook=OrderedDict)

    data = OrderedDict(reversed(list(data.items())))

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
        'brief': '',
        'debrief': '',
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

        ax.barh(
            y_pos,
            target_width,
            left=left,
            edgecolor='white',
            linewidth=2,
            color='#85aa00',
            height=0.6,
        )
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
        # transparent bar for hovering
        bars.append(
            ax.barh(
                y_pos,
                target_width,
                left=left,
                linewidth=2,
                height=0.6,
                zorder=1000,
                alpha=0.0,
            ))

    ax.set_yticks(y_pos)
    ax.set_yticklabels(team)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.set_xlim(
        [offset - PROPORTION * window, offset + (1 - PROPORTION) * window])

    def make_text(task):
        text = """
        <div style="background-color:#ffffff; padding:10px; border-style:solid; border-width:1px; border-color:#3b3b3b">
        <h6 style="font-size:10; color:#9b9b9b">{}</h6>
        <p style="font-size:10; color:#9b9b9b"><strong>Brief:</strong> {}</p>
        <div>
        """.format(task['name'], task['brief'])
        # if task['debrief']:
        #     text += '\n\n' + textwrap.fill('Debrief: ' + task['debrief'])
        return text

    for i, layer in enumerate(bars):
        for j, bar in enumerate(layer):
            tooltip = mpld3.plugins.PointHTMLTooltip(
                bar,
                [make_text(layers[i][j])],
                voffset=10,
                hoffset=10,
            )
            mpld3.plugins.connect(fig, tooltip)

    plt.axvline(
        x=-10,
        linewidth=1,
        linestyle='dashed',
        color='#3b3b3b',
        zorder=-1,
    )

    mpld3.show()


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
