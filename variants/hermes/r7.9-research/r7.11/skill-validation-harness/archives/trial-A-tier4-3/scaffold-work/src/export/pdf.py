from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import io

def serialize_pdf(records: list[dict]) -> bytes:
    """
    Serializes a list of dictionaries into a PDF byte string.
    
    Args:
        records: A list of dictionaries representing the rows.
        
    Returns:
        A PDF formatted byte string. Returns an empty byte string if records is empty.
    """
    if not records:
        return b""

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Header
    elements.append(Paragraph("Exported Data", styles['Title']))
    elements.append(Paragraph("<br/><br/>", styles['Normal']))

    # Prepare Data for Table
    # Get headers from first record
    headers = list(records[0].keys())
    data = [headers]
    
    for record in records:
        row = [str(record.get(h, "")) for h in headers]
        data.append(row)

    # Create Table
    table = Table(data)
    
    # Add Style
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#cccccc'),
        ('TEXTCOLOR', (0, 0), (-1, 0), '#000000'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), '#ffffff'),
        ('GRID', (0, 0), (-1, -1), 1, '#000000'),
    ])
    table.setStyle(style)
    
    elements.append(table)
    doc.build(elements)
    
    return buffer.getvalue()

def serialize_pdf_with_title(records: list[dict], title: str = "Exported Data") -> bytes:
    """
    Serializes a list of dictionaries into a PDF byte string with a custom title.
    
    Args:
        records: A list of dictionaries representing the rows.
        title: The title to display at the top of the PDF.
        
    Returns:
        A PDF formatted byte string.
    """
    if not records:
        return b""

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Header
    elements.append(Paragraph(title, styles['Title']))
    elements.append(Paragraph("<br/><br/>", styles['Normal']))

    # Prepare Data for Table
    headers = list(records[0].keys())
    data = [headers]
    
    for record in records:
        row = [str(record.get(h, "")) for h in headers]
        data.append(row)

    # Create Table
    table = Table(data)
    
    # Add Style
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#cccccc'),
        ('TEXTCOLOR', (0, 0), (-1, 0), '#000000'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), '#ffffff'),
        ('GRID', (0, 0), (-1, -1), 1, '#000000'),
    ])
    table.setStyle(style)
    
    elements.append(table)
    doc.build(elements)
    
    return buffer.getvalue()

if __name__ == "__main__":
    # Test cases
    test_data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
    pdf_bytes = serialize_pdf(test_data)
    print(f"Generated PDF with {len(pdf_bytes)} bytes")
    
    pdf_bytes_custom = serialize_pdf_with_title(test_data, "Custom Title")
    print(f"Generated PDF with custom title, {len(pdf_bytes_custom)} bytes")
    
    print(f"Empty PDF: {len(serialize_pdf([]))} bytes")
