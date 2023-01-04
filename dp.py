#!/usr/bin/env python

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Iterator, Tuple, List

CONF_DIR = os.path.expanduser("~/.config/dp")
P_CONF = re.compile(r'"([^"]+)"', re.IGNORECASE)
P_ATTR = re.compile(r'":"', re.IGNORECASE)


@dataclass
class Config:
    """
    Config for a single display
    """
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
    """
    Layout is a group of configs
    """
    configs: List[Config]
    name: str = None

    @staticmethod
    def parse(value, name=None):
        configs = [Config.parse(m.group(1))
                for line in value.split('\n')
                if line.startswith("displayplacer")
                for m in P_CONF.finditer(line)]
        return Layout(configs, name)

    @property
    def footprint(self):
        return [(c.id_, c.origin) for c in sorted(self.configs, key=lambda x: hash(x.id_))]

    def to_command(self):
        return "displayplacer " + ' '.join([f"\"{c.to_conf()}\"" for c in self.configs])

    def run(self):
        subprocess.run(self.to_command(), shell=True, check=True)

    def switch(self, template_items):
        if self.footprint == template_items[0].footprint:
            print("switch to 1", file=sys.stderr)
            self.configs = template_items[1].configs
        else:
            print("switch to 0", file=sys.stderr)
            self.configs = template_items[0].configs


class Template:
    def __init__(self, template_file) -> None:
        self._template_path = Path(template_file).expanduser()
        
    def save(self, layout: Layout):
        self._template_path.parent.mkdir(parents=True, exist_ok=True)
        with self._template_path.open('a') as f:
            f.write(layout.to_command())
            f.write("\n")

    def load(self):
        return [Layout.parse(raw, name) for name, raw in self.load_raw()]

    def load_raw(self):
        if self._template_path.exists():
            with self._template_path.open() as f:
                for i, l in enumerate(f.readlines()):
                    if "|" in l:
                        name, l = l.split('|', 2)
                    else:
                        name = f"Layout {i}"
                    yield name.strip(), l.strip()


def alfred_script_filter(template: Template):
    alfred_json = {
        "items": [
            {
                "title": "Auto Switch",
                "subtitle": "Auto switch based on the current config",
                "arg": "!",
                "autocomplete": "auto"
            }
        ] + [
            {
                "title": name,
                "subtitle": raw,
                "arg": raw,
                "autocomplete": name
            }
            for name, raw in template.load_raw()
        ]
    }

    print(json.dumps(alfred_json))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', "--save", action='store_true')
    parser.add_argument('-p', "--print-only", action='store_true')
    parser.add_argument("--alfred", action='store_true', help="run as alfred script filter")
    parser.add_argument('template_file', nargs='?', type=str, default=f"{CONF_DIR}/templates.txt")
    return parser.parse_args()


def main():
    args = parse_args()
    result = subprocess.run(['displayplacer', 'list'], capture_output=True, text=True)
    layout = Layout.parse(result.stdout)

    template = Template(args.template_file)
    if args.alfred:
        alfred_script_filter(template)
    elif args.save:
        template.save(layout)
    else:
        template_items = template.load()
        layout.switch(template_items)
        print(layout.to_command())
        if not args.print_only:
            layout.run()


if __name__ == "__main__":
    main()
