"""PDF export. Implementation using reportlab."""
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import io

def serialize_pdf(data: list[dict]) -> bytes:
    """
    Serializes a list of dictionaries into a PDF byte stream.
    
    Args:
        data: A list of dictionaries representing the rows.
        
    Returns:
        A PDF formatted bytes object.
    """
    if not data:
        return b""

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph("Exported Data", styles['Title']))
    elements.append(Paragraph("<br/><br/>", styles['Normal']))

    # Prepare Table Data
    # Header
    headers = list(data[0].keys())
    table_data = [headers]

    # Rows
    for row in data:
        table_data.append([str(row.get(h, "")) for h in headers])

    # Create Table
    t = Table(table_data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#CCCCCC'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), '#FFFFFF'),
        ('GRID', (0, 0), (-1, -1), 1, '#000000'),
    ]))
    
    elements.append(t)
    doc.build(elements)
    
    return buffer.getvalue()
