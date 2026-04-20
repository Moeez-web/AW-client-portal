from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from app.models import Client, ClientProfile, Account, Liability, ClientFinancial
from app.enums import MaritalStatus, AccountType, SubType, Owner, LiabilityType, ProfileRole

clients_bp = Blueprint("clients", __name__)


@clients_bp.route("/")
def landing():
    return render_template("landing/index.html")


@clients_bp.route("/clients")
def client_list():
    clients = Client.query.filter_by().order_by(Client.created_at.desc()).all()
    for c in clients:
        c.last_report = c.reports[-1] if c.reports else None
    return render_template("clients/list.html", clients=clients)


@clients_bp.route("/clients/new", methods=["GET"])
def new_client():
    return render_template("clients/form.html", client=None, enums={
        "marital_statuses": MaritalStatus,
        "account_types": AccountType,
        "sub_types": SubType,
        "owners": Owner,
        "liability_types": LiabilityType,
    })


@clients_bp.route("/clients", methods=["POST"])
def create_client():
    try:
        case_name = request.form.get("case_name", "").strip()
        if not case_name:
            flash("Case Name is required.", "error")
            return redirect(url_for("clients.new_client"))

        client = Client(
            case_name=case_name,
            marital_status=MaritalStatus(request.form.get("marital_status", "single")),
        )
        db.session.add(client)
        db.session.flush()

        # Primary profile
        primary = ClientProfile(
            client_id=client.id,
            full_name=request.form.get("primary_name"),
            dob=_parse_date(request.form.get("primary_dob")),
            ssn_last4=request.form.get("primary_ssn4"),
            monthly_salary_after_tax=float(request.form.get("primary_salary", 0) or 0),
            role=ProfileRole.primary,
        )
        db.session.add(primary)

        # Spouse profile if married
        if client.marital_status == MaritalStatus.married and request.form.get("spouse_name"):
            spouse = ClientProfile(
                client_id=client.id,
                full_name=request.form.get("spouse_name"),
                dob=_parse_date(request.form.get("spouse_dob")),
                ssn_last4=request.form.get("spouse_ssn4"),
                monthly_salary_after_tax=float(request.form.get("spouse_salary", 0) or 0),
                role=ProfileRole.spouse,
            )
            db.session.add(spouse)

        # Financials
        financials = ClientFinancial(
            client_id=client.id,
            monthly_expense_budget=float(request.form.get("monthly_expense_budget", 0) or 0),
            private_reserve_target=float(request.form.get("private_reserve_target", 0) or 0),
            insurance_deductibles=float(request.form.get("insurance_deductibles", 0) or 0),
        )
        db.session.add(financials)

        # Accounts (dynamic rows)
        accounts_data = _extract_accounts(request.form)
        for acc in accounts_data:
            account = Account(
                client_id=client.id,
                owner=Owner(acc["owner"]),
                account_type=AccountType(acc["account_type"]),
                sub_type=SubType(acc["sub_type"]),
                account_number_last4=acc.get("account_number_last4"),
                institution_name=acc.get("institution_name"),
            )
            db.session.add(account)

        # Liabilities (dynamic rows)
        liabilities_data = _extract_liabilities(request.form)
        for liab in liabilities_data:
            liability = Liability(
                client_id=client.id,
                liability_type=LiabilityType(liab["liability_type"]),
                interest_rate=float(liab.get("interest_rate", 0) or 0),
                balance=float(liab.get("balance", 0) or 0),
                description=liab.get("description"),
            )
            db.session.add(liability)

        db.session.commit()
        flash("Client created successfully.", "success")
        return redirect(url_for("clients.client_list"))

    except Exception as e:
        db.session.rollback()
        flash(f"Error creating client: {str(e)}", "error")
        return redirect(url_for("clients.new_client"))


@clients_bp.route("/clients/<int:client_id>", methods=["GET"])
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)
    primary = next((p for p in client.profiles if p.role == ProfileRole.primary), None)
    spouse = next((p for p in client.profiles if p.role == ProfileRole.spouse and p.is_active and not p.is_deleted), None)
    active_accounts = [a for a in client.accounts if a.is_active and not a.is_deleted]
    active_liabilities = [l for l in client.liabilities if l.is_active and not l.is_deleted]
    return render_template("clients/form.html", client=client,
                           primary=primary, spouse=spouse,
                           active_accounts=active_accounts,
                           active_liabilities=active_liabilities,
                           enums={
        "marital_statuses": MaritalStatus,
        "account_types": AccountType,
        "sub_types": SubType,
        "owners": Owner,
        "liability_types": LiabilityType,
    })


