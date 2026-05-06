import io
from typing import List, Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def serialize_pdf(records: List[Dict[str, Any]]) -> bytes:
    """
    Serializes a list of dictionaries to a PDF byte stream.
    Generates a simple table of the records.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    if not records:
        elements.append(Paragraph("No data available.", styles['Normal']))
        doc.build(elements)
        return buffer.getvalue()

    # Prepare table data
    fieldnames = list(records[0].keys())
    table_data = [fieldnames]  # Header row

    for row_dict in records:
        table_data.append([str(row_dict.get(field, "")) for field in fieldnames])

    # Create table
    table = Table(table_data)

    # Add style
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])
    table.setStyle(style)

    elements.append(table)
    doc.build(elements)

    return buffer.getvalue()
