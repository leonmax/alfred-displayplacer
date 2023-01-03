import json
from pathlib import Path
import sys
from typing import List


def load_templates(template_file: Path):
    template_path = Path(template_file).expanduser()
    template_path.parent.mkdir(parents=True, exist_ok=True)
    template_path.touch()
    with template_path.open() as f:
        return [l
                for l in f.readlines()
                if l.strip()]


def to_alfred_list(configs: List[str]):
    items = [
      {
        "title": f"Auto Switch",
        "subtitle": "Auto switch based on the current config",
        "arg": "!"
      }
    ]
    
    items += [
      {
        "title": f"Config {i}",
        "subtitle": configs[i],
        "arg": configs[i],
        "autocomplete": i
      }
      for i in range(len(configs))
    ]

    return {
            "items": items
    }



configs = load_templates(sys.argv[1])
print(
  json.dumps(
    to_alfred_list(configs)
  )
)
