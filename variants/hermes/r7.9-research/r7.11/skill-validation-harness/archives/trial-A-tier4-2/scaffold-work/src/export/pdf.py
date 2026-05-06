import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Reference: serialize_pdf
def serialize_pdf(records: list[dict]) -> bytes:
    """
    Serializes a list of dictionaries to a PDF byte string.
    Signature: (records: list[dict]) -> bytes
    """
    if not records:
        return b""

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    y_position = height - 50
    p.drawString(50, y_position, "Exported Records")
    y_position -= 30

    for record in records:
        if y_position < 50:
            p.showPage()
            y_position = height - 50
        
        line = ", ".join([f"{k}: {v}" for k, v in record.items()])
        p.drawString(50, y_position, line)
        y_position -= 20

    p.save()
    return buffer.getvalue()
