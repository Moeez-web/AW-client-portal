import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from app import db
from app.models import Client, Report, ReportEntry, Account
from app.enums import AccountType, Owner
from app.services.calculations import get_client_report_data, calculate_tcc
from app.services.pdf_generator import generate_sacs_pdf, generate_tcc_pdf

reports_bp = Blueprint("reports", __name__)

PDF_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "db", "pdfs")


def _ensure_pdf_dir():
    os.makedirs(PDF_DIR, exist_ok=True)


def _get_report_entries(report):
    """Build lookups from report entries."""
    entries_by_account = {}
    entries_by_label = {}
    for entry in report.entries:
        if entry.account_id:
            entries_by_account[entry.account_id] = entry.balance
        else:
            entries_by_label[entry.label] = entry.balance
    return entries_by_account, entries_by_label


def _calc_tcc_from_entries(report_data, entries_by_account, entries_by_label):
    """Calculate TCC totals using actual report entry values."""
    account_balances = []
    for acc in report_data["accounts"]:
        account_balances.append({
            "account_type": acc["account_type"],
            "owner": acc["owner"],
            "balance": entries_by_account.get(acc["id"], 0),
        })

    liability_balances = []
    for liab in report_data["liabilities"]:
        key = f"liability_{liab['id']}"
        val = entries_by_label.get(f"liability_balance_{liab['id']}")
        if val is not None:
            liability_balances.append(float(val))
        else:
            liability_balances.append(float(liab.get("balance", 0)))

    return calculate_tcc(account_balances, liability_balances)


@reports_bp.route("/clients/<int:client_id>/reports/new", methods=["GET"])
def new_report(client_id):
    client = Client.query.get_or_404(client_id)
    report_data = get_client_report_data(client)

    # Get last report for "use last value" feature
    last_report = Report.query.filter_by(client_id=client_id).order_by(Report.generated_at.desc()).first()
    last_entries = {}
    if last_report:
        for entry in last_report.entries:
            if entry.account_id:
                last_entries[entry.account_id] = entry.balance
            elif entry.label:
                last_entries[entry.label] = entry.balance

    # Group accounts by type for organized display
    accounts_grouped = {
        "retirement_client1": [],
        "retirement_client2": [],
        "non_retirement": [],
        "trust": [],
    }
    for acc in report_data["accounts"]:
        if acc["account_type"] == AccountType.retirement.value:
            if acc["owner"] == Owner.client2.value:
                accounts_grouped["retirement_client2"].append(acc)
            else:
                accounts_grouped["retirement_client1"].append(acc)
        elif acc["account_type"] == AccountType.non_retirement.value:
            accounts_grouped["non_retirement"].append(acc)
        elif acc["account_type"] == AccountType.trust.value:
            accounts_grouped["trust"].append(acc)

    return render_template("reports/entry.html",
                           client=client,
                           report_data=report_data,
                           accounts_grouped=accounts_grouped,
                           last_entries=last_entries,
                           last_report=last_report)


@reports_bp.route("/clients/<int:client_id>/reports", methods=["POST"])
def create_report(client_id):
    client = Client.query.get_or_404(client_id)
    try:
        now = datetime.utcnow()
        quarter = (now.month - 1) // 3 + 1

        report = Report(
            client_id=client_id,
            quarter=quarter,
            year=now.year,
            generated_at=now,
        )
        db.session.add(report)
        db.session.flush()

        # Save account balances
        active_accounts = [a for a in client.accounts if a.is_active and not a.is_deleted]
        for acc in active_accounts:
            balance = request.form.get(f"balance_{acc.id}", "")
            if balance and balance.strip():
                entry = ReportEntry(
                    report_id=report.id,
                    account_id=acc.id,
                    balance=max(0, float(balance)),
                    label=f"{acc.sub_type.value} ({acc.account_number_last4 or 'N/A'})",
                )
                db.session.add(entry)

        # Save liability balances
        active_liabilities = [l for l in client.liabilities if l.is_active and not l.is_deleted]
        for liab in active_liabilities:
            balance = request.form.get(f"liability_balance_{liab.id}", "")
            if balance and balance.strip():
                entry = ReportEntry(
                    report_id=report.id,
                    balance=max(0, float(balance)),
                    label=f"liability_balance_{liab.id}",
                )
                db.session.add(entry)

        # Save SACS extra fields
        for field in ["private_reserve_balance", "investment_balance"]:
            val = request.form.get(field, "")
            if val and val.strip():
                db.session.add(ReportEntry(
                    report_id=report.id,
                    balance=max(0, float(val)),
                    label=field,
                ))

        db.session.commit()
        flash("Report saved successfully.", "success")
        return redirect(url_for("reports.view_report", client_id=client_id, report_id=report.id))

    except Exception as e:
        db.session.rollback()
        flash(f"Error saving report: {str(e)}", "error")
        return redirect(url_for("reports.new_report", client_id=client_id))


