#!/usr/bin/python3

import html
import json
import math
import argparse
import drawSvg as draw

from tqdm import tqdm

EPSILON = 1e-4


def _distance(p):
    return math.sqrt(p[0]**2 + p[1]**2)


def _radius(area):
    return math.sqrt(abs(area) / math.pi)


def _propose(radius, circles):
    def _intersections(c1, c2):
        x0, y0, r0 = c1
        x1, y1, r1 = c2

        r0 += radius
        r1 += radius

        d = math.sqrt((x1 - x0)**2 + (y1 - y0)**2)

        # no overlap
        if d > r0 + r1:
            return []

        # a contains b
        if d < abs(r0 - r1):
            return []

        # a is b
        if d == 0 and r0 == r1:
            return []

        else:
            a = (r0**2 - r1**2 + d**2) / (2 * d)
            h = math.sqrt(r0**2 - a**2 + EPSILON)
            x2 = x0 + a * (x1 - x0) / d
            y2 = y0 + a * (y1 - y0) / d
            x3 = x2 + h * (y1 - y0) / d
            y3 = y2 - h * (x1 - x0) / d

            x4 = x2 - h * (y1 - y0) / d
            y4 = y2 + h * (x1 - x0) / d

            if abs(_distance((x3, y3)) - _distance((x4, y4))) < EPSILON:
                return [(x3, y3), (x4, y4)]

            return [max(
                [(x3, y3), (x4, y4)],
                key=lambda p: _distance(p),
            )]

    return [
        p for i, c1 in enumerate(circles) for c2 in circles[i:]
        for p in _intersections(c1, c2)
    ]


def _filter(radius, circles, positions):
    def _valid(c1, c2):
        x0, y0, r0 = c1
        x1, y1, r1 = c2

        d = math.sqrt((x1 - x0)**2 + (y1 - y0)**2) + EPSILON

        # collides
        if d < r0 + r1:
            return False

        return True

    result = []
    for p in positions:
        is_valid = True
        for c in reversed(circles):
            if not _valid((p[0], p[1], radius), c):
                is_valid = False
                break
        if is_valid:
            result.append(p)

    return result


def _choose_funder(radius, positions):
    return list(min(
        positions,
        key=lambda p: _distance(p),
    )) + [radius]


def _choose_user(radius, positions, funder):
    return list(
        min(
            positions,
            key=
            lambda p: math.sqrt((p[0] - funder[0])**2 + (p[1] - funder[1])**2),
        )) + [radius]


def calculate(data):
    assert len(data) >= 2

    circles = [
        [0, 0, _radius(data[0][1])],
        [0, _radius(data[0][1]) + _radius(data[1][1]),
         _radius(data[1][1])],
    ]

    last_funder = circles[0]

    for d in tqdm(data[2:]):
        positions = _propose(_radius(d[1]), circles)
        valid = _filter(_radius(d[1]), circles, positions)
        if d[1] > 0:
            circle = _choose_funder(_radius(d[1]), valid)
            last_funder = circle
        else:
            circle = _choose_user(_radius(d[1]), valid, last_funder)
        circles.append(circle)

    return circles


def render(circles, data, size, highlight=[], output='circles.svg'):
    d = draw.Drawing(size, size, origin='center')
    d.append(draw.Rectangle(
        -size / 2,
        -size / 2,
        size,
        size,
        fill='white',
    ))

    for i, item in enumerate(zip(circles, data)):
        circle = item[0]

        if item[1][1] > 0:
            color = '#3b3b3b'
        else:
            if item[1][0] and item[1][0] in highlight:
                color = '#ffff00'
            else:
                color = '#84ab3f'

        d.append(
            draw.Circle(
                *circle,
                fill=color,
                amount=item[1][1],
                person=item[1][0],
                target=item[1][2] if len(item[1]) >= 4 else '',
                description=html.escape(item[1][3]) if len(item[1]) >= 4 else '',
            ))

    d.saveSvg(output)


def run(funders, users, highlight=[], output='circles.svg'):

    data = []
    balance = 0
    index = 0

    for name, amount in funders:
        data.append((name, amount))
        balance += amount

        while index < len(users) and users[index][1] <= balance:
            balance -= users[index][1]
            data.append((
                users[index][0],
                -users[index][1],
                users[index][2],
                users[index][3],
            ))
            index += 1

        if index == len(users):
            break

    data = [x for x in data if x[1] >= 1 or x[1] <= -1]

    try:
        with open('circles.json') as fd:
            circles = json.load(fd)
    except Exception:
        circles = calculate(data)
        with open('circles.json', 'w') as fd:
            json.dump(circles, fd, indent=2)

    size = 2 * max(_distance(c) + c[2] for c in circles)
    render(circles, data, size, highlight, output)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description=
        """Tool for rendering names and values into a deterministically packed structure of circles """,
    )

    parser.add_argument(
        'funders',
        help='Path to JSON list of n pairs of [donor_name, total_donations]',
    )

    parser.add_argument(
        'users',
        help='Path to JSON list of n pairs of [user_name, total_donations]',
    )

    parser.add_argument(
        '-l',
        '--highlight',
        help='labels to highlight',
        action='append',
        default=[],
    )

    parser.add_argument(
        '-o',
        '--output',
        help='output file',
        action='append',
        default='circles.svg',
    )

    args = parser.parse_args()

    with open(args.funders) as fd:
        funders = json.load(fd)

    with open(args.users) as fd:
        users = json.load(fd)

    run(funders, users, args.highlight, args.output)
