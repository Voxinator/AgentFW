from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

def export_to_pdf(records: list[dict]) -> bytes:
    """Alias for serialize_to_pdf."""
    return serialize_to_pdf(records)

def serialize_to_pdf(records: list[dict]) -> bytes:
    """
    Serializes a list of dictionaries to a PDF byte stream using reportlab.
    
    Args:
        records: A list of dictionaries representing the data.
        
    Returns:
        PDF file content as bytes. Returns empty bytes if records is empty.
    """
    if not records:
        return b""

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    y_position = height - 40
    c.setFont("Helvetica", 12)

    for record in records:
        if y_position < 40:
            c.showPage()
            y_position = height - 40
            c.setFont("Helvetica", 12)
            
        line = ", ".join(f"{k}: {v}" for k, v in record.items())
        c.drawString(40, y_position, line)
        y_position -= 20

    c.save()
    return buffer.getvalue()

if __name__ == "__main__":
    data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
    print("PDF Output (bytes length):")
    print(len(serialize_to_pdf(data)))
    print("Empty PDF Output (bytes length):")
    print(len(serialize_to_pdf([])))