@reports_bp.route("/clients/<int:client_id>/reports", methods=["GET"])
def report_history(client_id):
    client = Client.query.get_or_404(client_id)
    reports = Report.query.filter_by(client_id=client_id).order_by(Report.generated_at.desc()).all()
    return render_template("reports/history.html", client=client, reports=reports)


@reports_bp.route("/clients/<int:client_id>/reports/<int:report_id>", methods=["GET"])
def view_report(client_id, report_id):
    client = Client.query.get_or_404(client_id)
    report = Report.query.get_or_404(report_id)
    if report.client_id != client_id:
        flash("Report not found.", "error")
        return redirect(url_for("reports.report_history", client_id=client_id))

    report_data = get_client_report_data(client)
    entries_by_account, entries_by_label = _get_report_entries(report)
    tcc_totals = _calc_tcc_from_entries(report_data, entries_by_account, entries_by_label)

    # Group accounts for display
    accounts_grouped = {
        "retirement_client1": [],
        "retirement_client2": [],
        "non_retirement": [],
        "trust": [],
    }
    for acc in report_data["accounts"]:
        if acc["account_type"] == AccountType.retirement.value:
            if acc["owner"] == Owner.client2.value:
                accounts_grouped["retirement_client2"].append(acc)
            else:
                accounts_grouped["retirement_client1"].append(acc)
        elif acc["account_type"] == AccountType.non_retirement.value:
            accounts_grouped["non_retirement"].append(acc)
        elif acc["account_type"] == AccountType.trust.value:
            accounts_grouped["trust"].append(acc)

    return render_template("reports/view.html",
                           client=client,
                           report=report,
                           report_data=report_data,
                           accounts_grouped=accounts_grouped,
                           entries_by_account=entries_by_account,
                           entries_by_label=entries_by_label,
                           tcc_totals=tcc_totals)


@reports_bp.route("/clients/<int:client_id>/reports/<int:report_id>/update", methods=["POST"])
def update_report(client_id, report_id):
    client = Client.query.get_or_404(client_id)
    report = Report.query.get_or_404(report_id)
    try:
        active_accounts = [a for a in client.accounts if a.is_active and not a.is_deleted]
        for acc in active_accounts:
            balance = request.form.get(f"balance_{acc.id}", "")
            if balance and balance.strip():
                existing = ReportEntry.query.filter_by(report_id=report.id, account_id=acc.id).first()
                if existing:
                    existing.balance = max(0, float(balance))
                else:
                    db.session.add(ReportEntry(
                        report_id=report.id,
                        account_id=acc.id,
                        balance=max(0, float(balance)),
                        label=f"{acc.sub_type.value} ({acc.account_number_last4 or 'N/A'})",
                    ))

        db.session.commit()
        flash("Report updated.", "success")
        return redirect(url_for("reports.view_report", client_id=client_id, report_id=report_id))

    except Exception as e:
        db.session.rollback()
        flash(f"Error updating report: {str(e)}", "error")
        return redirect(url_for("reports.view_report", client_id=client_id, report_id=report_id))


@reports_bp.route("/clients/<int:client_id>/reports/<int:report_id>/download/sacs", methods=["GET"])
def download_sacs(client_id, report_id):
    client = Client.query.get_or_404(client_id)
    report = Report.query.get_or_404(report_id)

    _ensure_pdf_dir()
    report_data = get_client_report_data(client)
    entries_by_account, entries_by_label = _get_report_entries(report)

    filename = f"sacs_{client.case_name.replace(' ', '_')}_{report.quarter_label.replace(' ', '_')}.pdf"
    filepath = os.path.join(PDF_DIR, filename)

    generate_sacs_pdf(filepath, report_data, entries_by_account, entries_by_label, report)

    report.pdf_sacs_path = filepath
    db.session.commit()

    return send_file(filepath, as_attachment=True, download_name=filename)


@reports_bp.route("/clients/<int:client_id>/reports/<int:report_id>/download/tcc", methods=["GET"])
def download_tcc(client_id, report_id):
    client = Client.query.get_or_404(client_id)
    report = Report.query.get_or_404(report_id)

    _ensure_pdf_dir()
    report_data = get_client_report_data(client)
    entries_by_account, entries_by_label = _get_report_entries(report)

    filename = f"tcc_{client.case_name.replace(' ', '_')}_{report.quarter_label.replace(' ', '_')}.pdf"
    filepath = os.path.join(PDF_DIR, filename)

    generate_tcc_pdf(filepath, report_data, entries_by_account, entries_by_label, report)

    report.pdf_tcc_path = filepath
    db.session.commit()

    return send_file(filepath, as_attachment=True, download_name=filename)
