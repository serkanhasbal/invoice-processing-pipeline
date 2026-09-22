"""
Energy Invoice Generator
-------------------------
Generates synthetic colocation/power invoices from different providers.
All data is completely fictional — no real invoices used.

Providers simulated:
  1. Equinix (Paris, FR)     — EUR, French data centre
  2. Digital Realty (London) — GBP, UK data centre
  3. CyrusOne (Frankfurt)    — EUR, German data centre
  4. NTT (Zurich)            — CHF, Swiss data centre
  5. Vantage (Amsterdam)     — EUR, Dutch data centre
  6. Iron Mountain (London)  — GBP, UK data centre

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
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_invoices")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle("R",   parent=s["Normal"], alignment=TA_RIGHT))
    s.add(ParagraphStyle("C",   parent=s["Normal"], alignment=TA_CENTER))
    s.add(ParagraphStyle("B",   parent=s["Normal"], fontName="Helvetica-Bold"))
    s.add(ParagraphStyle("T",   parent=s["Normal"], fontName="Helvetica-Bold", fontSize=20))
    s.add(ParagraphStyle("Sm",  parent=s["Normal"], fontSize=8))
    s.add(ParagraphStyle("SmR", parent=s["Normal"], fontSize=8, alignment=TA_RIGHT))
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


# ─────────────────────────────────────────────────────────────────────────────
# 1. Equinix Paris — EUR
# ─────────────────────────────────────────────────────────────────────────────
def make_equinix_paris():
    path = os.path.join(OUTPUT_DIR, "energy_equinix_paris_PA13_202409.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    s = _styles()
    col = colors.HexColor("#003087")  # Equinix blue
    story = []

    story.append(Paragraph("EQUINIX", ParagraphStyle("EQ", fontName="Helvetica-Bold",
                 fontSize=28, textColor=col)))
    story.append(Paragraph("Equinix Hyperscale 2 (PA13) SAS", s["Normal"]))
    story.append(Paragraph("114 Rue Ambroise Croizat, 93200 Saint-Denis, France", s["Normal"]))
    story.append(Paragraph("TVA Intra: FR 76 432 876 543  |  billing@equinix.com", s["Normal"]))
    story.append(Spacer(1, 5*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=col))
    story.append(Spacer(1, 4*mm))

    meta = [
        ["FACTURE / INVOICE", ""],
        ["Numéro de facture:", "372220000016"],
        ["Date de facture:",   "25 octobre 2024"],
        ["Période de facturation:", "Octobre 2024"],
        ["Client:", "GlobalTech Solutions SAS\n12 Avenue des Champs-Élysées\n75008 Paris, France"],
        ["Contrat:", "IBX-PA13-2019-00892"],
    ]
    t = Table(meta, colWidths=[55*mm, 120*mm])
    t.setStyle(TableStyle([("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
                            ("FONTSIZE",(0,0),(-1,0),14),
                            ("TEXTCOLOR",(0,0),(-1,0),col),
                            ("BOTTOMPADDING",(0,0),(-1,-1),4),
                            ("VALIGN",(0,0),(-1,-1),"TOP")]))
    story.append(t)
    story.append(Spacer(1, 6*mm))

    story.append(Paragraph("Détail de la consommation électrique", s["B"]))
    story.append(Spacer(1, 2*mm))
    items = [
        ["Description",                          "Unité",  "Quantité",   "Tarif",         "Montant HT"],
        ["Consommation électrique — Octobre 2024","kWh",   "1,947,094",  "€0.09175/kWh",  "€178,682.37"],
        ["Majoration PUE (1.302)",                "factor", "—",          "—",             "€ 55,164.97"],
        ["Refroidissement & Infrastructure",      "forfait","1",          "€12,500.00",    "€ 12,500.00"],
        ["Remote Hands (4h)",                     "heure",  "4",          "€95.00/h",      "€    380.00"],
    ]
    t2 = Table(items, colWidths=[75*mm, 18*mm, 24*mm, 30*mm, 30*mm])
    t2.setStyle(_table_style(col))
    story.append(t2)
    story.append(Spacer(1, 4*mm))

    totals = [
        ["", "Sous-total HT:",    "€ 246,727.34"],
        ["", "TVA 20%:",          "€  49,345.47"],
        ["", "TOTAL TTC:",        "€ 296,072.81"],
    ]
    t3 = Table(totals, colWidths=[105*mm, 40*mm, 40*mm])
    t3.setStyle(TableStyle([("ALIGN",(1,0),(-1,-1),"RIGHT"),
                             ("FONTNAME",(1,2),(-1,2),"Helvetica-Bold"),
                             ("FONTSIZE",(1,2),(-1,2),11),
                             ("LINEABOVE",(1,2),(-1,2),1,colors.black),
                             ("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    story.append(t3)
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph("PUE Réel: 1.302  |  PUE Contractuel Maximum: 1.50", s["B"]))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("Échéance: 30 jours — IBAN: FR76 3000 6000 0112 3456 7890 189", s["Sm"]))

    doc.build(story)
    print(f"  Created: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# 2. Digital Realty London — GBP
# ─────────────────────────────────────────────────────────────────────────────
def make_digital_realty_london():
    path = os.path.join(OUTPUT_DIR, "energy_digitalrealty_london_LHR8_202410.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    s = _styles()
    col = colors.HexColor("#0066CC")
    story = []

    story.append(Paragraph("Digital Realty", ParagraphStyle("DR", fontName="Helvetica-Bold",
                 fontSize=24, textColor=col)))
    story.append(Paragraph("Digital Realty Trust UK Limited  —  LHR8 Data Centre", s["Normal"]))
    story.append(Paragraph("Buckingham Avenue, Slough SL1 4NB, United Kingdom", s["Normal"]))
    story.append(Paragraph("VAT No: GB 294 7654 32  |  invoicing@digitalrealty.com", s["Normal"]))
    story.append(Spacer(1, 5*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=col))
    story.append(Spacer(1, 4*mm))

    meta = [
        ["TAX INVOICE", ""],
        ["Invoice Number:", "DR-LHR8-2024-10-00441"],
        ["Invoice Date:",   "31 October 2024"],
        ["Billing Period:", "October 2024"],
        ["Bill To:", "Meridian Capital Management Ltd\n1 Canada Square, Canary Wharf\nLondon E14 5AB"],
        ["Contract Ref:", "LHR8-CAB-0044-A"],
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
        ["Description",                         "Unit",    "Qty",        "Rate",           "Amount"],
        ["IT Power Consumption",                 "kWh",    "823,450",    "£0.1124/kWh",    "£92,555.88"],
        ["PUE Uplift (measured PUE: 1.385)",     "factor",  "—",          "—",             "£32,394.56"],
        ["Cross Connect — 10GbE (×4)",           "port",    "4",          "£120.00/mo",    "£   480.00"],
        ["Remote Hands Standard (2h)",           "hour",    "2",          "£85.00/h",      "£   170.00"],
    ]
    t2 = Table(items, colWidths=[75*mm, 18*mm, 22*mm, 32*mm, 30*mm])
    t2.setStyle(_table_style(col))
    story.append(t2)
    story.append(Spacer(1, 4*mm))

    totals = [
        ["", "Net Amount:",    "£ 125,600.44"],
        ["", "VAT (20%):",     "£  25,120.09"],
        ["", "Total Due:",     "£ 150,720.53"],
    ]
    t3 = Table(totals, colWidths=[105*mm, 40*mm, 40*mm])
    t3.setStyle(TableStyle([("ALIGN",(1,0),(-1,-1),"RIGHT"),
                             ("FONTNAME",(1,2),(-1,2),"Helvetica-Bold"),
                             ("FONTSIZE",(1,2),(-1,2),11),
                             ("LINEABOVE",(1,2),(-1,2),1,colors.black),
                             ("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    story.append(t3)
    story.append(Spacer(1, 5*mm))
    story.append(Paragraph("Actual PUE: 1.385  |  Contracted PUE Cap: 1.45", s["B"]))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("Payment: 30 days net — Sort: 60-00-01 | Acc: 31926819", s["Sm"]))

    doc.build(story)
    print(f"  Created: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# 3. CyrusOne Frankfurt — EUR
# ─────────────────────────────────────────────────────────────────────────────
def make_cyrusone_frankfurt():
    path = os.path.join(OUTPUT_DIR, "energy_cyrusone_frankfurt_FRA1_202410.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    s = _styles()
    col = colors.HexColor("#E31837")
    story = []

    story.append(Paragraph("CyrusOne", ParagraphStyle("CO", fontName="Helvetica-Bold",
                 fontSize=26, textColor=col)))
    story.append(Paragraph("CyrusOne GmbH  —  Rechenzentrum Frankfurt FRA1", s["Normal"]))
    story.append(Paragraph("Grenzstraße 28, 65933 Frankfurt am Main, Deutschland", s["Normal"]))
    story.append(Paragraph("USt-IdNr: DE 298 765 432  |  billing-eu@cyrusone.com", s["Normal"]))
    story.append(Spacer(1, 5*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=col))
    story.append(Spacer(1, 4*mm))

    meta = [
        ["RECHNUNG", ""],
        ["Rechnungsnummer:", "CO-FRA1-2024-10-0887"],
        ["Rechnungsdatum:",  "31. Oktober 2024"],
        ["Abrechnungszeitraum:", "Oktober 2024"],
        ["Auftraggeber:", "Nexus Financial AG\nTaunusanlage 12\n60325 Frankfurt am Main"],
        ["Vertragsnummer:", "FRA1-2022-0091"],
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
        ["Leistungsbeschreibung",               "Einheit", "Menge",      "Preis",          "Betrag"],
        ["IT-Stromverbrauch",                    "kWh",    "1,124,800",  "€0.0882/kWh",   "€ 99,207.36"],
        ["PUE-Aufschlag (gemessener PUE: 1.28)", "Faktor",  "—",          "—",             "€ 24,801.84"],
        ["Kühlung & Infrastruktur",              "Pausch.", "1",          "€8,200.00",     "€  8,200.00"],
        ["Bandbreite 100G Uplink (2×)",          "Port",    "2",          "€950.00/Mo",    "€  1,900.00"],
    ]
    t2 = Table(items, colWidths=[75*mm, 18*mm, 24*mm, 28*mm, 32*mm])
    t2.setStyle(_table_style(col))
    story.append(t2)
    story.append(Spacer(1, 4*mm))

    totals = [
        ["", "Nettobetrag:",    "€ 134,109.20"],
        ["", "MwSt. 19%:",     "€  25,480.75"],
        ["", "Rechnungsbetrag:", "€ 159,589.95"],
    ]
    t3 = Table(totals, colWidths=[105*mm, 40*mm, 40*mm])
    t3.setStyle(TableStyle([("ALIGN",(1,0),(-1,-1),"RIGHT"),
                             ("FONTNAME",(1,2),(-1,2),"Helvetica-Bold"),
                             ("FONTSIZE",(1,2),(-1,2),11),
                             ("LINEABOVE",(1,2),(-1,2),1,colors.black),
                             ("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    story.append(t3)
    story.append(Spacer(1, 5*mm))
    story.append(Paragraph("Gemessener PUE: 1.28  |  Vertraglicher PUE-Cap: 1.35", s["B"]))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("Zahlungsziel: 30 Tage netto — IBAN: DE89 3704 0044 0532 0130 00", s["Sm"]))

    doc.build(story)
    print(f"  Created: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# 4. NTT Zurich — CHF
# ─────────────────────────────────────────────────────────────────────────────
def make_ntt_zurich():
    path = os.path.join(OUTPUT_DIR, "energy_ntt_zurich_ZRH1_202410.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    s = _styles()
    col = colors.HexColor("#009B77")
    story = []

    story.append(Paragraph("NTT Global Data Centers", ParagraphStyle("NTT", fontName="Helvetica-Bold",
                 fontSize=20, textColor=col)))
    story.append(Paragraph("NTT Ltd. Switzerland AG  —  ZRH1 Zürich", s["Normal"]))
    story.append(Paragraph("Hardturmstrasse 253, 8005 Zürich, Schweiz", s["Normal"]))
    story.append(Paragraph("MWST-Nr: CHE-456.123.789 MWST  |  billing.ch@ntt.com", s["Normal"]))
    story.append(Spacer(1, 5*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=col))
    story.append(Spacer(1, 4*mm))

    meta = [
        ["RECHNUNG / INVOICE", ""],
        ["Rechnungsnummer:", "NTT-ZRH1-2024-10-0234"],
        ["Datum:", "31. Oktober 2024"],
        ["Abrechnungsperiode:", "Oktober 2024"],
        ["Auftraggeber:", "Swiss Banking Partners AG\nBahnhofstrasse 10\n8001 Zürich, Schweiz"],
        ["Referenz:", "ZRH1-SBP-2021-0044"],
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
        ["Beschreibung",                          "Einheit", "Menge",     "Tarif",          "Betrag CHF"],
        ["Stromverbrauch IT-Lasten",               "kWh",    "654,200",   "CHF 0.1450/kWh", "CHF 94,859.00"],
        ["PUE-Koeffizient (1.22)",                 "Faktor",  "—",         "—",              "CHF 20,869.98"],
        ["Klimatisierung & Facility",              "Pausch.", "1",         "CHF 6,800.00",   "CHF  6,800.00"],
        ["Managed NOC Service (24/7)",             "Pausch.", "1",         "CHF 2,400.00",   "CHF  2,400.00"],
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
    t3.setStyle(TableStyle([("ALIGN",(1,0),(-1,-1),"RIGHT"),
                             ("FONTNAME",(1,2),(-1,2),"Helvetica-Bold"),
                             ("FONTSIZE",(1,2),(-1,2),11),
                             ("LINEABOVE",(1,2),(-1,2),1,colors.black),
                             ("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    story.append(t3)
    story.append(Spacer(1, 5*mm))
    story.append(Paragraph("Gemessener PUE: 1.22  |  Vertraglicher PUE-Cap: 1.30", s["B"]))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("Zahlungsfrist: 30 Tage  —  IBAN: CH56 0483 5012 3456 7800 9", s["Sm"]))

    doc.build(story)
    print(f"  Created: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# 5. Vantage Amsterdam — EUR
# ─────────────────────────────────────────────────────────────────────────────
def make_vantage_amsterdam():
    path = os.path.join(OUTPUT_DIR, "energy_vantage_amsterdam_AMS1_202411.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    s = _styles()
    col = colors.HexColor("#FF6B00")
    story = []

    story.append(Paragraph("Vantage Data Centers", ParagraphStyle("VDC", fontName="Helvetica-Bold",
                 fontSize=22, textColor=col)))
    story.append(Paragraph("Vantage DC Netherlands B.V.  —  AMS1 Amsterdam", s["Normal"]))
    story.append(Paragraph("Gyroscoopweg 50, 1042 AX Amsterdam, Netherlands", s["Normal"]))
    story.append(Paragraph("BTW-nummer: NL 863 452 917 B01  |  billing@vantagedc.com", s["Normal"]))
    story.append(Spacer(1, 5*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=col))
    story.append(Spacer(1, 4*mm))

    meta = [
        ["FACTUUR / INVOICE", ""],
        ["Factuurnummer:", "VDC-AMS1-2024-11-0556"],
        ["Factuurdatum:",  "28 november 2024"],
        ["Factureringsperiode:", "November 2024"],
        ["Klant:", "Amsterdam Trading House B.V.\nHerengracht 420\n1017 BZ Amsterdam"],
        ["Contract:", "AMS1-ATH-2023-0017"],
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
        ["Omschrijving",                          "Eenheid","Hoeveelheid", "Tarief",         "Bedrag"],
        ["IT-stroomverbruik",                     "kWh",    "987,320",    "€0.0945/kWh",    "€ 93,302.04"],
        ["PUE-toeslag (gemeten PUE: 1.31)",       "factor",  "—",          "—",             "€ 28,923.63"],
        ["Koeling & facilitaire kosten",          "vast",    "1",          "€9,500.00",     "€  9,500.00"],
        ["Beveiligde connectiviteit (2×10G)",     "poort",   "2",          "€780.00/mnd",   "€  1,560.00"],
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
    t3.setStyle(TableStyle([("ALIGN",(1,0),(-1,-1),"RIGHT"),
                             ("FONTNAME",(1,2),(-1,2),"Helvetica-Bold"),
                             ("FONTSIZE",(1,2),(-1,2),11),
                             ("LINEABOVE",(1,2),(-1,2),1,colors.black),
                             ("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    story.append(t3)
    story.append(Spacer(1, 5*mm))
    story.append(Paragraph("Gemeten PUE: 1.31  |  Contractuele PUE-cap: 1.40", s["B"]))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("Betaaltermijn: 30 dagen — IBAN: NL91 ABNA 0417 1643 00", s["Sm"]))

    doc.build(story)
    print(f"  Created: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# 6. Iron Mountain London — GBP
# ─────────────────────────────────────────────────────────────────────────────
def make_iron_mountain_london():
    path = os.path.join(OUTPUT_DIR, "energy_ironmountain_london_LON2_202411.pdf")
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    s = _styles()
    col = colors.HexColor("#C41230")
    story = []

    story.append(Paragraph("Iron Mountain", ParagraphStyle("IM", fontName="Helvetica-Bold",
                 fontSize=24, textColor=col)))
    story.append(Paragraph("Iron Mountain Data Centres Ltd  —  LON2 London", s["Normal"]))
    story.append(Paragraph("3 Comer Business and Innovation Centre, London NW9 6BX", s["Normal"]))
    story.append(Paragraph("VAT No: GB 189 3421 56  |  datacenter-billing@ironmountain.com", s["Normal"]))
    story.append(Spacer(1, 5*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=col))
    story.append(Spacer(1, 4*mm))

    meta = [
        ["INVOICE", ""],
        ["Invoice Number:", "IM-LON2-2024-11-00892"],
        ["Invoice Date:",   "30 November 2024"],
        ["Service Period:", "November 2024"],
        ["Customer:", "Hargreaves Asset Management PLC\n250 Bishopsgate\nLondon EC2M 4AA"],
        ["Service Agreement:", "LON2-HAM-2022-SA-0043"],
    ]
    t = Table(meta, colWidths=[50*mm, 120*mm])
    t.setStyle(TableStyle([("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
                            ("FONTSIZE",(0,0),(-1,0),14),
                            ("TEXTCOLOR",(0,0),(-1,0),col),
                            ("BOTTOMPADDING",(0,0),(-1,-1),4),
                            ("VALIGN",(0,0),(-1,-1),"TOP")]))
    story.append(t)
    story.append(Spacer(1, 6*mm))

    story.append(Paragraph("Power & Facilities — November 2024", s["B"]))
    story.append(Spacer(1, 2*mm))
    items = [
        ["Description",                          "Unit",    "Quantity",   "Rate",           "Amount"],
        ["Power Consumption (metered)",           "kWh",    "1,203,750",  "£0.1056/kWh",   "£127,116.00"],
        ["PUE Efficiency Factor (1.41)",          "factor",  "—",          "—",             "£ 52,118.56"],
        ["Colocation Rack Rental (×8)",           "rack",    "8",          "£1,200.00/mo",  "£  9,600.00"],
        ["Resilience & UPS Maintenance",          "fixed",   "1",          "£3,500.00",     "£  3,500.00"],
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
    t3.setStyle(TableStyle([("ALIGN",(1,0),(-1,-1),"RIGHT"),
                             ("FONTNAME",(1,2),(-1,2),"Helvetica-Bold"),
                             ("FONTSIZE",(1,2),(-1,2),11),
                             ("LINEABOVE",(1,2),(-1,2),1,colors.black),
                             ("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    story.append(t3)
    story.append(Spacer(1, 5*mm))
    story.append(Paragraph("Actual PUE: 1.41  |  Contracted PUE Cap: 1.50", s["B"]))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("Payment Terms: 30 days net — Sort: 40-47-84 | Acc: 00128654", s["Sm"]))

    doc.build(story)
    print(f"  Created: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Generating energy invoices → {OUTPUT_DIR}/\n")

    make_equinix_paris()
    make_digital_realty_london()
    make_cyrusone_frankfurt()
    make_ntt_zurich()
    make_vantage_amsterdam()
    make_iron_mountain_london()

    files = [f for f in os.listdir(OUTPUT_DIR) if f.startswith("energy_")]
    print(f"\n✅ {len(files)} energy invoice files generated:")
    for f in sorted(files):
        size = os.path.getsize(os.path.join(OUTPUT_DIR, f))
        print(f"   {f:55s}  {size/1024:.0f} KB")
