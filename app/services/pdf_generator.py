import math
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas


BRAND_BLUE = HexColor("#1e40af")
BRAND_BLUE_LIGHT = HexColor("#3b82f6")
GREEN = HexColor("#22c55e")
GREEN_DARK = HexColor("#15803d")
RED = HexColor("#ef4444")
RED_DARK = HexColor("#dc2626")
BLUE = HexColor("#3b82f6")
BLUE_DARK = HexColor("#1d4ed8")
GRAY = HexColor("#6b7280")
GRAY_LIGHT = HexColor("#f3f4f6")
DARK = HexColor("#1f2937")

PAGE_W, PAGE_H = letter
MARGIN = 0.75 * inch


def _draw_header(c, client_name, date_str, title):
    c.setFillColor(BRAND_BLUE)
    c.rect(0, PAGE_H - 60, PAGE_W, 60, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(MARGIN, PAGE_H - 38, title)
    c.setFont("Helvetica", 10)
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - 28, client_name)
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - 42, date_str)


def _draw_currency(c, x, y, amount, font_size=12, color=DARK, bold=True):
    text = f"${amount:,.0f}"
    font = "Helvetica-Bold" if bold else "Helvetica"
    c.setFillColor(color)
    c.setFont(font, font_size)
    c.drawCentredString(x, y, text)


def _draw_bubble(c, x, y, radius, label, amount, fill_color, text_color=white):
    c.setFillColor(fill_color)
    c.circle(x, y, radius, fill=1, stroke=0)
    c.setFillColor(text_color)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(x, y + 10, label)
    c.setFont("Helvetica-Bold", 14)
    _draw_currency(c, x, y - 10, amount, font_size=14, color=text_color)


def _draw_arrow(c, x1, y1, x2, y2, color=DARK, label=None):
    c.setStrokeColor(color)
    c.setLineWidth(2)
    c.line(x1, y1, x2, y2)
    # Arrowhead
    angle = math.atan2(y2 - y1, x2 - x1)
    arrow_len = 10
    c.setFillColor(color)
    p = c.beginPath()
    p.moveTo(x2, y2)
    p.lineTo(x2 - arrow_len * math.cos(angle - 0.4), y2 - arrow_len * math.sin(angle - 0.4))
    p.lineTo(x2 - arrow_len * math.cos(angle + 0.4), y2 - arrow_len * math.sin(angle + 0.4))
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        c.setFillColor(color)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(mx, my + 12, label)


def generate_sacs_pdf(filepath, report_data, entries_by_account, entries_by_label, report):
    c = canvas.Canvas(filepath, pagesize=letter)

    client_name = report_data["primary"].full_name if report_data["primary"] else ""
    if report_data["spouse"]:
        client_name += f" & {report_data['spouse'].full_name}"
    date_str = report.generated_at.strftime("%B %d, %Y")

    # Page 1: Cashflow Diagram
    _draw_header(c, client_name, date_str, "Simple Automated Cash Flow System (SACS)")

    sacs = report_data["sacs"]
    cx = PAGE_W / 2

    # Inflow bubble (left)
    inflow_y = PAGE_H - 220
    _draw_bubble(c, cx - 180, inflow_y, 55, "MONTHLY INFLOW", sacs["inflow"], GREEN, white)

    # Outflow bubble (right)
    outflow_y = PAGE_H - 220
    _draw_bubble(c, cx + 180, outflow_y, 55, "MONTHLY OUTFLOW", sacs["outflow"], RED, white)

    # Arrow: Inflow → Outflow with X
    _draw_arrow(c, cx - 125, inflow_y, cx + 125, outflow_y, RED_DARK)
    c.setFillColor(RED_DARK)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(cx, inflow_y + 5, "X")

    # Private Reserve bubble (bottom center)
    pr_y = PAGE_H - 380
    _draw_bubble(c, cx, pr_y, 60, "PRIVATE RESERVE", sacs["excess"], BLUE_DARK, white)

    # Arrow: Outflow → Private Reserve
    _draw_arrow(c, cx + 180, outflow_y - 55, cx + 40, pr_y + 60, BLUE, "EXCESS")

    # Summary box
    box_y = PAGE_H - 520
    c.setFillColor(GRAY_LIGHT)
    c.roundRect(MARGIN + 20, box_y - 80, PAGE_W - 2 * MARGIN - 40, 80, 8, fill=1, stroke=0)

    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(MARGIN + 40, box_y - 25, "Monthly Summary")
    c.setFont("Helvetica", 10)
    c.drawString(MARGIN + 40, box_y - 45, f"Inflow: ${sacs['inflow']:,.0f}   |   Outflow: ${sacs['outflow']:,.0f}   |   Excess to Private Reserve: ${sacs['excess']:,.0f}")
    c.drawString(MARGIN + 40, box_y - 62, f"Private Reserve Target: ${sacs['private_reserve_target']:,.0f}")

    # Footer
    c.setFillColor(GRAY)
    c.setFont("Helvetica", 8)
    c.drawCentredString(PAGE_W / 2, 30, "EF Financial Planning — Windbrook Solutions")

    c.showPage()

    # Page 2: Private Reserve Details
    _draw_header(c, client_name, date_str, "SACS — Private Reserve Details")

    pr_balance = entries_by_label.get("Private Reserve Balance", 0)
    inv_balance = entries_by_label.get("Investment Account Balance", 0)

    y = PAGE_H - 120
    items = [
        ("Private Reserve Balance", pr_balance),
        ("Investment Account Balance", inv_balance),
        ("Monthly Excess (to Private Reserve)", sacs["excess"]),
        ("Private Reserve Target", sacs["private_reserve_target"]),
    ]

    for label, amount in items:
        c.setFillColor(GRAY_LIGHT)
        c.roundRect(MARGIN + 20, y - 30, PAGE_W - 2 * MARGIN - 40, 35, 6, fill=1, stroke=0)
        c.setFillColor(DARK)
        c.setFont("Helvetica", 11)
        c.drawString(MARGIN + 35, y - 17, label)
        c.setFont("Helvetica-Bold", 11)
        c.drawRightString(PAGE_W - MARGIN - 35, y - 17, f"${amount:,.0f}")
        y -= 50

    c.setFillColor(GRAY)
    c.setFont("Helvetica", 8)
    c.drawCentredString(PAGE_W / 2, 30, "EF Financial Planning — Windbrook Solutions")

    c.save()


