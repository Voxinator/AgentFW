from src.export.formats import serialize_csv, serialize_json, serialize_pdf

def smoke_test():
    print("Running smoke test for serializers...")
    
    # Test CSV
    try:
        serialize_csv([])
        print("serialize_csv: OK")
    except Exception as e:
        print(f"serialize_csv: FAILED with {e}")

    # Test JSON
    try:
        serialize_json([])
        print("serialize_json: OK")
    except Exception as e:
        print(f"serialize_json: FAILED with {e}")

    # Test PDF
    try:
        serialize_pdf([])
        print("serialize_pdf: OK")
    except Exception as e:
        print(f"serialize_pdf: FAILED with {e}")

if __name__ == "__main__":
    smoke_test()
