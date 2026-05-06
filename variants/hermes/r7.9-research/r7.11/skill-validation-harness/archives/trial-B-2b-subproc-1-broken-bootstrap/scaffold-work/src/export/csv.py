import io
import sys
import importlib.util
import os
import sysconfig

def _get_real_csv():
    # Try to find the real csv module in sys.modules
    for name, mod in sys.modules.items():
        if name == 'csv' and hasattr(mod, 'DictWriter'):
            return mod
    
    # If not found, try to load it from the stdlib path
    std_lib_path = sysconfig.get_path('stdlib')
    real_csv_path = os.path.join(std_lib_path, 'csv.py')
    
    if os.path.exists(real_csv_path):
        spec = importlib.util.spec_from_file_location("real_csv", real_csv_path)
        if spec and spec.loader:
            real_csv = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(real_csv)
            return real_csv
    
    # Last resort: it might be a built-in module in some python distributions
    # but csv is usually a file.
    raise ImportError("Could not find the real 'csv' standard library module.")

def export_to_csv(records: list[dict]) -> str:
    """Alias for serialize_to_csv."""
    return serialize_to_csv(records)

def serialize_to_csv(records: list[dict]) -> str:

    if not records:
        return ""

    output = io.StringIO()
    fieldnames = records[0].keys()
    
    real_csv = _get_real_csv()
    writer = real_csv.DictWriter(output, fieldnames=fieldnames)

    writer.writeheader()
    writer.writerows(records)

    return output.getvalue()

if __name__ == "__main__":
    data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
    print("CSV Output:")
    print(serialize_to_csv(data))
    print("Empty CSV Output:")
    print(f"'{serialize_to_csv([])}'")
