"""
Energy Invoice Generator — Fictional Data
------------------------------------------
Generates synthetic colocation/power invoices from completely fictional providers.
NO real company names, NO real location codes, NO real addresses.

Fictional providers:
  1. Nexova Datacenters SARL     — Paris area, EUR
  2. BritCore Hosting Ltd        — London area, GBP
  3. Rheintech Rechenzentrum AG  — Frankfurt area, EUR
  4. Alpencloud Services AG      — Zurich area, CHF
  5. Deltanode BV                — Amsterdam area, EUR
  6. Severn Digital Facilities   — London area, GBP

Run:
    python3 scripts/generate_energy_invoices.py
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_invoices")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle("R",   parent=s["Normal"], alignment=TA_RIGHT))
    s.add(ParagraphStyle("B",   parent=s["Normal"], fontName="Helvetica-Bold"))
    s.add(ParagraphStyle("Sm",  parent=s["Normal"], fontSize=8))
    return s


def _table_style(header_color):
    return TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  header_color),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("ALIGN",         (1, 0), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
        ("GRID",          (0, 0), (-1, -1), 0.4, colors.lightgrey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
    ])


def _totals_style():
    return TableStyle([
        ("ALIGN",         (1, 0), (-1, -1), "RIGHT"),
        ("FONTNAME",      (1, 2), (-1, 2),  "Helvetica-Bold"),
        ("FONTSIZE",      (1, 2), (-1, 2),  11),
        ("LINEABOVE",     (1, 2), (-1, 2),  1, colors.black),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ])


# ─────────────────────────────────────────────────────────────────────────────
# 1. Nexova Datacenters SARL — Paris, EUR
# ─────────────────────────────────────────────────────────────────────────────
def make_nexova_paris():
    path = os.path.join(OUTPUT_DIR, "energy_nexova_paris_202409.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    s = _styles()
    col = colors.HexColor("#1A3A6B")
    story = []

    story.append(Paragraph("NEXOVA DATACENTERS",
                 ParagraphStyle("H", fontName="Helvetica-Bold", fontSize=26, textColor=col)))
    story.append(Paragraph("Nexova Datacenters SARL", s["Normal"]))
    story.append(Paragraph("42 Rue de la Technologie, 93200 Aubervilliers, France", s["Normal"]))
    story.append(Paragraph("TVA Intra: FR 12 987 654 321  |  facturation@nexova-dc.fr", s["Normal"]))
    story.append(Spacer(1, 5*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=col))
    story.append(Spacer(1, 4*mm))

    meta = [
        ["FACTURE / INVOICE", ""],
        ["Numéro de facture:", "NXV-2024-09-00447"],
        ["Date de facture:",   "30 septembre 2024"],
        ["Période de facturation:", "Septembre 2024"],
        ["Client:", "Marchand Capital Partners SAS\n18 Boulevard Haussmann\n75009 Paris, France"],
        ["Référence contrat:", "NXV-MCP-2020-0091"],
    ]
    t = Table(meta, colWidths=[55*mm, 120*mm])
    t.setStyle(TableStyle([("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
                            ("FONTSIZE",(0,0),(-1,0),14),
                            ("TEXTCOLOR",(0,0),(-1,0),col),
                            ("BOTTOMPADDING",(0,0),(-1,-1),4),
                            ("VALIGN",(0,0),(-1,-1),"TOP")]))
    story.append(t)
    story.append(Spacer(1, 6*mm))

    story.append(Paragraph("Détail consommation électrique — Septembre 2024", s["B"]))
    story.append(Spacer(1, 2*mm))
    items = [
        ["Description",                         "Unité",  "Quantité",  "Tarif",         "Montant HT"],
        ["Consommation IT mesurée",              "kWh",   "1,947,094", "€0.09175/kWh",  "€178,682.37"],
        ["Majoration PUE réel (1.302)",          "coeff.", "—",         "—",             "€ 55,164.97"],
        ["Infrastructure & refroidissement",    "forfait","1",          "€12,500.00",    "€ 12,500.00"],
        ["Service technique sur site (4h)",      "heure",  "4",         "€95.00/h",      "€    380.00"],
    ]
    t2 = Table(items, colWidths=[75*mm, 18*mm, 24*mm, 30*mm, 30*mm])
    t2.setStyle(_table_style(col))
    story.append(t2)
    story.append(Spacer(1, 4*mm))

    totals = [
        ["", "Sous-total HT:",   "€ 246,727.34"],
        ["", "TVA 20%:",         "€  49,345.47"],
        ["", "TOTAL TTC:",       "€ 296,072.81"],
    ]
    t3 = Table(totals, colWidths=[105*mm, 40*mm, 40*mm])
    t3.setStyle(_totals_style())
    story.append(t3)
    story.append(Spacer(1, 5*mm))
    story.append(Paragraph("PUE Réel: 1.302  |  PUE Maximum Contractuel: 1.50", s["B"]))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("Échéance: 30 jours — IBAN: FR76 1820 6004 8800 1234 5678 900", s["Sm"]))

    doc.build(story)
    print(f"  Created: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# 2. BritCore Hosting Ltd — London, GBP
# ─────────────────────────────────────────────────────────────────────────────
def make_britcore_london():
    path = os.path.join(OUTPUT_DIR, "energy_britcore_london_202410.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    s = _styles()
    col = colors.HexColor("#0055A4")
    story = []

    story.append(Paragraph("BritCore Hosting",
                 ParagraphStyle("H", fontName="Helvetica-Bold", fontSize=26, textColor=col)))
    story.append(Paragraph("BritCore Hosting Ltd  —  West London Data Centre", s["Normal"]))
    story.append(Paragraph("12 Whitmore Road, Park Royal, London NW10 7BW, United Kingdom", s["Normal"]))
    story.append(Paragraph("VAT No: GB 345 8765 12  |  billing@britcorehosting.co.uk", s["Normal"]))
    story.append(Spacer(1, 5*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=col))
    story.append(Spacer(1, 4*mm))

    meta = [
        ["TAX INVOICE", ""],
        ["Invoice Number:", "BCH-2024-10-00882"],
        ["Invoice Date:",   "31 October 2024"],
        ["Billing Period:", "October 2024"],
        ["Bill To:", "Westfield Asset Management Ltd\n4 Broadgate, London EC2M 2QS"],
        ["Contract Ref:", "BCH-WAM-2021-0034"],
    ]
    t = Table(meta, colWidths=[50*mm, 120*mm])
    t.setStyle(TableStyle([("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
                            ("FONTSIZE",(0,0),(-1,0),14),
                            ("TEXTCOLOR",(0,0),(-1,0),col),
                            ("BOTTOMPADDING",(0,0),(-1,-1),4),
                            ("VALIGN",(0,0),(-1,-1),"TOP")]))
    story.append(t)
    story.append(Spacer(1, 6*mm))

    story.append(Paragraph("Power Consumption Detail — October 2024", s["B"]))
    story.append(Spacer(1, 2*mm))
    items = [
        ["Description",                        "Unit",   "Qty",       "Rate",           "Amount"],
        ["Metered IT Power Consumption",        "kWh",   "823,450",   "£0.1124/kWh",   "£ 92,555.88"],
        ["PUE Efficiency Uplift (1.385)",        "factor", "—",         "—",             "£ 32,394.56"],
        ["Cross-Connect Ports (×4)",             "port",   "4",         "£120.00/mo",    "£    480.00"],
        ["Remote Hands (2h)",                    "hour",   "2",         "£85.00/h",      "£    170.00"],
    ]
    t2 = Table(items, colWidths=[75*mm, 18*mm, 22*mm, 32*mm, 30*mm])
    t2.setStyle(_table_style(col))
    story.append(t2)
    story.append(Spacer(1, 4*mm))

    totals = [
        ["", "Net Amount:",  "£ 125,600.44"],
        ["", "VAT (20%):",   "£  25,120.09"],
        ["", "Total Due:",   "£ 150,720.53"],
    ]
    t3 = Table(totals, colWidths=[105*mm, 40*mm, 40*mm])
    t3.setStyle(_totals_style())
    story.append(t3)
    story.append(Spacer(1, 5*mm))
    story.append(Paragraph("Actual PUE: 1.385  |  Contracted PUE Cap: 1.45", s["B"]))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("Payment Terms: 30 days — Sort: 40-22-33 | Acc: 12345678", s["Sm"]))

    doc.build(story)
    print(f"  Created: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# 3. Rheintech Rechenzentrum AG — Frankfurt, EUR
# ─────────────────────────────────────────────────────────────────────────────
def make_rheintech_frankfurt():
    path = os.path.join(OUTPUT_DIR, "energy_rheintech_frankfurt_202410.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    s = _styles()
    col = colors.HexColor("#C0392B")
    story = []

    story.append(Paragraph("RHEINTECH",
                 ParagraphStyle("H", fontName="Helvetica-Bold", fontSize=28, textColor=col)))
    story.append(Paragraph("Rheintech Rechenzentrum AG", s["Normal"]))
    story.append(Paragraph("Industriepark Süd 14, 60599 Frankfurt am Main, Deutschland", s["Normal"]))
    story.append(Paragraph("USt-IdNr: DE 312 876 543  |  abrechnung@rheintech-rz.de", s["Normal"]))
    story.append(Spacer(1, 5*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=col))
    story.append(Spacer(1, 4*mm))

    meta = [
        ["RECHNUNG", ""],
        ["Rechnungsnummer:", "RHT-2024-10-01124"],
        ["Rechnungsdatum:",  "31. Oktober 2024"],
        ["Abrechnungszeitraum:", "Oktober 2024"],
        ["Auftraggeber:", "Nordbank Vermögensverwaltung AG\nKaiserstraße 22\n60311 Frankfurt am Main"],
        ["Vertragsnummer:", "RHT-NBV-2022-0077"],
    ]
    t = Table(meta, colWidths=[55*mm, 120*mm])
    t.setStyle(TableStyle([("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
                            ("FONTSIZE",(0,0),(-1,0),14),
                            ("TEXTCOLOR",(0,0),(-1,0),col),
                            ("BOTTOMPADDING",(0,0),(-1,-1),4),
                            ("VALIGN",(0,0),(-1,-1),"TOP")]))
    story.append(t)
    story.append(Spacer(1, 6*mm))

    story.append(Paragraph("Stromverbrauch Oktober 2024", s["B"]))
    story.append(Spacer(1, 2*mm))
    items = [
        ["Leistungsbeschreibung",               "Einheit","Menge",     "Preis",         "Betrag"],
        ["IT-Stromverbrauch (gemessen)",         "kWh",   "1,124,800", "€0.0882/kWh",  "€ 99,207.36"],
        ["PUE-Aufschlag (gemessen: 1.28)",       "Faktor", "—",         "—",            "€ 24,801.84"],
        ["Kühlung & Infrastruktur",              "Pausch.","1",         "€8,200.00",    "€  8,200.00"],
        ["100G Bandbreite Uplink (2 Ports)",     "Port",   "2",         "€950.00/Mo",   "€  1,900.00"],
    ]
    t2 = Table(items, colWidths=[75*mm, 18*mm, 24*mm, 28*mm, 32*mm])
    t2.setStyle(_table_style(col))
    story.append(t2)
    story.append(Spacer(1, 4*mm))

    totals = [
        ["", "Nettobetrag:",     "€ 134,109.20"],
        ["", "MwSt. 19%:",       "€  25,480.75"],
        ["", "Rechnungsbetrag:", "€ 159,589.95"],
    ]
    t3 = Table(totals, colWidths=[105*mm, 40*mm, 40*mm])
    t3.setStyle(_totals_style())
    story.append(t3)
    story.append(Spacer(1, 5*mm))
    story.append(Paragraph("Gemessener PUE: 1.28  |  Vertraglicher PUE-Cap: 1.35", s["B"]))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("Zahlungsziel: 30 Tage netto — IBAN: DE12 5005 0201 0012 3456 78", s["Sm"]))

    doc.build(story)
    print(f"  Created: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# 4. Alpencloud Services AG — Zurich, CHF
# ─────────────────────────────────────────────────────────────────────────────
def make_alpencloud_zurich():
    path = os.path.join(OUTPUT_DIR, "energy_alpencloud_zurich_202410.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    s = _styles()
    col = colors.HexColor("#2E7D32")
    story = []

    story.append(Paragraph("Alpencloud Services",
                 ParagraphStyle("H", fontName="Helvetica-Bold", fontSize=24, textColor=col)))
    story.append(Paragraph("Alpencloud Services AG  —  Rechenzentrum Zürich-West", s["Normal"]))
    story.append(Paragraph("Werkstrasse 88, 8005 Zürich, Schweiz", s["Normal"]))
    story.append(Paragraph("MWST-Nr: CHE-987.654.321 MWST  |  billing@alpencloud.ch", s["Normal"]))
    story.append(Spacer(1, 5*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=col))
    story.append(Spacer(1, 4*mm))

    meta = [
        ["RECHNUNG / INVOICE", ""],
        ["Rechnungsnummer:", "APC-2024-10-00567"],
        ["Datum:",           "31. Oktober 2024"],
        ["Abrechnungsperiode:", "Oktober 2024"],
        ["Auftraggeber:", "Helvetia Finanzgruppe AG\nParadeplatz 4\n8001 Zürich, Schweiz"],
        ["Referenz:", "APC-HFG-2021-0088"],
    ]
    t = Table(meta, colWidths=[55*mm, 120*mm])
    t.setStyle(TableStyle([("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
                            ("FONTSIZE",(0,0),(-1,0),14),
                            ("TEXTCOLOR",(0,0),(-1,0),col),
                            ("BOTTOMPADDING",(0,0),(-1,-1),4),
                            ("VALIGN",(0,0),(-1,-1),"TOP")]))
    story.append(t)
    story.append(Spacer(1, 6*mm))

    story.append(Paragraph("Stromverbrauch / Power Consumption — Oktober 2024", s["B"]))
    story.append(Spacer(1, 2*mm))
    items = [
        ["Beschreibung",                        "Einheit","Menge",    "Tarif",           "Betrag CHF"],
        ["Gemessener IT-Stromverbrauch",         "kWh",   "654,200",  "CHF 0.1450/kWh", "CHF 94,859.00"],
        ["PUE-Koeffizient (1.22)",               "Faktor", "—",        "—",              "CHF 20,869.98"],
        ["Klimatisierung & Facility",            "Pausch.","1",        "CHF 6,800.00",   "CHF  6,800.00"],
        ["Managed NOC Service (24/7)",           "Pausch.","1",        "CHF 2,400.00",   "CHF  2,400.00"],
    ]
    t2 = Table(items, colWidths=[73*mm, 18*mm, 22*mm, 34*mm, 32*mm])
    t2.setStyle(_table_style(col))
    story.append(t2)
    story.append(Spacer(1, 4*mm))

    totals = [
        ["", "Nettobetrag:",    "CHF 124,928.98"],
        ["", "MWST 8.1%:",      "CHF  10,119.25"],
        ["", "Rechnungstotal:", "CHF 135,048.23"],
    ]
    t3 = Table(totals, colWidths=[105*mm, 40*mm, 40*mm])
    t3.setStyle(_totals_style())
    story.append(t3)
    story.append(Spacer(1, 5*mm))
    story.append(Paragraph("Gemessener PUE: 1.22  |  Vertraglicher PUE-Cap: 1.30", s["B"]))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("Zahlungsfrist: 30 Tage — IBAN: CH93 0076 2011 6238 5295 7", s["Sm"]))

    doc.build(story)
    print(f"  Created: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# 5. Deltanode BV — Amsterdam, EUR
# ─────────────────────────────────────────────────────────────────────────────
def make_deltanode_amsterdam():
    path = os.path.join(OUTPUT_DIR, "energy_deltanode_amsterdam_202411.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    s = _styles()
    col = colors.HexColor("#E65100")
    story = []

    story.append(Paragraph("DELTANODE",
                 ParagraphStyle("H", fontName="Helvetica-Bold", fontSize=28, textColor=col)))
    story.append(Paragraph("Deltanode BV  —  Datacentrum Amsterdam Noord", s["Normal"]))
    story.append(Paragraph("Asterweg 20, 1031 HN Amsterdam, Nederland", s["Normal"]))
    story.append(Paragraph("BTW-nummer: NL 654 321 987 B01  |  facturatie@deltanode.nl", s["Normal"]))
    story.append(Spacer(1, 5*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=col))
    story.append(Spacer(1, 4*mm))

    meta = [
        ["FACTUUR / INVOICE", ""],
        ["Factuurnummer:", "DNO-2024-11-00334"],
        ["Factuurdatum:",  "29 november 2024"],
        ["Factureringsperiode:", "November 2024"],
        ["Klant:", "Polderwerk Investments BV\nKeizersgracht 312\n1016 EX Amsterdam"],
        ["Contract:", "DNO-PWI-2023-0019"],
    ]
    t = Table(meta, colWidths=[55*mm, 120*mm])
    t.setStyle(TableStyle([("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
                            ("FONTSIZE",(0,0),(-1,0),14),
                            ("TEXTCOLOR",(0,0),(-1,0),col),
                            ("BOTTOMPADDING",(0,0),(-1,-1),4),
                            ("VALIGN",(0,0),(-1,-1),"TOP")]))
    story.append(t)
    story.append(Spacer(1, 6*mm))

    story.append(Paragraph("Stroomverbruik / Power Consumption — November 2024", s["B"]))
    story.append(Spacer(1, 2*mm))
    items = [
        ["Omschrijving",                         "Eenheid","Hoeveelheid","Tarief",        "Bedrag"],
        ["IT-stroomverbruik (gemeten)",           "kWh",   "987,320",   "€0.0945/kWh",  "€ 93,302.04"],
        ["PUE-toeslag (gemeten PUE: 1.31)",       "factor", "—",         "—",            "€ 28,923.63"],
        ["Koeling & facilitaire kosten",          "vast",   "1",         "€9,500.00",    "€  9,500.00"],
        ["Connectiviteit 2×10G",                  "poort",  "2",         "€780.00/mnd",  "€  1,560.00"],
    ]
    t2 = Table(items, colWidths=[73*mm, 18*mm, 25*mm, 30*mm, 31*mm])
    t2.setStyle(_table_style(col))
    story.append(t2)
    story.append(Spacer(1, 4*mm))

    totals = [
        ["", "Subtotaal excl. BTW:", "€ 133,285.67"],
        ["", "BTW 21%:",             "€  27,989.99"],
        ["", "Totaal te betalen:",   "€ 161,275.66"],
    ]
    t3 = Table(totals, colWidths=[105*mm, 42*mm, 38*mm])
    t3.setStyle(_totals_style())
    story.append(t3)
    story.append(Spacer(1, 5*mm))
    story.append(Paragraph("Gemeten PUE: 1.31  |  Contractuele PUE-cap: 1.40", s["B"]))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("Betaaltermijn: 30 dagen — IBAN: NL12 ABNA 0123 4567 89", s["Sm"]))

    doc.build(story)
    print(f"  Created: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# 6. Severn Digital Facilities Ltd — London, GBP
# ─────────────────────────────────────────────────────────────────────────────
def make_severn_london():
    path = os.path.join(OUTPUT_DIR, "energy_severn_london_202411.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    s = _styles()
    col = colors.HexColor("#37474F")
    story = []

    story.append(Paragraph("Severn Digital Facilities",
                 ParagraphStyle("H", fontName="Helvetica-Bold", fontSize=22, textColor=col)))
    story.append(Paragraph("Severn Digital Facilities Ltd  —  East London Data Centre", s["Normal"]))
    story.append(Paragraph("Unit 8, Cody Technology Park, Farnborough GU14 0LX, United Kingdom", s["Normal"]))
    story.append(Paragraph("VAT No: GB 211 4567 89  |  accounts@severndigital.co.uk", s["Normal"]))
    story.append(Spacer(1, 5*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=col))
    story.append(Spacer(1, 4*mm))

    meta = [
        ["INVOICE", ""],
        ["Invoice Number:", "SDF-2024-11-01045"],
        ["Invoice Date:",   "30 November 2024"],
        ["Service Period:", "November 2024"],
        ["Customer:", "Chandler & Webb Asset Management PLC\n30 St Mary Axe\nLondon EC3A 8BF"],
        ["Service Agreement:", "SDF-CWA-2022-0051"],
    ]
    t = Table(meta, colWidths=[50*mm, 120*mm])
    t.setStyle(TableStyle([("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
                            ("FONTSIZE",(0,0),(-1,0),14),
                            ("TEXTCOLOR",(0,0),(-1,0),col),
                            ("BOTTOMPADDING",(0,0),(-1,-1),4),
                            ("VALIGN",(0,0),(-1,-1),"TOP")]))
    story.append(t)
    story.append(Spacer(1, 6*mm))

    story.append(Paragraph("Power & Facilities Charges — November 2024", s["B"]))
    story.append(Spacer(1, 2*mm))
    items = [
        ["Description",                         "Unit",   "Quantity",  "Rate",           "Amount"],
        ["Power Consumption (metered)",          "kWh",   "1,203,750", "£0.1056/kWh",   "£127,116.00"],
        ["PUE Efficiency Factor (1.41)",         "factor", "—",         "—",             "£ 52,118.56"],
        ["Colocation Rack Rental (×8)",          "rack",   "8",         "£1,200.00/mo",  "£  9,600.00"],
        ["Resilience & UPS Maintenance",         "fixed",  "1",         "£3,500.00",     "£  3,500.00"],
    ]
    t2 = Table(items, colWidths=[73*mm, 18*mm, 24*mm, 32*mm, 30*mm])
    t2.setStyle(_table_style(col))
    story.append(t2)
    story.append(Spacer(1, 4*mm))

    totals = [
        ["", "Subtotal (excl. VAT):", "£ 192,334.56"],
        ["", "VAT (20%):",            "£  38,466.91"],
        ["", "Total Due:",            "£ 230,801.47"],
    ]
    t3 = Table(totals, colWidths=[105*mm, 42*mm, 38*mm])
    t3.setStyle(_totals_style())
    story.append(t3)
    story.append(Spacer(1, 5*mm))
    story.append(Paragraph("Actual PUE: 1.41  |  Contracted PUE Cap: 1.50", s["B"]))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("Payment Terms: 30 days net — Sort: 20-44-55 | Acc: 87654321", s["Sm"]))

    doc.build(story)
    print(f"  Created: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Generating fictional energy invoices → {OUTPUT_DIR}/\n")

    make_nexova_paris()
    make_britcore_london()
    make_rheintech_frankfurt()
    make_alpencloud_zurich()
    make_deltanode_amsterdam()
    make_severn_london()

    files = [f for f in os.listdir(OUTPUT_DIR) if f.startswith("energy_")]
    print(f"\n✅ {len(files)} energy invoice files generated:")
    for f in sorted(files):
        size = os.path.getsize(os.path.join(OUTPUT_DIR, f))
        print(f"   {f:55s}  {size/1024:.0f} KB")