def generate_tcc_pdf(filepath, report_data, entries_by_account, entries_by_label, report):
    c = canvas.Canvas(filepath, pagesize=letter)

    client_name = report_data["primary"].full_name if report_data["primary"] else ""
    if report_data["spouse"]:
        client_name += f" & {report_data['spouse'].full_name}"
    date_str = report.generated_at.strftime("%B %d, %Y")

    _draw_header(c, client_name, date_str, "Total Client Chart (TCC)")

    accounts = report_data["accounts"]
    liabilities = report_data["liabilities"]

    # Separate accounts by type and owner
    client1_ret = [a for a in accounts if a["account_type"] == "retirement" and a["owner"] != "client2"]
    client2_ret = [a for a in accounts if a["account_type"] == "retirement" and a["owner"] == "client2"]
    non_ret = [a for a in accounts if a["account_type"] == "non_retirement"]
    trust_accs = [a for a in accounts if a["account_type"] == "trust"]

    # Client info section
    y = PAGE_H - 90
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(DARK)

    # Client 1 info bubble
    if report_data["primary"]:
        p = report_data["primary"]
        info = f"{p.full_name}"
        if p.age:
            info += f"  |  Age: {p.age}"
        if p.dob:
            info += f"  |  DOB: {p.dob.strftime('%m/%d/%Y')}"
        if p.ssn_last4:
            info += f"  |  SSN: ***{p.ssn_last4}"
        c.setFillColor(HexColor("#dcfce7"))
        c.roundRect(MARGIN, y - 10, PAGE_W - 2 * MARGIN, 25, 6, fill=1, stroke=0)
        c.setFillColor(GREEN_DARK)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(MARGIN + 10, y - 2, info)
        y -= 35

    # Client 2 info bubble
    if report_data["spouse"]:
        s = report_data["spouse"]
        info = f"{s.full_name}"
        if s.age:
            info += f"  |  Age: {s.age}"
        if s.dob:
            info += f"  |  DOB: {s.dob.strftime('%m/%d/%Y')}"
        if s.ssn_last4:
            info += f"  |  SSN: ***{s.ssn_last4}"
        c.setFillColor(HexColor("#dcfce7"))
        c.roundRect(MARGIN, y - 10, PAGE_W - 2 * MARGIN, 25, 6, fill=1, stroke=0)
        c.setFillColor(GREEN_DARK)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(MARGIN + 10, y - 2, info)
        y -= 40

    # Retirement sections
    def draw_retirement_section(label, ret_accounts, start_y, color):
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(color)
        c.drawString(MARGIN + 5, start_y, label)
        start_y -= 15

        section_total = 0.0
        bubble_radius = 32
        spacing = 80
        base_x = MARGIN + 50

        for i, acc in enumerate(ret_accounts):
            balance = entries_by_account.get(acc["id"], 0)
            section_total += balance
            bx = base_x + (i % 3) * spacing
            by = start_y - 40 - (i // 3) * 85

            c.setFillColor(HexColor("#eff6ff"))
            c.circle(bx, by, bubble_radius, fill=1, stroke=0)
            c.setFillColor(BRAND_BLUE)
            c.setFont("Helvetica-Bold", 7)
            c.drawCentredString(bx, by + 12, acc["sub_type"])
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(bx, by - 2, f"${balance:,.0f}")
            if acc.get("account_number_last4"):
                c.setFillColor(GRAY)
                c.setFont("Helvetica", 7)
                c.drawCentredString(bx, by - 15, f"#{acc['account_number_last4']}")

        # Total box
        row_count = max(1, math.ceil(len(ret_accounts) / 3))
        total_y = start_y - 40 - row_count * 85 - 15
        c.setFillColor(GRAY_LIGHT)
        c.roundRect(MARGIN + 5, total_y - 8, 300, 22, 4, fill=1, stroke=0)
        c.setFillColor(DARK)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(MARGIN + 15, total_y, f"{label} Total: ${section_total:,.0f}")
        return total_y - 20, section_total

    y -= 5
    y, c1_total = draw_retirement_section("Client 1 — Retirement", client1_ret, y, BRAND_BLUE)
    y -= 15

    if report_data["spouse"] and client2_ret:
        y, c2_total = draw_retirement_section("Client 2 — Retirement", client2_ret, y, HexColor("#7c3aed"))
        y -= 15
    else:
        c2_total = 0.0

    # Non-Retirement section
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(HexColor("#b45309"))
    c.drawString(MARGIN + 5, y, "Non-Retirement")
    y -= 15

    nr_total = 0.0
    base_x = MARGIN + 50
    for i, acc in enumerate(non_ret):
        balance = entries_by_account.get(acc["id"], 0)
        nr_total += balance
        bx = base_x + (i % 3) * 80
        by = y - 35
        c.setFillColor(HexColor("#fef3c7"))
        c.circle(bx, by, 32, fill=1, stroke=0)
        c.setFillColor(HexColor("#b45309"))
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(bx, by + 12, acc["sub_type"])
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(bx, by - 2, f"${balance:,.0f}")

    nr_row_count = max(1, math.ceil(len(non_ret) / 3))
    total_y = y - 35 - nr_row_count * 5 - 55
    c.setFillColor(GRAY_LIGHT)
    c.roundRect(MARGIN + 5, total_y - 8, 300, 22, 4, fill=1, stroke=0)
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(MARGIN + 15, total_y, f"Non-Retirement Total: ${nr_total:,.0f}")
    y = total_y - 25

    # Trust section
    trust_total = 0.0
    for acc in trust_accs:
        trust_total += entries_by_account.get(acc["id"], 0)
    if trust_total:
        c.setFillColor(HexColor("#f0fdf4"))
        c.roundRect(MARGIN + 5, y - 30, 300, 30, 6, fill=1, stroke=0)
        c.setFillColor(GREEN_DARK)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(MARGIN + 15, y - 18, f"Trust: ${trust_total:,.0f}")
        y -= 40

    # Grand Total
    grand_total = c1_total + c2_total + nr_total + trust_total
    c.setFillColor(BRAND_BLUE)
    c.roundRect(MARGIN + 5, y - 30, PAGE_W - 2 * MARGIN - 10, 30, 6, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(MARGIN + 15, y - 20, f"Grand Total Net Worth: ${grand_total:,.0f}")
    y -= 45

    # Liabilities (separate, NOT subtracted)
    if liabilities:
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(RED_DARK)
        c.drawString(MARGIN + 5, y, "Liabilities (Not subtracted from net worth)")
        y -= 15

        liab_total = 0.0
        for liab in liabilities:
            balance = float(liab.get("balance", 0))
            liab_total += balance
            rate = liab.get("interest_rate", 0)
            desc = liab.get("description", "")
            c.setFillColor(HexColor("#fef2f2"))
            c.roundRect(MARGIN + 10, y - 18, PAGE_W - 2 * MARGIN - 20, 22, 4, fill=1, stroke=0)
            c.setFillColor(RED_DARK)
            c.setFont("Helvetica", 9)
            c.drawString(MARGIN + 20, y - 10, f"{liab['liability_type']} — {desc}  |  Rate: {rate}%  |  Balance: ${balance:,.0f}")
            y -= 28

        c.setFillColor(GRAY_LIGHT)
        c.roundRect(MARGIN + 10, y - 5, 250, 20, 4, fill=1, stroke=0)
        c.setFillColor(DARK)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(MARGIN + 20, y + 2, f"Liabilities Total: ${liab_total:,.0f}")

    # Footer
    c.setFillColor(GRAY)
    c.setFont("Helvetica", 8)
    c.drawCentredString(PAGE_W / 2, 30, "EF Financial Planning — Windbrook Solutions")

    c.save()
