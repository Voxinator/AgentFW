from typing import List, Dict
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io

def serialize_pdf(records: List[Dict]) -> bytes:
    """
    Serializes a list of dictionaries into a PDF byte stream.
    """
    if not records:
        return b""

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph("Exported Data", styles['Title']))
    elements.append(Paragraph("<br/><br/>", styles['Normal']))

    # Prepare table data
    fieldnames = list(records[0].keys())
    data = [fieldnames]  # Header row
    
    for record in records:
        row = [str(record.get(field, "")) for field in fieldnames]
        data.append(row)

    # Create table
    table = Table(data)
    
    # Style the table
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])
    table.setStyle(style)
    elements.append(table)

    # Build PDF
    doc.build(elements)
    return buffer.getvalue()
