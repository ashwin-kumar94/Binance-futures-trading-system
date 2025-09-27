from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.units import inch

import os

def read_markdown(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def md_to_flowables(md_text: str):
    styles = getSampleStyleSheet()
    body = styles['BodyText']
    title = styles['Title']
    h1 = styles['Heading1']
    h2 = styles['Heading2']

    flow = []
    for line in md_text.splitlines():
        if line.startswith('# '):
            flow.append(Paragraph(line[2:].strip(), title))
            flow.append(Spacer(1, 0.2 * inch))
        elif line.startswith('## '):
            flow.append(Paragraph(line[3:].strip(), h1))
            flow.append(Spacer(1, 0.15 * inch))
        elif line.startswith('### '):
            flow.append(Paragraph(line[4:].strip(), h2))
            flow.append(Spacer(1, 0.1 * inch))
        elif line.strip().startswith('- '):
            # simple bullet list rendering
            txt = f"• {line.strip()[2:]}"
            flow.append(Paragraph(txt, body))
        elif line.strip() == '':
            flow.append(Spacer(1, 0.1 * inch))
        else:
            flow.append(Paragraph(line.strip(), body))
    return flow

def generate_pdf(md_path: str, pdf_path: str):
    md_text = read_markdown(md_path)
    doc = SimpleDocTemplate(pdf_path, pagesize=LETTER)
    flow = md_to_flowables(md_text)
    doc.build(flow)

if __name__ == '__main__':
    root = os.path.dirname(os.path.abspath(__file__))
    md_path = os.path.join(root, 'report.md')
    pdf_path = os.path.join(root, 'report.pdf')
    generate_pdf(md_path, pdf_path)
    print(f"Generated: {pdf_path}")