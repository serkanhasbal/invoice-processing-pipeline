"""
Sample Invoice Generator
-------------------------
Generates 8 realistic sample invoices in various formats (PDF and PNG)
for testing the invoice processing pipeline.

Formats produced:
  PDF:
    1. invoice_consulting_usd.pdf    — US consulting firm, USD, hourly billing
    2. invoice_retail_eur.pdf        — European retail/wholesale, EUR, multi-item
    3. invoice_saas_gbp.pdf          — UK SaaS subscription, GBP, simple
    4. invoice_construction_chf.pdf  — Swiss construction, CHF, with PO number
    5. invoice_paid_usd.pdf          — US invoice already marked as PAID

  PNG (simulated scanned/photographed invoices):
    6. invoice_simple_usd.png        — Simple US invoice, single item
    7. invoice_freelance_eur.png     — European freelancer, EUR, Net 30 terms
    8. invoice_retail_multi_gbp.png  — UK retail, GBP, multiple line items

Run:
    python3 scripts/generate_sample_invoices.py
"""

import os
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from reportlab.lib.units import mm, inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
from PIL import Image, ImageDraw, ImageFont
import io

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_invoices")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# PDF Invoice Generators
# ─────────────────────────────────────────────────────────────────────────────

def _base_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("Right",  parent=styles["Normal"], alignment=TA_RIGHT))
    styles.add(ParagraphStyle("Center", parent=styles["Normal"], alignment=TA_CENTER))
    styles.add(ParagraphStyle("Bold",   parent=styles["Normal"], fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle("BoldRight", parent=styles["Normal"],
                              fontName="Helvetica-Bold", alignment=TA_RIGHT))
    styles.add(ParagraphStyle("Title2", parent=styles["Normal"],
                              fontSize=20, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle("Small",  parent=styles["Normal"], fontSize=8))
    return styles


def make_pdf_consulting_usd():
    """US consulting invoice — hourly rates, multiple engineers, USD."""
    path = os.path.join(OUTPUT_DIR, "invoice_consulting_usd.pdf")
    doc = SimpleDocTemplate(path, pagesize=letter,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    s = _base_styles()
    story = []

    # Header
    story.append(Paragraph("Vertex Solutions LLC", s["Title2"]))
    story.append(Paragraph("1420 Harbor Blvd, Suite 300, Chicago, IL 60601", s["Normal"]))
    story.append(Paragraph("Tel: +1 (312) 555-0192  |  billing@vertexsolutions.com", s["Normal"]))
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2C3E50")))
    story.append(Spacer(1, 5*mm))

    # Invoice meta
    meta = [
        ["INVOICE", ""],
        ["Invoice Number:", "INV-2024-00847"],
        ["Invoice Date:",   "September 3, 2024"],
        ["Due Date:",       "October 3, 2024"],
        ["Bill To:", "Meridian Capital Group\n350 Fifth Avenue, New York, NY 10118\nAccounts Payable: ap@meridiancapital.com"],
    ]
    t = Table(meta, colWidths=[45*mm, 100*mm])
    t.setStyle(TableStyle([
        ("FONTNAME",  (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE",  (0,0), (1,0),  16),
        ("FONTNAME",  (0,0), (1,0),  "Helvetica-Bold"),
        ("TEXTCOLOR", (0,0), (1,0),  colors.HexColor("#2C3E50")),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("VALIGN",    (0,0), (-1,-1), "TOP"),
    ]))
    story.append(t)
    story.append(Spacer(1, 8*mm))

    # Line items
    story.append(Paragraph("Services Rendered — August 2024", s["Bold"]))
    story.append(Spacer(1, 3*mm))
    items = [
        ["Description",                         "Hours", "Rate (USD)", "Amount (USD)"],
        ["Senior Cloud Architect — AWS Design",  "40",   "$195.00",    "$7,800.00"],
        ["Backend Developer — API Integration",  "56",   "$145.00",    "$8,120.00"],
        ["QA Engineer — Automated Testing",      "32",   "$110.00",    "$3,520.00"],
        ["Project Management",                   "12",   "$165.00",    "$1,980.00"],
        ["Technical Documentation",              "8",    "$95.00",     "$760.00"],
    ]
    t2 = Table(items, colWidths=[85*mm, 20*mm, 35*mm, 35*mm])
    t2.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0),  colors.HexColor("#2C3E50")),
        ("TEXTCOLOR",    (0,0), (-1,0),  colors.white),
        ("FONTNAME",     (0,0), (-1,0),  "Helvetica-Bold"),
        ("ALIGN",        (1,0), (-1,-1), "RIGHT"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [colors.white, colors.HexColor("#F2F3F4")]),
        ("GRID",         (0,0), (-1,-1), 0.5, colors.lightgrey),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
        ("TOPPADDING",   (0,0), (-1,-1), 5),
    ]))
    story.append(t2)
    story.append(Spacer(1, 5*mm))

    # Totals
    totals = [
        ["", "Subtotal:",   "$22,180.00"],
        ["", "Tax (8.5%):", "$1,885.30"],
        ["", "TOTAL DUE:",  "$24,065.30"],
    ]
    t3 = Table(totals, colWidths=[100*mm, 35*mm, 40*mm])
    t3.setStyle(TableStyle([
        ("ALIGN",     (1,0), (-1,-1), "RIGHT"),
        ("FONTNAME",  (1,2), (-1,2),  "Helvetica-Bold"),
        ("FONTSIZE",  (1,2), (-1,2),  12),
        ("LINEABOVE", (1,2), (-1,2),  1, colors.black),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(t3)
    story.append(Spacer(1, 8*mm))

    # Payment terms
    story.append(Paragraph("Payment Terms: Net 30 days. Wire transfer preferred.", s["Small"]))
    story.append(Paragraph("Bank: Chase Bank | Account: 8823-XXXX | Routing: 021000021", s["Small"]))

    doc.build(story)
    print(f"  Created: {path}")
    return path


def make_pdf_retail_eur():
    """European wholesale/retail invoice — multiple product items, EUR, VAT."""
    path = os.path.join(OUTPUT_DIR, "invoice_retail_eur.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    s = _base_styles()
    story = []

    story.append(Paragraph("EuroTrade GmbH", s["Title2"]))
    story.append(Paragraph("Hauptstraße 42, 80331 München, Deutschland", s["Normal"]))
    story.append(Paragraph("USt-IdNr: DE298765432  |  info@eurotrade.de", s["Normal"]))
    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#27AE60")))
    story.append(Spacer(1, 4*mm))

    meta = [
        ["Rechnung (Invoice)",  ""],
        ["Rechnungsnummer:", "RE-2024-3892"],
        ["Rechnungsdatum:",  "15.08.2024"],
        ["Lieferdatum:",     "10.08.2024"],
        ["Bestellnummer:",   "PO-88432"],
        ["Rechnungsempfänger:", "Nordic Supplies AS\nKarl Johans gate 14\n0154 Oslo, Norway"],
    ]
    t = Table(meta, colWidths=[50*mm, 120*mm])
    t.setStyle(TableStyle([
        ("FONTNAME",  (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE",  (0,0), (-1,0), 15),
        ("TEXTCOLOR", (0,0), (-1,0), colors.HexColor("#27AE60")),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("VALIGN",    (0,0), (-1,-1), "TOP"),
    ]))
    story.append(t)
    story.append(Spacer(1, 6*mm))

    items = [
        ["Pos.", "Artikelbeschreibung",           "Menge", "Einheit", "Einzelpreis €", "Gesamt €"],
        ["1",   "Industrial Cable Reel 50m",       "20",   "Stk",    "45.90",          "918.00"],
        ["2",   "Safety Gloves Class B (12-pack)", "15",   "Pack",   "28.50",          "427.50"],
        ["3",   "LED Flood Light 200W IP65",        "8",    "Stk",    "119.00",         "952.00"],
        ["4",   "Extension Cord 10m 3-socket",     "50",   "Stk",    "12.80",          "640.00"],
        ["5",   "Circuit Breaker 16A",             "100",  "Stk",    "8.40",           "840.00"],
        ["6",   "Shipping & Handling",             "1",    "Pausch",  "75.00",          "75.00"],
    ]
    t2 = Table(items, colWidths=[12*mm, 72*mm, 16*mm, 18*mm, 26*mm, 26*mm])
    t2.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0),  colors.HexColor("#27AE60")),
        ("TEXTCOLOR",    (0,0), (-1,0),  colors.white),
        ("FONTNAME",     (0,0), (-1,0),  "Helvetica-Bold"),
        ("ALIGN",        (2,0), (-1,-1), "RIGHT"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [colors.white, colors.HexColor("#EAFAF1")]),
        ("GRID",         (0,0), (-1,-1), 0.5, colors.lightgrey),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ("TOPPADDING",   (0,0), (-1,-1), 4),
        ("FONTSIZE",     (0,0), (-1,-1), 9),
    ]))
    story.append(t2)
    story.append(Spacer(1, 4*mm))

    totals = [
        ["", "Nettobetrag:",        "€ 3,852.50"],
        ["", "MwSt. 19%:",          "€   731.98"],
        ["", "Rechnungsbetrag:",    "€ 4,584.48"],
    ]
    t3 = Table(totals, colWidths=[110*mm, 35*mm, 35*mm])
    t3.setStyle(TableStyle([
        ("ALIGN",     (1,0), (-1,-1), "RIGHT"),
        ("FONTNAME",  (1,2), (-1,2),  "Helvetica-Bold"),
        ("FONTSIZE",  (1,2), (-1,2),  11),
        ("LINEABOVE", (1,2), (-1,2),  1, colors.black),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(t3)
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("Zahlungsbedingungen: 30 Tage netto. IBAN: DE89 3704 0044 0532 0130 00", s["Small"]))

    doc.build(story)
    print(f"  Created: {path}")
    return path


def make_pdf_saas_gbp():
    """UK SaaS subscription invoice — simple, monthly recurring, GBP."""
    path = os.path.join(OUTPUT_DIR, "invoice_saas_gbp.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=25*mm, rightMargin=25*mm,
                            topMargin=25*mm, bottomMargin=25*mm)
    s = _base_styles()
    story = []

    story.append(Paragraph("Cloudify Ltd", s["Title2"]))
    story.append(Paragraph("12 Finsbury Square, London EC2A 1AS, United Kingdom", s["Normal"]))
    story.append(Paragraph("VAT No: GB 294 8765 21  |  accounts@cloudify.io", s["Normal"]))
    story.append(Spacer(1, 8*mm))

    story.append(Table([
        [Paragraph("TAX INVOICE", ParagraphStyle("H", fontName="Helvetica-Bold", fontSize=16)),
         Paragraph("Invoice #: CLF-2024-09-1142\nDate: 01 September 2024\nDue: 15 September 2024",
                   ParagraphStyle("R", alignment=TA_RIGHT, fontSize=10))]
    ], colWidths=[90*mm, 90*mm]))
    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#8E44AD")))
    story.append(Spacer(1, 6*mm))

    story.append(Paragraph("Bill To:", s["Bold"]))
    story.append(Paragraph("Hartwell & Partners LLP\n22 Old Broad Street, London EC2N 1HQ", s["Normal"]))
    story.append(Spacer(1, 6*mm))

    items = [
        ["Description",                         "Qty", "Unit Price", "Amount"],
        ["Cloudify Business Plan — September 2024", "1", "£ 599.00", "£ 599.00"],
        ["Additional User Seats (×5)",           "5",   "£  29.00",  "£ 145.00"],
        ["Premium Support Add-on",               "1",   "£  75.00",  "£  75.00"],
    ]
    t = Table(items, colWidths=[90*mm, 15*mm, 35*mm, 35*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0),  colors.HexColor("#8E44AD")),
        ("TEXTCOLOR",    (0,0), (-1,0),  colors.white),
        ("FONTNAME",     (0,0), (-1,0),  "Helvetica-Bold"),
        ("ALIGN",        (1,0), (-1,-1), "RIGHT"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [colors.white, colors.HexColor("#F5EEF8")]),
        ("GRID",         (0,0), (-1,-1), 0.5, colors.lightgrey),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
        ("TOPPADDING",   (0,0), (-1,-1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 4*mm))

    totals = [
        ["", "Subtotal:",  "£ 819.00"],
        ["", "VAT (20%):", "£ 163.80"],
        ["", "Total Due:", "£ 982.80"],
    ]
    t2 = Table(totals, colWidths=[100*mm, 35*mm, 40*mm])
    t2.setStyle(TableStyle([
        ("ALIGN",     (1,0), (-1,-1), "RIGHT"),
        ("FONTNAME",  (1,2), (-1,2),  "Helvetica-Bold"),
        ("LINEABOVE", (1,2), (-1,2),  1, colors.black),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(t2)
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("Payment: BACS transfer. Sort code: 20-00-00 | Account: 55779911", s["Small"]))

    doc.build(story)
    print(f"  Created: {path}")
    return path


def make_pdf_construction_chf():
    """Swiss construction invoice — CHF, with PO number, multi-phase project."""
    path = os.path.join(OUTPUT_DIR, "invoice_construction_chf.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    s = _base_styles()
    story = []

    story.append(Paragraph("Müller Bau AG", s["Title2"]))
    story.append(Paragraph("Bahnhofstrasse 88, 8001 Zürich, Schweiz", s["Normal"]))
    story.append(Paragraph("MWST-Nr: CHE-123.456.789 MWST  |  rechnung@muellerbau.ch", s["Normal"]))
    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#E67E22")))
    story.append(Spacer(1, 4*mm))

    meta = [
        ["RECHNUNG / FACTURE", ""],
        ["Rechnungsnummer:",   "MB-2024-0556"],
        ["Datum:",             "22.07.2024"],
        ["Zahlbar bis:",       "21.08.2024"],
        ["Bestellreferenz:",   "PO-2024-BL-0093"],
        ["Bauprojekt:",        "Neubau Bürogebäude Leutschenbachstrasse"],
        ["Auftraggeber:", "Zürcher Immobilien AG\nSeestrasse 45, 8002 Zürich"],
    ]
    t = Table(meta, colWidths=[50*mm, 120*mm])
    t.setStyle(TableStyle([
        ("FONTNAME",  (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE",  (0,0), (-1,0), 14),
        ("TEXTCOLOR", (0,0), (-1,0), colors.HexColor("#E67E22")),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("VALIGN",    (0,0), (-1,-1), "TOP"),
    ]))
    story.append(t)
    story.append(Spacer(1, 6*mm))

    story.append(Paragraph("Leistungsverzeichnis — Juli 2024", s["Bold"]))
    story.append(Spacer(1, 3*mm))

    items = [
        ["Pos.", "Leistungsbeschreibung",           "Einheit", "Menge",  "Einheitspreis CHF", "Betrag CHF"],
        ["1.1",  "Erdarbeiten und Aushub",          "m³",      "350",    "85.00",              "29,750.00"],
        ["1.2",  "Betonarbeiten Fundament B25",     "m³",      "120",    "220.00",             "26,400.00"],
        ["2.1",  "Stahlbau Tragkonstruktion",       "t",       "18.5",   "1,850.00",           "34,225.00"],
        ["2.2",  "Zimmermannsarbeiten Dachstuhl",   "m²",      "480",    "95.00",              "45,600.00"],
        ["3.1",  "Elektrische Installationen EG",   "Pausch.", "1",      "12,400.00",          "12,400.00"],
        ["3.2",  "Sanitär Rohinstallation",         "Pausch.", "1",      "8,900.00",            "8,900.00"],
        ["4.0",  "Gerüstmiete Juli 2024",            "Monat",   "1",      "2,200.00",            "2,200.00"],
    ]
    t2 = Table(items, colWidths=[12*mm, 72*mm, 16*mm, 14*mm, 32*mm, 30*mm])
    t2.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0),  colors.HexColor("#E67E22")),
        ("TEXTCOLOR",    (0,0), (-1,0),  colors.white),
        ("FONTNAME",     (0,0), (-1,0),  "Helvetica-Bold"),
        ("ALIGN",        (2,0), (-1,-1), "RIGHT"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [colors.white, colors.HexColor("#FEF9E7")]),
        ("GRID",         (0,0), (-1,-1), 0.5, colors.lightgrey),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ("TOPPADDING",   (0,0), (-1,-1), 4),
        ("FONTSIZE",     (0,0), (-1,-1), 9),
    ]))
    story.append(t2)
    story.append(Spacer(1, 4*mm))

    totals = [
        ["", "Nettobetrag:",     "CHF 159,475.00"],
        ["", "MWST 8.1%:",       "CHF  12,917.48"],
        ["", "Rechnungstotal:", "CHF 172,392.48"],
    ]
    t3 = Table(totals, colWidths=[110*mm, 35*mm, 40*mm])
    t3.setStyle(TableStyle([
        ("ALIGN",     (1,0), (-1,-1), "RIGHT"),
        ("FONTNAME",  (1,2), (-1,2),  "Helvetica-Bold"),
        ("FONTSIZE",  (1,2), (-1,2),  11),
        ("LINEABOVE", (1,2), (-1,2),  1.5, colors.black),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(t3)
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("Zahlungskonditionen: 30 Tage netto. IBAN: CH56 0483 5012 3456 7800 9", s["Small"]))

    doc.build(story)
    print(f"  Created: {path}")
    return path


def make_pdf_paid_usd():
    """US invoice marked as PAID — tests payment status extraction."""
    path = os.path.join(OUTPUT_DIR, "invoice_paid_usd.pdf")
    doc = SimpleDocTemplate(path, pagesize=letter,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    s = _base_styles()
    story = []

    story.append(Paragraph("Apex Marketing Agency", s["Title2"]))
    story.append(Paragraph("800 N Michigan Ave, Chicago, IL 60611", s["Normal"]))
    story.append(Paragraph("EIN: 82-XXXXXXX  |  invoices@apexmarketing.com", s["Normal"]))
    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1ABC9C")))
    story.append(Spacer(1, 4*mm))

    story.append(Table([[
        Paragraph("INVOICE", ParagraphStyle("H", fontName="Helvetica-Bold", fontSize=18)),
        Paragraph("Invoice #: APX-2024-0231\nDate: June 1, 2024\nPayment Due: June 15, 2024",
                  ParagraphStyle("R", alignment=TA_RIGHT, fontSize=10))
    ]], colWidths=[95*mm, 95*mm]))
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph("Bill To: TechFlow Inc.  |  500 Brannan St, San Francisco, CA 94107", s["Normal"]))
    story.append(Spacer(1, 6*mm))

    items = [
        ["Service",                             "Quantity", "Price",    "Total"],
        ["Brand Strategy & Positioning",        "1",        "$3,500.00","$3,500.00"],
        ["Social Media Campaign (3 platforms)", "1",        "$2,200.00","$2,200.00"],
        ["Content Creation (10 articles)",      "10",       "$  350.00","$3,500.00"],
        ["SEO Audit & Recommendations",         "1",        "$1,800.00","$1,800.00"],
        ["Monthly Retainer Fee",                "1",        "$1,500.00","$1,500.00"],
    ]
    t = Table(items, colWidths=[90*mm, 25*mm, 35*mm, 35*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0),  colors.HexColor("#1ABC9C")),
        ("TEXTCOLOR",    (0,0), (-1,0),  colors.white),
        ("FONTNAME",     (0,0), (-1,0),  "Helvetica-Bold"),
        ("ALIGN",        (1,0), (-1,-1), "RIGHT"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [colors.white, colors.HexColor("#E8F8F5")]),
        ("GRID",         (0,0), (-1,-1), 0.5, colors.lightgrey),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
        ("TOPPADDING",   (0,0), (-1,-1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 4*mm))

    totals = [
        ["", "Subtotal:",   "$12,500.00"],
        ["", "Tax (9%):",   " $1,125.00"],
        ["", "TOTAL:",      "$13,625.00"],
    ]
    t2 = Table(totals, colWidths=[100*mm, 35*mm, 50*mm])
    t2.setStyle(TableStyle([
        ("ALIGN",     (1,0), (-1,-1), "RIGHT"),
        ("FONTNAME",  (1,2), (-1,2),  "Helvetica-Bold"),
        ("LINEABOVE", (1,2), (-1,2),  1, colors.black),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(t2)
    story.append(Spacer(1, 8*mm))

    # PAID stamp effect
    paid_style = ParagraphStyle("Paid",
        fontName="Helvetica-Bold", fontSize=36,
        textColor=colors.HexColor("#27AE60"),
        alignment=TA_CENTER,
        borderColor=colors.HexColor("#27AE60"),
        borderWidth=3, borderPadding=6,
    )
    story.append(Paragraph("✓ PAYMENT RECEIVED — PAID IN FULL", paid_style))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("Payment received on June 12, 2024 via ACH Transfer. Thank you for your business.", s["Small"]))

    doc.build(story)
    print(f"  Created: {path}")
    return path


# ─────────────────────────────────────────────────────────────────────────────
# PNG Invoice Generators (using Pillow — simulates scanned/photo invoices)
# ─────────────────────────────────────────────────────────────────────────────

def _draw_text(draw, xy, text, size=14, bold=False, color=(30, 30, 30)):
    """Draw text at position using a default font (falls back gracefully)."""
    try:
        if bold:
            font = ImageFont.truetype("/Library/Fonts/Arial Bold.ttf", size)
        else:
            font = ImageFont.truetype("/Library/Fonts/Arial.ttf", size)
    except Exception:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)
        except Exception:
            font = ImageFont.load_default()
    draw.text(xy, text, font=font, fill=color)


def make_png_simple_usd():
    """Simple US invoice as PNG — single service, minimal design."""
    path = os.path.join(OUTPUT_DIR, "invoice_simple_usd.png")
    W, H = 1200, 1600
    img = Image.new("RGB", (W, H), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Header bar
    draw.rectangle([0, 0, W, 120], fill=(44, 62, 80))
    _draw_text(draw, (60, 25), "NOVA DESIGN STUDIO", size=36, bold=True, color=(255,255,255))
    _draw_text(draw, (60, 75), "204 W 10th St, New York, NY 10014  |  hello@novadesign.studio", size=18, color=(189,195,199))

    # Invoice title
    _draw_text(draw, (60, 160), "INVOICE", size=48, bold=True, color=(44,62,80))

    # Meta block
    y = 240
    fields = [
        ("Invoice Number:", "ND-2024-0078"),
        ("Invoice Date:",   "October 15, 2024"),
        ("Payment Due:",    "November 14, 2024"),
        ("Bill To:",        "Clearwater Consulting LLC"),
        ("",                "1875 K Street NW, Washington, DC 20006"),
        ("",                "Contact: Michael Torres"),
    ]
    for label, value in fields:
        if label:
            _draw_text(draw, (60, y),   label, size=20, bold=True)
        _draw_text(draw, (320, y), value, size=20)
        y += 40

    # Divider
    y += 20
    draw.rectangle([60, y, W-60, y+3], fill=(44,62,80))
    y += 20

    # Table header
    draw.rectangle([60, y, W-60, y+50], fill=(44,62,80))
    cols = [60, 600, 780, 960, W-60]
    headers = ["Description", "Qty", "Rate", "Amount"]
    for i, h in enumerate(headers):
        _draw_text(draw, (cols[i]+10, y+12), h, size=18, bold=True, color=(255,255,255))
    y += 50

    # Single line item
    draw.rectangle([60, y, W-60, y+60], fill=(242,243,244))
    row = ["Brand Identity Design Package", "1", "$4,500.00", "$4,500.00"]
    for i, val in enumerate(row):
        _draw_text(draw, (cols[i]+10, y+18), val, size=18)
    y += 60

    draw.rectangle([60, y, W-60, y+60], fill=(255,255,255))
    row2 = ["Rush delivery fee (48hr turnaround)", "1", "$750.00", "$750.00"]
    for i, val in enumerate(row2):
        _draw_text(draw, (cols[i]+10, y+18), val, size=18)
    y += 80

    # Totals
    draw.rectangle([60, y, W-60, y+2], fill=(200,200,200))
    y += 20
    totals = [("Subtotal:", "$5,250.00"), ("Tax (8.875%):", "$465.94"), ("TOTAL DUE:", "$5,715.94")]
    for label, val in totals:
        _draw_text(draw, (800, y), label, size=22, bold=(label.startswith("TOTAL")))
        _draw_text(draw, (1050, y), val, size=22, bold=(label.startswith("TOTAL")))
        y += 45

    y += 30
    _draw_text(draw, (60, y), "Payment Terms: Net 30 | Venmo / ACH / Check accepted", size=16, color=(100,100,100))
    y += 30
    _draw_text(draw, (60, y), "Thank you for your business!", size=18, color=(44,62,80))

    img.save(path, "PNG", dpi=(150, 150))
    print(f"  Created: {path}")
    return path


def make_png_freelance_eur():
    """European freelancer invoice as PNG — EUR, Net 30, minimalist."""
    path = os.path.join(OUTPUT_DIR, "invoice_freelance_eur.png")
    W, H = 1200, 1700
    img = Image.new("RGB", (W, H), color=(250, 250, 248))
    draw = ImageDraw.Draw(img)

    # Accent line
    draw.rectangle([0, 0, 8, H], fill=(39,174,96))

    # Vendor
    _draw_text(draw, (60, 60), "Sophie Leclerc", size=40, bold=True, color=(30,30,30))
    _draw_text(draw, (60, 115), "Freelance UX/UI Designer", size=22, color=(100,100,100))
    _draw_text(draw, (60, 148), "14 Rue de Rivoli, 75001 Paris, France", size=18, color=(120,120,120))
    _draw_text(draw, (60, 175), "SIRET: 823 456 789 00014  |  sophie@leclerc-design.fr", size=16, color=(120,120,120))

    # Invoice header right-aligned
    _draw_text(draw, (750, 60),  "FACTURE", size=40, bold=True, color=(39,174,96))
    _draw_text(draw, (750, 115), "N° Facture:  FCT-2024-0032", size=18)
    _draw_text(draw, (750, 145), "Date:         01/10/2024", size=18)
    _draw_text(draw, (750, 175), "Échéance:    31/10/2024", size=18)

    # Divider
    draw.rectangle([60, 230, W-60, 232], fill=(200,200,200))

    # Bill To
    _draw_text(draw, (60, 255), "Facturer à:", size=20, bold=True)
    _draw_text(draw, (60, 290), "BrightMind Agency SARL", size=22, bold=True)
    _draw_text(draw, (60, 325), "28 Avenue de l'Opéra, 75002 Paris", size=18)
    _draw_text(draw, (60, 355), "TVA Intracommunautaire: FR 76 432 876 543", size=16, color=(120,120,120))

    # Table
    y = 420
    draw.rectangle([60, y, W-60, y+55], fill=(39,174,96))
    cols = [60, 550, 720, 890, W-60]
    headers = ["Prestation", "Jours", "Tarif journalier", "Total HT"]
    for i, h in enumerate(headers):
        _draw_text(draw, (cols[i]+12, y+14), h, size=18, bold=True, color=(255,255,255))
    y += 55

    rows = [
        ("Conception UX — Application mobile",     "8", "€ 650.00", "€ 5,200.00"),
        ("Création maquettes UI (Figma)",           "5", "€ 650.00", "€ 3,250.00"),
        ("Tests utilisateurs & rapport d'analyse",  "2", "€ 650.00", "€ 1,300.00"),
        ("Révisions et ajustements finaux",         "1", "€ 650.00", "€   650.00"),
    ]
    for idx, (desc, qty, rate, total) in enumerate(rows):
        bg = (255,255,255) if idx % 2 == 0 else (240,248,240)
        draw.rectangle([60, y, W-60, y+55], fill=bg)
        _draw_text(draw, (cols[0]+12, y+15), desc, size=17)
        _draw_text(draw, (cols[1]+12, y+15), qty, size=17)
        _draw_text(draw, (cols[2]+12, y+15), rate, size=17)
        _draw_text(draw, (cols[3]+12, y+15), total, size=17)
        y += 55

    # Totals
    y += 20
    draw.rectangle([60, y, W-60, y+2], fill=(200,200,200))
    y += 20
    totals = [
        ("Total HT:",       "€ 10,400.00"),
        ("TVA 20%:",        "€  2,080.00"),
        ("Total TTC:",      "€ 12,480.00"),
    ]
    for label, val in totals:
        is_total = "TTC" in label
        _draw_text(draw, (760, y), label, size=22, bold=is_total)
        _draw_text(draw, (1020, y), val,  size=22, bold=is_total)
        y += 48

    if is_total:
        draw.rectangle([755, y-2, W-60, y], fill=(39,174,96))

    y += 30
    _draw_text(draw, (60, y), "Modalités de paiement: Virement bancaire sous 30 jours", size=17, color=(80,80,80))
    y += 30
    _draw_text(draw, (60, y), "IBAN: FR76 3000 6000 0112 3456 7890 189 | BIC: BNPAFRPP", size=16, color=(120,120,120))
    y += 50
    _draw_text(draw, (60, y), "Merci pour votre confiance.", size=18, color=(39,174,96))

    img.save(path, "PNG", dpi=(150, 150))
    print(f"  Created: {path}")
    return path


def make_png_retail_gbp():
    """UK retail invoice as PNG — GBP, multiple product items, classic layout."""
    path = os.path.join(OUTPUT_DIR, "invoice_retail_multi_gbp.png")
    W, H = 1200, 1900
    img = Image.new("RGB", (W, H), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Header
    draw.rectangle([0, 0, W, 130], fill=(142,68,173))
    _draw_text(draw, (60, 28), "BritishOfficeSupplies.co.uk", size=34, bold=True, color=(255,255,255))
    _draw_text(draw, (60, 80), "Unit 7, Trafford Park, Manchester M17 1PQ  |  VAT: GB 123 4567 89", size=18, color=(220,200,240))

    # Invoice / meta
    y = 160
    _draw_text(draw, (60, y), "INVOICE", size=44, bold=True, color=(142,68,173))
    _draw_text(draw, (700, y),  "Invoice No:  BOS-INV-20241105", size=20, bold=True)
    _draw_text(draw, (700, y+40), "Date:          05 November 2024", size=18)
    _draw_text(draw, (700, y+75), "Payment Due: 05 December 2024", size=18)
    _draw_text(draw, (700, y+110),"PO Reference:  PO-GH-5523", size=18)
    y += 180

    _draw_text(draw, (60, y), "Invoice To:", size=20, bold=True)
    y += 35
    _draw_text(draw, (60, y), "Greenhill Academy Trust", size=22, bold=True)
    y += 35
    _draw_text(draw, (60, y), "15 School Lane, Leeds LS7 4AA", size=18)
    y += 35
    _draw_text(draw, (60, y), "Contact: Procurement Dept", size=16, color=(100,100,100))
    y += 50

    # Table
    draw.rectangle([60, y, W-60, y+55], fill=(142,68,173))
    cols = [60, 460, 610, 770, 930, W-60]
    headers = ["Item Description", "SKU", "Qty", "Unit Price", "VAT", "Line Total"]
    for i, h in enumerate(headers):
        _draw_text(draw, (cols[i]+8, y+14), h, size=16, bold=True, color=(255,255,255))
    y += 55

    rows = [
        ("A4 Copier Paper 80gsm (Box of 5 reams)", "PAP-A4-80",  "10", "£ 14.99", "20%", "£ 149.90"),
        ("Black Ballpoint Pens (Box of 50)",        "PEN-BP-50",  "5",  "£  8.50", "20%", "£  42.50"),
        ("Lever Arch Files A4 (Pack of 10)",        "FILE-LA-10", "8",  "£ 12.75", "20%", "£ 102.00"),
        ("Whiteboard Markers Assorted (Pack 8)",    "MRK-WB-8",   "12", "£  5.99", "20%", "£  71.88"),
        ("Printer Toner HP 85A Black",              "TNR-HP85A",  "3",  "£ 54.00", "20%", "£ 162.00"),
        ("Stapler Heavy Duty 100-sheet",            "STP-HD100",  "4",  "£ 22.50", "20%", "£  90.00"),
        ("Sticky Notes 76x76mm (Pack of 12)",       "STK-7676",   "20", "£  4.25", "20%", "£  85.00"),
        ("Scissors Stainless Steel 21cm",           "SCS-21SS",   "6",  "£  3.99", "20%", "£  23.94"),
    ]
    for idx, row in enumerate(rows):
        bg = (255,255,255) if idx % 2 == 0 else (245,238,248)
        draw.rectangle([60, y, W-60, y+52], fill=bg)
        for i, val in enumerate(row):
            _draw_text(draw, (cols[i]+8, y+14), val, size=15)
        y += 52

    # Totals
    y += 20
    draw.rectangle([60, y, W-60, y+2], fill=(142,68,173))
    y += 15
    items_subtotal = 727.22
    vat = 145.44
    total = 872.66
    totals = [
        ("Net Amount:",    f"£ {items_subtotal:,.2f}"),
        ("VAT (20%):",     f"£ {vat:,.2f}"),
        ("Invoice Total:", f"£ {total:,.2f}"),
    ]
    for label, val in totals:
        is_total = "Total" in label
        _draw_text(draw, (780, y), label, size=22, bold=is_total)
        _draw_text(draw, (1040, y), val,  size=22, bold=is_total)
        y += 48

    y += 20
    _draw_text(draw, (60, y), "Terms: 30 days net. Bank: Barclays | Sort: 20-18-19 | Acc: 33445566", size=16, color=(80,80,80))
    y += 35
    _draw_text(draw, (60, y), "Remittance to: accounts@britishofficessupplies.co.uk", size=16, color=(80,80,80))

    img.save(path, "PNG", dpi=(150, 150))
    print(f"  Created: {path}")
    return path


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"Generating sample invoices → {OUTPUT_DIR}/\n")

    print("PDF invoices:")
    make_pdf_consulting_usd()
    make_pdf_retail_eur()
    make_pdf_saas_gbp()
    make_pdf_construction_chf()
    make_pdf_paid_usd()

    print("\nPNG invoices:")
    make_png_simple_usd()
    make_png_freelance_eur()
    make_png_retail_gbp()

    files = os.listdir(OUTPUT_DIR)
    print(f"\n✅ {len(files)} invoice files generated in sample_invoices/")
    for f in sorted(files):
        size = os.path.getsize(os.path.join(OUTPUT_DIR, f))
        print(f"   {f:45s}  {size/1024:.0f} KB")
