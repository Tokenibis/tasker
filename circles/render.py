#!/usr/bin/python3

import html
import json
import math
import bisect
import argparse
import drawSvg as draw

from tqdm import tqdm

EPSILON = 1e-4


def _distance(p1, p2=(0, 0)):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


def _radius(area):
    return math.sqrt(abs(area) / math.pi)


class Grid:
    """Stores circles in a grid and return all circles that are relevant
    to a specific point

    """

    SIZE = 8

    def __init__(self, circles=[]):
        self.grid = [[[] for _ in range(4)] for _ in range(4)]

        self.circles = []

        for c in circles:
            self.add_circle(c)

    def add_circle(self, circle):
        while math.ceil((max(abs(circle[0]), abs(circle[1])) + circle[2]) /
                        Grid.SIZE) >= int(len(self.grid) / 2):
            self.grid = [
                [[] for _ in range(len(self.grid[0]) * 2)]
                for _ in range(int(len(self.grid) / 2))
            ] + [[[] for _ in range(int(len(self.grid[0]) / 2))] + self.grid[j]
                 + [[] for _ in range(int(len(self.grid[0]) / 2))]
                 for j in range(int(len(self.grid)))
                 ] + [[[] for _ in range(len(self.grid) * 2)]
                      for _ in range(int(len(self.grid) / 2))]

        for j, i in self._get_squares(circle):
            self.grid[j][i].append(circle)
        self.circles.append(circle)

    def get_circles(self, circle):
        seen = set()
        for j, i in self._get_squares(circle):
            if j < len(self.grid) and i < len(self.grid[0]):
                for c in self.grid[j][i]:
                    if c in seen:
                        continue
                    seen.add((j, i))
                    yield c

    def _get_squares(self, circle):
        for j in range(
                int(
                    math.floor((circle[0] - circle[2]) / Grid.SIZE) +
                    len(self.grid) / 2),
                int(
                    math.ceil((circle[0] + circle[2]) / Grid.SIZE) +
                    len(self.grid) / 2),
        ):
            for i in range(
                    int(
                        math.floor((circle[1] - circle[2]) / Grid.SIZE) +
                        len(self.grid[0]) / 2),
                    int(
                        math.ceil((circle[1] + circle[2]) / Grid.SIZE) +
                        len(self.grid[0]) / 2),
            ):
                if _distance(circle, (
                        (j - len(self.grid) / 2) * Grid.SIZE,
                        (i - len(self.grid[0]) / 2) * Grid.SIZE,
                )) <= circle[2] + (Grid.SIZE * 2):
                    yield (j, i)


class Proximities:
    """Stores distances between circles (edge to edge) and returns pairs
    that are less than a given distance

    """

    def __init__(self, circles=[]):
        self.circles = {}
        self.proximities = []

        for c in circles:
            self.add_circle(c)

    def add_circle(self, c2):
        for c1 in self.circles:
            bisect.insort(
                self.proximities,
                (max(0,
                     _distance(c1, c2) - c1[2] - c2[2]), c1, c2),
            )
        self.circles[c2] = len(self.circles)

    def get_circles(self, distance):
        return sorted(
            [
                x[1:] for x in self.proximities[:bisect.bisect_right(
                    self.proximities,
                    (distance + EPSILON, None, None),
                )]
            ],
            key=lambda x: (self.circles[x[0]], self.circles[x[1]]),
        )


def _propose(radius, proximities):
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
        p for c1, c2 in proximities.get_circles(radius * 2)
        for p in _intersections(c1, c2)
    ]


def _filter(radius, grid, positions):
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
        candidate = (p[0], p[1], radius)

        for c in grid.get_circles(candidate):
            if not _valid(candidate, c):
                is_valid = False
                break
        if is_valid:
            result.append(p)

    return result


def _choose_funder(radius, positions):
    return tuple(
        list(min(
            positions,
            key=lambda p: _distance(p),
        )) + [radius])


def _choose_user(radius, positions, funder):
    return tuple(
        list(
            min(
                positions,
                key=
                lambda p: math.sqrt((p[0] - funder[0])**2 + (p[1] - funder[1])**2),
            )) + [radius])


def calculate(data):
    assert len(data) >= 2

    circles = [
        (0, 0, _radius(data[0][1])),
        (0, _radius(data[0][1]) + _radius(data[1][1]), _radius(data[1][1])),
    ]

    proximities = Proximities(circles)
    grid = Grid(circles)

    last_funder = circles[0]

    for d in tqdm(data[2:]):
        positions = _propose(_radius(d[1]), proximities)
        valid = _filter(_radius(d[1]), grid, positions)
        if d[1] > 0:
            circle = _choose_funder(_radius(d[1]), valid)
            last_funder = circle
        else:
            circle = _choose_user(_radius(d[1]), valid, last_funder)
        circles.append(circle)
        proximities.add_circle(circle)
        grid.add_circle(circle)

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
                person=html.escape(item[1][0]),
                target=html.escape(item[1][2]) if len(item[1]) >= 4 else '',
                description=html.escape(item[1][3])
                if len(item[1]) >= 4 else '',
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
