from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def gerar_pdf_curriculo(data: dict, file_path: str):
    doc = SimpleDocTemplate(file_path, pagesize=A4)
    styles = getSampleStyleSheet()

    elements = []

    elements.append(Paragraph(f"<b>{data['nome']}</b>", styles["Title"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"<b>Objetivo:</b> {data['titulo_objetivo']}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("<b>Resumo Profissional</b>", styles["Heading2"]))
    elements.append(Paragraph(data["resumo"], styles["Normal"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("<b>Skills para Destacar</b>", styles["Heading2"]))
    elements.append(Paragraph(", ".join(data["skills"]), styles["Normal"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("<b>Pontos de Evolução</b>", styles["Heading2"]))
    elements.append(Paragraph(", ".join(data["gaps"]) if data["gaps"] else "Nenhum gap relevante identificado.", styles["Normal"]))

    doc.build(elements)