import csv
import io

def serialize_csv(records: list[dict]) -> str:
    """
    Serializes a list of dictionaries into a CSV string.
    
    Args:
        records: A list of dictionaries representing the rows.
        
    Returns:
        A CSV formatted string. Returns an empty string if records is empty.
    """
    if not records:
        return ""
    
    output = io.StringIO()
    # Use the keys from the first dictionary as fieldnames
    fieldnames = records[0].keys()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    
    writer.writeheader()
    writer.writerows(records)
    
    return output.getvalue()

def serialize_csv_with_custom_delimiter(records: list[dict], delimiter: str = ',') -> str:
    """
    Serializes a list of dictionaries into a CSV string with a custom delimiter.
    
    Args:
        records: A list of dictionaries representing the rows.
        delimiter: The character used to separate fields.
        
    Returns:
        A CSV formatted string. Returns an empty string if records is empty.
    """
    if not records:
        return ""
    
    output = io.StringIO()
    fieldnames = records[0].keys()
    writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=delimiter)
    
    writer.writeheader()
    writer.writerows(records)
    
    return output.getvalue()

if __name__ == "__main__":
    # Test cases
    test_data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
    print("CSV Output:")
    print(serialize_csv(test_data))
    
    print("TSV Output:")
    print(serialize_csv_with_custom_delimiter(test_data, delimiter='\t'))
    
    print("Empty Output:")
    print(f"'{serialize_csv([])}'")