@clients_bp.route("/clients/<int:client_id>", methods=["POST"])
def update_client(client_id):
    client = Client.query.get_or_404(client_id)
    try:
        client.case_name = request.form.get("case_name", client.case_name)
        client.marital_status = MaritalStatus(request.form.get("marital_status", client.marital_status.value))

        # Update primary profile
        primary = next((p for p in client.profiles if p.role == ProfileRole.primary), None)
        if primary:
            primary.full_name = request.form.get("primary_name", primary.full_name)
            primary.dob = _parse_date(request.form.get("primary_dob")) or primary.dob
            primary.ssn_last4 = request.form.get("primary_ssn4", primary.ssn_last4)
            primary.monthly_salary_after_tax = float(request.form.get("primary_salary", 0) or primary.monthly_salary_after_tax)

        # Handle spouse
        if client.marital_status == MaritalStatus.married:
            spouse = next((p for p in client.profiles if p.role == ProfileRole.spouse and p.is_active), None)
            spouse_name = request.form.get("spouse_name")
            if spouse and spouse_name:
                spouse.full_name = spouse_name
                spouse.dob = _parse_date(request.form.get("spouse_dob")) or spouse.dob
                spouse.ssn_last4 = request.form.get("spouse_ssn4", spouse.ssn_last4)
                spouse.monthly_salary_after_tax = float(request.form.get("spouse_salary", 0) or spouse.monthly_salary_after_tax)
            elif not spouse and spouse_name:
                new_spouse = ClientProfile(
                    client_id=client.id,
                    full_name=spouse_name,
                    dob=_parse_date(request.form.get("spouse_dob")),
                    ssn_last4=request.form.get("spouse_ssn4"),
                    monthly_salary_after_tax=float(request.form.get("spouse_salary", 0) or 0),
                    role=ProfileRole.spouse,
                )
                db.session.add(new_spouse)
        else:
            for p in client.profiles:
                if p.role == ProfileRole.spouse and p.is_active:
                    p.is_active = False
            # Reassign client2/joint accounts to client1
            for acc in client.accounts:
                if acc.is_active and not acc.is_deleted and acc.owner in (Owner.client2, Owner.joint):
                    acc.owner = Owner.client1

        # Update financials
        if not client.financials:
            client.financials = ClientFinancial(client_id=client.id)
            db.session.add(client.financials)
        client.financials.monthly_expense_budget = max(0, float(request.form.get("monthly_expense_budget", 0) or 0))
        client.financials.private_reserve_target = max(0, float(request.form.get("private_reserve_target", 0) or 0))
        client.financials.insurance_deductibles = max(0, float(request.form.get("insurance_deductibles", 0) or 0))

        # Update accounts — save pre-existing IDs before adding new ones
        pre_existing_account_ids = {a.id for a in client.accounts if a.is_active and not a.is_deleted}
        form_account_ids = set()
        accounts_data = _extract_accounts(request.form)
        for acc in accounts_data:
            if acc.get("id"):
                form_account_ids.add(int(acc["id"]))
                account = Account.query.get(acc["id"])
                if account and account.client_id == client.id:
                    account.owner = Owner(acc["owner"])
                    account.account_type = AccountType(acc["account_type"])
                    account.sub_type = SubType(acc["sub_type"])
                    account.account_number_last4 = acc.get("account_number_last4")
                    account.institution_name = acc.get("institution_name")
            else:
                new_acc = Account(
                    client_id=client.id,
                    owner=Owner(acc["owner"]),
                    account_type=AccountType(acc["account_type"]),
                    sub_type=SubType(acc["sub_type"]),
                    account_number_last4=acc.get("account_number_last4"),
                    institution_name=acc.get("institution_name"),
                )
                db.session.add(new_acc)

        # Mark removed accounts as deleted (only pre-existing ones not in form)
        for acc_id in pre_existing_account_ids:
            if acc_id not in form_account_ids:
                account = Account.query.get(acc_id)
                if account:
                    account.is_deleted = True

        # Update liabilities — same pattern
        pre_existing_liab_ids = {l.id for l in client.liabilities if l.is_active and not l.is_deleted}
        form_liab_ids = set()
        liabilities_data = _extract_liabilities(request.form)
        for liab in liabilities_data:
            if liab.get("id"):
                form_liab_ids.add(int(liab["id"]))
                liability = Liability.query.get(liab["id"])
                if liability and liability.client_id == client.id:
                    liability.liability_type = LiabilityType(liab["liability_type"])
                    liability.interest_rate = float(liab.get("interest_rate", 0) or 0)
                    liability.balance = float(liab.get("balance", 0) or 0)
                    liability.description = liab.get("description")
            else:
                new_liab = Liability(
                    client_id=client.id,
                    liability_type=LiabilityType(liab["liability_type"]),
                    interest_rate=float(liab.get("interest_rate", 0) or 0),
                    balance=float(liab.get("balance", 0) or 0),
                    description=liab.get("description"),
                )
                db.session.add(new_liab)

        # Mark removed liabilities as deleted
        for liab_id in pre_existing_liab_ids:
            if liab_id not in form_liab_ids:
                liability = Liability.query.get(liab_id)
                if liability:
                    liability.is_deleted = True

        db.session.commit()
        flash("Client updated successfully.", "success")
        return redirect(url_for("clients.client_list"))

    except Exception as e:
        db.session.rollback()
        flash(f"Error updating client: {str(e)}", "error")
        return redirect(url_for("clients.edit_client", client_id=client_id))


