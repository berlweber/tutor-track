import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from .forms import AssignmentForm, AttendanceAdjustmentForm
from .models import Assignment, AttendanceAdjustment, Session, Student
from .views import calculate_totals


class BillingModeTests(TestCase):
    def setUp(self):
        self.tutor = User.objects.create_user(username="avrech", password="secret")
        self.student = Student.objects.create(name="Moshe")

    def create_assignment(self, **overrides):
        defaults = {
            "student": self.student,
            "tutor": self.tutor,
            "goal": "חזרה על הגמרא",
            "session_rate": Decimal("120.00"),
            "sponsor": "P",
            "start_time": datetime.time(18, 0),
            "end_time": datetime.time(19, 0),
            "session_length": datetime.timedelta(hours=1),
            "billing_mode": Assignment.BILLING_PER_SESSION,
        }
        defaults.update(overrides)
        return Assignment.objects.create(**defaults)

    def test_monthly_assignment_computes_hidden_session_rate(self):
        assignment = self.create_assignment(
            billing_mode=Assignment.BILLING_PER_MONTH,
            monthly_rate=Decimal("1290.00"),
            sessions_per_week=3,
            session_rate=Decimal("0.00"),
        )

        assignment.refresh_from_db()

        self.assertEqual(assignment.session_rate, Decimal("100.00"))

    def test_monthly_dashboard_total_starts_from_monthly_rate_and_reduces_adjustments(self):
        assignment = self.create_assignment(
            billing_mode=Assignment.BILLING_PER_MONTH,
            monthly_rate=Decimal("1290.00"),
            sessions_per_week=3,
            session_rate=Decimal("0.00"),
        )
        AttendanceAdjustment.objects.create(
            assignment=assignment,
            date=datetime.date(2026, 4, 3),
            adjustment_type=AttendanceAdjustment.TYPE_ABSENT,
        )
        AttendanceAdjustment.objects.create(
            assignment=assignment,
            date=datetime.date(2026, 4, 10),
            adjustment_type=AttendanceAdjustment.TYPE_LATE,
            duration=datetime.timedelta(minutes=30),
        )

        assignment = calculate_totals(assignment, 4, 2026)

        self.assertEqual(assignment.total_adjustments, 2)
        self.assertEqual(assignment.total_earnings, Decimal("1140.00"))
        self.assertEqual(assignment.activity_label, "הפחתות")

    def test_per_session_dashboard_total_stays_based_on_sessions(self):
        assignment = self.create_assignment(session_rate=Decimal("150.00"))
        Session.objects.create(
            assignment=assignment,
            date=datetime.date(2026, 4, 2),
            duration=datetime.timedelta(hours=1),
        )
        Session.objects.create(
            assignment=assignment,
            date=datetime.date(2026, 4, 9),
            duration=datetime.timedelta(hours=1),
        )

        assignment = calculate_totals(assignment, 4, 2026)

        self.assertEqual(assignment.total_sessions, 2)
        self.assertEqual(assignment.total_earnings, Decimal("300.00"))
        self.assertEqual(assignment.activity_label, "שיעורים")

    def test_assignment_form_renders_billing_mode_choices(self):
        form = AssignmentForm()

        self.assertIn("value=\"session\"", str(form["billing_mode"]))
        self.assertIn("value=\"month\"", str(form["billing_mode"]))

    def test_late_adjustment_deduction_is_proportional_to_duration(self):
        assignment = self.create_assignment(
            billing_mode=Assignment.BILLING_PER_MONTH,
            monthly_rate=Decimal("1290.00"),
            sessions_per_week=3,
            session_rate=Decimal("0.00"),
            session_length=datetime.timedelta(hours=1),
        )
        adjustment = AttendanceAdjustment.objects.create(
            assignment=assignment,
            date=datetime.date(2026, 4, 10),
            adjustment_type=AttendanceAdjustment.TYPE_LATE,
            duration=datetime.timedelta(minutes=15),
        )

        self.assertEqual(adjustment.deduction_amount, Decimal("25.00"))

    def test_late_adjustment_form_requires_duration(self):
        form = AttendanceAdjustmentForm(
            data={
                "date": "10/04/2026",
                "adjustment_type": AttendanceAdjustment.TYPE_LATE,
                "duration": "",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("duration", form.errors)
