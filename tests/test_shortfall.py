from decimal import Decimal

from wage_checker.reconcile import shortfall


class TestShortfall:
    def test_shortfall_underpaid_shift(self):
        # Underpaid shift: shortfall(required, paid) == required - paid to the cent
        required = Decimal('176.46')
        paid = Decimal('120.00')
        assert shortfall(required, paid) == Decimal('56.46')

    def test_shortfall_compliant_shift(self):
        # Compliant shift: clamps to Decimal('0.00') when paid >= required
        required = Decimal('100.00')
        paid = Decimal('150.00')
        assert shortfall(required, paid) == Decimal('0.00')

    def test_shortfall_overpaid_shift(self):
        # Overpaid shift: never negative, clamps to Decimal('0.00')
        required = Decimal('100.00')
        paid = Decimal('200.00')
        assert shortfall(required, paid) == Decimal('0.00')

    def test_shortfall_exact_payment(self):
        # Exact payment: should clamp to Decimal('0.00')
        required = Decimal('100.00')
        paid = Decimal('100.00')
        assert shortfall(required, paid) == Decimal('0.00')