@clients_bp.route("/clients/<int:client_id>/delete", methods=["POST"])
def delete_client(client_id):
    client = Client.query.get_or_404(client_id)
    for profile in client.profiles:
        profile.is_deleted = True
        profile.is_active = False
    for account in client.accounts:
        account.is_deleted = True
    for liability in client.liabilities:
        liability.is_deleted = True
    db.session.commit()
    flash("Client deleted.", "success")
    return redirect(url_for("clients.client_list"))


# --- Account / Liability inline delete ---

@clients_bp.route("/clients/<int:client_id>/accounts/<int:account_id>/delete", methods=["POST"])
def delete_account(client_id, account_id):
    account = Account.query.get_or_404(account_id)
    if account.client_id != client_id:
        return jsonify({"error": "Unauthorized"}), 403
    account.is_deleted = True
    db.session.commit()
    return jsonify({"success": True})


@clients_bp.route("/clients/<int:client_id>/liabilities/<int:liability_id>/delete", methods=["POST"])
def delete_liability(client_id, liability_id):
    liability = Liability.query.get_or_404(liability_id)
    if liability.client_id != client_id:
        return jsonify({"error": "Unauthorized"}), 403
    liability.is_deleted = True
    db.session.commit()
    return jsonify({"success": True})


# --- Helpers ---

def _parse_date(date_str):
    if not date_str:
        return None
    from datetime import datetime
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None


def _extract_accounts(form):
    accounts = []
    idx = 0
    while form.get(f"accounts[{idx}][account_type]"):
        accounts.append({
            "id": form.get(f"accounts[{idx}][id]"),
            "owner": form.get(f"accounts[{idx}][owner]", "client1"),
            "account_type": form.get(f"accounts[{idx}][account_type]"),
            "sub_type": form.get(f"accounts[{idx}][sub_type]"),
            "account_number_last4": form.get(f"accounts[{idx}][account_number_last4]"),
            "institution_name": form.get(f"accounts[{idx}][institution_name]"),
        })
        idx += 1
    return accounts


def _extract_liabilities(form):
    liabilities = []
    idx = 0
    while form.get(f"liabilities[{idx}][liability_type]"):
        liabilities.append({
            "id": form.get(f"liabilities[{idx}][id]"),
            "liability_type": form.get(f"liabilities[{idx}][liability_type]"),
            "interest_rate": form.get(f"liabilities[{idx}][interest_rate]"),
            "balance": form.get(f"liabilities[{idx}][balance]"),
            "description": form.get(f"liabilities[{idx}][description]"),
        })
        idx += 1
    return liabilities
