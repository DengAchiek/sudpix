from decimal import Decimal, ROUND_HALF_UP


def format_currency(value):
    amount = Decimal(value or 0).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    if amount == amount.to_integral():
        return f"KES {amount:,.0f}"

    return f"KES {amount:,.2f}"
