from src.export import serialize_csv, serialize_json, serialize_pdf

if __name__ == "__main__":
    data = [{"id": 1, "name": "test"}]
    serialize_csv(data)
    serialize_json(data)
    serialize_pdf(data)
