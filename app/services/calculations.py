
from app.enums import AccountType, Owner
from app.models import Client, Account, Liability


def calculate_sacs(data):
    """Calculate SACS (cashflow) values."""
    inflow = float(data.get("inflow", 0))
    outflow = float(data.get("outflow", 0))
    monthly_expenses = float(data.get("monthly_expenses", 0))
    insurance_deductibles = float(data.get("insurance_deductibles", 0))

    excess = inflow - outflow
    private_reserve_target = (6 * monthly_expenses) + insurance_deductibles

    return {
        "inflow": inflow,
        "outflow": outflow,
        "excess": excess,
        "private_reserve_target": private_reserve_target,
    }


def calculate_tcc(account_balances, liabilities_balances):
    """
    Calculate TCC (net worth) values from account balances dict.
    account_balances: list of dicts with keys: account_type, owner, balance
    liabilities_balances: list of floats
    """
    client1_retirement = 0.0
    client2_retirement = 0.0
    non_retirement = 0.0
    trust = 0.0

    for acc in account_balances:
        atype = acc.get("account_type")
        owner = acc.get("owner")
        balance = float(acc.get("balance", 0))

        if atype == AccountType.retirement.value:
            if owner == Owner.client2.value:
                client2_retirement += balance
            else:
                client1_retirement += balance
        elif atype == AccountType.non_retirement.value:
            non_retirement += balance
        elif atype == AccountType.trust.value:
            trust += balance

    liabilities_total = sum(float(b) for b in liabilities_balances)
    grand_total = client1_retirement + client2_retirement + non_retirement + trust

    return {
        "client1_retirement_total": client1_retirement,
        "client2_retirement_total": client2_retirement,
        "non_retirement_total": non_retirement,
        "trust": trust,
        "grand_total": grand_total,
        "liabilities_total": liabilities_total,
    }


def get_client_report_data(client):
    """Gather all data needed for report generation from a client record."""
    active_profiles = [p for p in client.profiles if p.is_active and not p.is_deleted]
    active_accounts = [a for a in client.accounts if a.is_active and not a.is_deleted]
    active_liabilities = [l for l in client.liabilities if l.is_active and not l.is_deleted]

    primary = next((p for p in active_profiles if p.role.value == "primary"), None)
    spouse = next((p for p in active_profiles if p.role.value == "spouse"), None)

    total_inflow = primary.monthly_salary_after_tax if primary else 0
    if spouse:
        total_inflow += spouse.monthly_salary_after_tax

    expense_budget = client.financials.monthly_expense_budget if client.financials else 0
    insurance = client.financials.insurance_deductibles if client.financials else 0

    sacs = calculate_sacs({
        "inflow": total_inflow,
        "outflow": expense_budget,
        "monthly_expenses": expense_budget,
        "insurance_deductibles": insurance,
    })

    account_data = []
    for acc in active_accounts:
        account_data.append({
            "id": acc.id,
            "account_type": acc.account_type.value,
            "sub_type": acc.sub_type.value,
            "owner": acc.owner.value,
            "account_number_last4": acc.account_number_last4,
            "institution_name": acc.institution_name,
        })

    liability_data = []
    for liab in active_liabilities:
        liability_data.append({
            "id": liab.id,
            "liability_type": liab.liability_type.value,
            "interest_rate": liab.interest_rate,
            "balance": liab.balance,
            "description": liab.description,
        })

    return {
        "client": client,
        "primary": primary,
        "spouse": spouse,
        "accounts": account_data,
        "liabilities": liability_data,
        "sacs": sacs,
        "total_inflow": total_inflow,
        "expense_budget": expense_budget,
        "insurance": insurance,
    }
