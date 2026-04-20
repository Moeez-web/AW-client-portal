from flask import Blueprint, request, jsonify
from app.services.calculations import calculate_sacs, calculate_tcc

api_bp = Blueprint("api", __name__)


@api_bp.route("/calculate", methods=["POST"])
def calculate():
    data = request.get_json()
    mode = data.get("mode", "all")

    result = {}

    if mode in ("all", "sacs"):
        result.update(calculate_sacs({
            "inflow": data.get("inflow", 0),
            "outflow": data.get("outflow", 0),
            "monthly_expenses": data.get("monthly_expenses", 0),
            "insurance_deductibles": data.get("insurance_deductibles", 0),
        }))

    if mode in ("all", "tcc"):
        result.update(calculate_tcc(
            data.get("accounts", []),
            data.get("liabilities", []),
        ))

    return jsonify(result)
