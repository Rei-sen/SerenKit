import json

from pathlib   import Path

from ..tagfile import Definition


_FOLDER   = Path(__file__).parent
_DEF_FILE = "definitions.json"

def get_definitions() -> dict[str, dict]:
    if not (_FOLDER / _DEF_FILE).is_file():
        return {}
    
    with open(_FOLDER / _DEF_FILE, 'r') as file:
        return json.load(file)
    
def add_definitions(definitions: list[Definition]) -> None: 
    existing = get_definitions()
    for defn in definitions:
        if defn is None:
            continue
        
        if defn.name not in existing:
            existing[defn.name] = {defn.version: defn.to_dict()}
        
        elif str(defn.version) not in existing[defn.name]:
            existing[defn.name][str(defn.version)] = defn.to_dict()

    with open(_FOLDER / _DEF_FILE, 'w') as file:
        file.write(json.dumps(existing, indent=4))

