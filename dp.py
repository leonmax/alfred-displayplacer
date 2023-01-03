#!/usr/bin/env python

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Tuple, List

CONF_DIR = os.path.expanduser("~/.config/dp")
P_CONF = re.compile(r'"([^"]+)"', re.IGNORECASE)
P_ATTR = re.compile(r'":"', re.IGNORECASE)


@dataclass
class Config:
    id_: str
    res: Tuple[int, int]
    origin: Tuple[int, int] = (0,0)
    hz: int = -1
    color_depth: int = -1
    scaling: bool = False
    degree: int = 0

    def to_conf(self):
        result = f"id:{self.id_}"
        result += f" degree:{self.degree}"
        result += f" res:{self.res}"

        result += f" hz:{self.hz}" if self.hz != -1 else ""
        result += f" scaling:{'on' if self.scaling else 'off'}"
        result += f" origin:{self.origin}"
        return result

    @staticmethod
    def parse(value):
        kv = dict(attr.split(':', 1) for attr in value.split(' '))
        kv['id_'] = kv.pop('id')
        return Config(**kv)


@dataclass
class Layout:
    configs: List[Config]

    @staticmethod
    def parse(value):
        configs = [Config.parse(m.group(1))
                for line in value.split('\n')
                if line.startswith("displayplacer")
                for m in P_CONF.finditer(line)]
        return Layout(configs)

    @property
    def footprint(self):
        return [(c.id_, c.origin) for c in sorted(self.configs, key=lambda x: hash(x.id_))]

    def to_command(self):
        return "displayplacer " + ' '.join([f"\"{c.to_conf()}\"" for c in self.configs])

    def run(self):
        subprocess.run(self.to_command(), shell=True, check=True)

    def switch(self, templates):
        if self.footprint == templates[0].footprint:
            print("switch to 1", file=sys.stderr)
            self.configs = templates[1].configs
        else:
            print("switch to 0", file=sys.stderr)
            self.configs = templates[0].configs


def save_templates(template_path: Path, layout: Layout):
    template_path.parent.mkdir(parents=True, exist_ok=True)
    with template_path.open('a') as f:
        f.write(layout.to_command())
        f.write("\n")


def load_templates(template_path: Path):
    with template_path.open() as f:
        return [Layout.parse(l)
                for l in f.readlines()
                if l.strip()]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', "--save", action='store_true')
    parser.add_argument('-p', "--print-only", action='store_true')
    parser.add_argument('template_file', nargs='?', type=str, default=f"{CONF_DIR}/templates.txt")
    return parser.parse_args()


def main():
    args = parse_args()
    result = subprocess.run(['displayplacer', 'list'], capture_output=True, text=True)
    layout = Layout.parse(result.stdout)

    template_path = Path(args.template_file).expanduser()
    if args.save:
        save_templates(template_path, layout)
    else:
        templates = load_templates(template_path)
        layout.switch(templates)
        print(layout.to_command())
        if not args.print_only:
            layout.run()


if __name__ == "__main__":
    main()

