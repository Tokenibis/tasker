#!/usr/bin/python3

import json
import math
import argparse
import drawSvg as draw

TIERS = [
    'Frogmouth',
    'Hoatzin',
    'Kakapo',
    'Kagu',
    'Firgatebird',
    'Tragopan',
    'Secretarybird',
    'Widowbird',
    'Owlet-Nightjar',
    'Coucal',
    'Guineafowl',
    'Iider',
    'Pheasant',
    'Cock-of-the-Rock',
    'Potoo',
    'Kiwi',
    'Cassowary',
    'Astrapia',
    'Kea',
    'Umbrellabird',
    'Bustard',
]


def create_labels(data):
    labels = []

    for name, value in data:
        assert type(value) == int and value >= 0

        while value:
            level = int(math.log(value, 4))

            while len(labels) <= level:
                labels.append([])

            while value >= 4**level:
                labels[level].append(name)
                value -= 4**level

    return labels


def create_fractals(labels, max_level):
    def create_fractal(h, x, y):
        triangles = [[(
            x - h,  # 0 (x0)
            y + h,  # 1 (y1)
            x,  # 2 (x1)
            y + h * 2,  # 3 (y1)
            x + h,  # 4 (x2)
            y + h,  # 5 (y2)
        )]]

        if h <= 1:
            return triangles

        bottom = create_fractal(h / 2, x, y)
        left = create_fractal(h / 2, x - h, y + h)
        right = create_fractal(h / 2, x + h, y + h)

        for i in range(len(bottom) - 1, -1, -1):
            triangles = [bottom[i] + (left[i] + right[i])] + triangles

        return triangles

    # calculate the size of sierpinski gaskets that we need
    if not max_level:
        max_height = 0
        for level, names in enumerate(labels):
            if len(names):
                height = int(2**math.ceil(
                    math.log(math.ceil(len(names) / 4), 3)) * 2**level)
                max_height = height if height > max_height else max_height
    else:
        max_height = 2**(max_level - 1)

    fractals = [create_fractal(max_height, 0, 0) for _ in range(4)]

    # deep copy of fractal triangles with extra meta field(s)
    labeled_fractals = [[[[z, ''] for z in y] for y in x] for x in fractals]
    for level, names in enumerate(labels[:len(labeled_fractals[0])]):
        for i, name in enumerate(names[:4 * len(labeled_fractals[0][level])]):
            quadrant = i % 4
            labeled_fractals[quadrant][level][int(i / 4)][1] = name

    return labeled_fractals


def create_figure(
        fractals,
        output,
        blank,
        rotation,
        padding,
        gap,
        unlabeled_text=lambda l, ml: '',
        pos_color=lambda l, ml: '#000000',
        neg_color=lambda l, ml: '#ffffff',
        back_color=lambda ml: '#ffffff',
        text_color=lambda ml: '#000000',
        neg_text=lambda ml: '#000000',
):
    g = gap / 2
    ml = len(fractals[0])

    size = 2**(ml + 1) + g * 2 + padding
    d = draw.Drawing(size, size, origin='center')
    d.append(
        draw.Rectangle(
            -size / 2,
            -size / 2,
            size,
            size,
            fill=back_color(ml),
        ))
    triangles = [y[0] for x in fractals[0] for y in x]

    for quadrant, fractal in enumerate(fractals):
        q = (quadrant + rotation) % 4
        for l, triangles in enumerate(fractal):
            for p, label in triangles:
                d.append(
                    draw.Lines(
                        ((p[1] + g) if q % 2 else p[0]) * (-1)**(q in [2, 3]),
                        (p[0] if q % 2 else (p[1] + g)) * (-1)**(q in [1, 2]),
                        ((p[3] + g) if q % 2 else p[2]) * (-1)**(q in [2, 3]),
                        (p[2] if q % 2 else (p[3] + g)) * (-1)**(q in [1, 2]),
                        ((p[5] + g) if q % 2 else p[4]) * (-1)**(q in [2, 3]),
                        (p[4] if q % 2 else (p[5] + g)) * (-1)**(q in [1, 2]),
                        fill=pos_color(l, ml) if label else neg_color(l, ml),
                    ))

                if not blank:
                    d.append(
                        draw.Text(
                            label.upper() if label else unlabeled_text(l, ml),
                            (2**l) / 8,
                            (p[0] + p[4]) / 2 - (p[4] - p[0]) * 3 / 8,
                            (p[1] + p[5]) / 2 + g + (2**l) / 32,
                            fill=text_color(ml),
                            transform='rotate({})'.format(q * 90),
                        ))

    d.setPixelScale(8)  # Set number of pixels per geometry unit
    d.saveSvg(output)


def render(data, output, levels, **kwargs):
    """Render the fractal

    Parameters:
    data (list): ordered [name, value] pairs

    """

    labels = create_labels(data)
    fractals = create_fractals(labels, levels)
    create_figure(
        fractals,
        output,
        unlabeled_text=lambda l, ml: '{:,} {}'.format(4**l, TIERS[l].upper()),
        pos_color=lambda l, ml: '#{:02x}{:02x}{:02x}'.format(
            220 - int(88 * l/ml),
            230 - int(59 * l/ml),
            220 - int(157 * l/ml),
        ),
        neg_color=lambda l, ml: '#{0:02x}{0:02x}{0:02x}'.format(
            250 - int(32 * l/ml),
        ),
        back_color=lambda ml: '#{0:02x}{0:02x}{0:02x}'.format(255),
        # neg_color=lambda l, ml: '#{0:02x}{0:02x}{0:02x}'.format(
        #     16 + int(32 * l/ml),
        # ),
        # back_color=lambda ml: '#{0:02x}{0:02x}{0:02x}'.format(16),
        text_color=lambda ml: '#ffffff',
        **kwargs,
    )


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="""Tool for rendering names and values into a partial
        Sierpinski triangle fractal.
        """, )

    parser.add_argument(
        'path',
        help='Path to JSON list of n pairs of [donor_name, total_donations]',
    )

    parser.add_argument(
        '-o',
        '--output',
        help='Path to output svg file',
        default='fractal.svg',
    )

    parser.add_argument(
        '-l',
        '--levels',
        help='If non-zero, specifies the specific number of levels to draw',
        type=int,
        default=0,
    )

    parser.add_argument(
        '-b',
        '--blank',
        help='Do not display labels',
        action='store_true',
    )

    parser.add_argument(
        '-g',
        '--gap',
        help='Size of gap between quadrants',
        type=int,
        default=0,
    )

    parser.add_argument(
        '-p',
        '--padding',
        help='Size of padding',
        type=int,
        default=0,
    )

    parser.add_argument(
        '-r',
        '--rotation',
        help='Number of quadrants to rotate (modulo 4)',
        type=int,
        default=0,
    )

    args = parser.parse_args()

    with open(args.path) as fd:
        data = json.load(fd)

    render(
        data[:200],
        args.output,
        levels=args.levels,
        blank=args.blank,
        rotation=args.rotation,
        gap=args.gap,
        padding=args.padding,
    )
