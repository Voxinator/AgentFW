import sys
import importlib.util
import os
import sysconfig

def _get_real_json():
    # Try to find the real json module in sys.modules
    for name, mod in sys.modules.items():
        if name == 'json' and hasattr(mod, 'dumps'):
            return mod
    
    # If not found, try to load it from the stdlib path
    std_lib_path = sysconfig.get_path('stdlib')
    # json is a package, so we look for __init__.py
    real_json_path = os.path.join(std_lib_path, 'json', '__init__.py')
    
    if os.path.exists(real_json_path):
        # To load a package correctly, we need to set the name and package
        spec = importlib.util.spec_from_file_location("json", real_json_path)
        if spec and spec.loader:
            real_json = importlib.util.module_from_spec(spec)
            # We must add it to sys.modules so that relative imports within the package work
            sys.modules["json"] = real_json
            spec.loader.exec_module(real_json)
            return real_json
    
    raise ImportError("Could not find the real 'json' standard library module.")

def export_to_json(records: list[dict]) -> str:
    """Alias for serialize_to_json."""
    return serialize_to_json(records)

def serialize_to_json(records: list[dict]) -> str:
    """
    Serializes a list of dictionaries to a JSON string.
    """
    if not records:
        return "[]"

    real_json = _get_real_json()
    return real_json.dumps(records)

if __name__ == "__main__":
    data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
    print("JSON Output:")
    print(serialize_to_json(data))
    print("Empty JSON Output:")
    print(serialize_to_json([]))
