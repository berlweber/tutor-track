import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase

from .forms import (
    AssignmentForm,
    AttendanceAdjustmentForm,
    MonthlyReportForm,
    SessionForm,
    StudentForm,
)
from .models import Assignment, AttendanceAdjustment, MonthlyReport, Session, Student
from .views import (
    SORT_BY_STUDENT,
    SORT_BY_TUTOR,
    calculate_totals,
    sort_assignments_for_display,
)


class BillingModeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.tutor = User.objects.create_user(username="avrech", password="secret")
        self.student = Student.objects.create(first_name="Moshe", last_name="Green")

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
        self.assertEqual(assignment.activity_count, Decimal("2.00"))
        self.assertEqual(assignment.activity_label, "שיעורים לפי שעות")

    def test_per_session_dashboard_total_scales_with_shorter_and_longer_sessions(self):
        assignment = self.create_assignment(
            session_rate=Decimal("150.00"),
            session_length=datetime.timedelta(hours=1),
        )
        Session.objects.create(
            assignment=assignment,
            date=datetime.date(2026, 4, 2),
            duration=datetime.timedelta(minutes=30),
        )
        Session.objects.create(
            assignment=assignment,
            date=datetime.date(2026, 4, 9),
            duration=datetime.timedelta(hours=2),
        )

        assignment = calculate_totals(assignment, 4, 2026)

        self.assertEqual(assignment.total_sessions, 2)
        self.assertEqual(assignment.activity_count, Decimal("2.50"))
        self.assertEqual(assignment.total_earnings, Decimal("375.00"))
        self.assertEqual(assignment.activity_label, "שיעורים לפי שעות")

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

    def test_student_display_name_uses_new_format(self):
        self.assertEqual(str(self.student), 'הבה"ח Moshe Green ני"ו')

    def test_student_falls_back_to_legacy_name_as_last_name(self):
        student = Student.objects.create(name="Weiss")

        self.assertEqual(student.last_name, "Weiss")
        self.assertEqual(str(student), 'הבה"ח Weiss ני"ו')

    def test_student_form_only_exposes_first_and_last_name(self):
        form = StudentForm()

        self.assertEqual(list(form.fields.keys()), ["first_name", "last_name"])

    def test_student_sort_orders_by_student_then_tutor_last_name(self):
        student_a = Student.objects.create(first_name="A", last_name="כהן")
        student_b = Student.objects.create(first_name="B", last_name="לוי")
        tutor_a = User.objects.create_user(username="tutor-a", password="secret", last_name="ברק")
        tutor_b = User.objects.create_user(username="tutor-b", password="secret", last_name="דוד")

        assignment_1 = self.create_assignment(student=student_a, tutor=tutor_b)
        assignment_2 = self.create_assignment(student=student_a, tutor=tutor_a)
        assignment_3 = self.create_assignment(student=student_b, tutor=tutor_a)

        sorted_assignments = sort_assignments_for_display(
            [assignment_1, assignment_2, assignment_3],
            SORT_BY_STUDENT,
        )

        self.assertEqual(
            [assignment.id for assignment in sorted_assignments],
            [assignment_2.id, assignment_1.id, assignment_3.id],
        )

    def test_tutor_sort_orders_by_tutor_then_student_last_name(self):
        student_a = Student.objects.create(first_name="A", last_name="כהן")
        student_b = Student.objects.create(first_name="B", last_name="לוי")
        tutor_a = User.objects.create_user(username="tutor-a", password="secret", last_name="ברק")
        tutor_b = User.objects.create_user(username="tutor-b", password="secret", last_name="דוד")

        assignment_1 = self.create_assignment(student=student_b, tutor=tutor_a)
        assignment_2 = self.create_assignment(student=student_a, tutor=tutor_a)
        assignment_3 = self.create_assignment(student=student_a, tutor=tutor_b)

        sorted_assignments = sort_assignments_for_display(
            [assignment_1, assignment_2, assignment_3],
            SORT_BY_TUTOR,
        )

        self.assertEqual(
            [assignment.id for assignment in sorted_assignments],
            [assignment_2.id, assignment_1.id, assignment_3.id],
        )

    def test_assignment_list_page_shows_assignments(self):
        self.create_assignment()
        self.client.force_login(self.tutor)

        response = self.client.get("/assignments/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Moshe Green")
        self.assertContains(response, "חזרה על הגמרא")

    def test_session_form_requires_duration(self):
        form = SessionForm(
            data={
                "date": "10/04/2026",
                "duration": "",
                "note": "",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("duration", form.errors)

    def test_session_create_missing_date_rerenders_form_with_error(self):
        assignment = self.create_assignment()
        self.client.force_login(self.tutor)

        response = self.client.post(
            f"/assignment/{assignment.id}/sessions/create/",
            data={
                "date": "",
                "duration": "01:00",
                "note": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "נא לבחור תאריך.", status_code=200)
        self.assertEqual(Session.objects.filter(assignment=assignment).count(), 0)

    def test_session_billing_detail_shows_monthly_header_actions_once(self):
        assignment = self.create_assignment()
        Session.objects.create(
            assignment=assignment,
            date=datetime.date(2026, 4, 10),
            duration=datetime.timedelta(hours=1),
        )
        self.client.force_login(self.tutor)

        response = self.client.get(f"/assignments/{assignment.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "הוסף שיעור", count=1)
        self.assertContains(response, "הוסף עידכון התקדמות", count=1)

    def test_monthly_billing_detail_uses_header_actions_without_inline_adjustment_form(self):
        assignment = self.create_assignment(
            billing_mode=Assignment.BILLING_PER_MONTH,
            monthly_rate=Decimal("1290.00"),
            sessions_per_week=3,
            session_rate=Decimal("0.00"),
        )
        AttendanceAdjustment.objects.create(
            assignment=assignment,
            date=datetime.date(2026, 4, 10),
            adjustment_type=AttendanceAdjustment.TYPE_ABSENT,
        )
        self.client.force_login(self.tutor)

        response = self.client.get(f"/assignments/{assignment.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "הוסף דיווח איחור/חיסור", count=1)
        self.assertContains(response, "הוסף עידכון התקדמות", count=1)
        self.assertNotContains(response, "adjustment-form")
        self.assertNotContains(response, "add-adjustment")

    def test_adjustment_create_page_saves_and_redirects_to_month(self):
        assignment = self.create_assignment(
            billing_mode=Assignment.BILLING_PER_MONTH,
            monthly_rate=Decimal("1290.00"),
            sessions_per_week=3,
            session_rate=Decimal("0.00"),
        )
        self.client.force_login(self.tutor)

        response = self.client.post(
            f"/assignment/{assignment.id}/adjustments/create/",
            data={
                "date": "10/04/2026",
                "adjustment_type": AttendanceAdjustment.TYPE_LATE,
                "duration": "00:15",
            },
        )

        self.assertRedirects(
            response,
            f"/assignments/{assignment.id}/#month-2026-04",
            fetch_redirect_response=False,
        )
        self.assertEqual(AttendanceAdjustment.objects.filter(assignment=assignment).count(), 1)

    def test_dashboard_initial_month_picker_renders_without_day(self):
        self.create_assignment()
        self.client.force_login(self.tutor)

        response = self.client.get("/assignments/dashboard/")

        self.assertEqual(response.status_code, 200)
        today = datetime.date.today().replace(day=1)
        self.assertContains(response, f'value="{today.strftime("%Y-%m")}"')

    def test_progress_update_form_uses_full_date_field(self):
        form = MonthlyReportForm()

        self.assertIn("report_date", form.fields)
        self.assertNotIn("day", form.fields)

    def test_assignment_can_store_multiple_progress_updates_in_same_month(self):
        assignment = self.create_assignment()

        MonthlyReport.objects.create(
            assignment=assignment,
            report_date=datetime.date(2026, 4, 5),
            content="עידכון ראשון",
        )
        MonthlyReport.objects.create(
            assignment=assignment,
            report_date=datetime.date(2026, 4, 18),
            content="עידכון שני",
        )

        self.assertEqual(MonthlyReport.objects.filter(assignment=assignment).count(), 2)

    def test_dashboard_uses_latest_progress_update_and_count_for_selected_month(self):
        assignment = self.create_assignment()
        MonthlyReport.objects.create(
            assignment=assignment,
            report_date=datetime.date(2026, 4, 5),
            content="עידכון ראשון",
        )
        latest_update = MonthlyReport.objects.create(
            assignment=assignment,
            report_date=datetime.date(2026, 4, 18),
            content="עידכון שני",
        )

        assignment = calculate_totals(assignment, 4, 2026)

        self.assertEqual(assignment.progress_update_count, 2)
        self.assertEqual(assignment.earlier_progress_update_count, 1)
        self.assertEqual(assignment.latest_progress_update.id, latest_update.id)
        self.assertEqual(
            assignment.progress_updates_month_url,
            f"/assignments/{assignment.id}/#updates-2026-04",
        )

    def test_dashboard_links_earlier_progress_updates_to_assignment_month(self):
        assignment = self.create_assignment()
        MonthlyReport.objects.create(
            assignment=assignment,
            report_date=datetime.date(2026, 4, 5),
            content="עידכון ראשון",
        )
        MonthlyReport.objects.create(
            assignment=assignment,
            report_date=datetime.date(2026, 4, 18),
            content="עידכון שני",
        )
        self.client.force_login(self.tutor)

        response = self.client.get("/assignments/dashboard/?month=2026-04")

        self.assertContains(response, "העידכון האחרון")
        self.assertContains(response, "עידכון שני")
        self.assertContains(response, "יש עוד עידכון קודם לחודש הזה")
        self.assertContains(response, f'href="/assignments/{assignment.id}/#updates-2026-04"')
        self.assertContains(response, f'data-update-url="/assignments/{assignment.id}/#updates-2026-04"')

    def test_create_progress_update_saves_full_selected_date(self):
        assignment = self.create_assignment()
        self.client.force_login(self.tutor)

        response = self.client.post(
            f"/assignment/{assignment.id}/reports/create/",
            data={
                "report_date": "15/04/2026",
                "content": "עידכון לאמצע החודש",
            },
        )

        self.assertEqual(response.status_code, 302)
        update = MonthlyReport.objects.get(assignment=assignment)
        self.assertEqual(update.report_date, datetime.date(2026, 4, 15))

    def test_edit_progress_update_allows_full_date_change(self):
        assignment = self.create_assignment()
        update = MonthlyReport.objects.create(
            assignment=assignment,
            report_date=datetime.date(2026, 4, 15),
            content="עידכון מקורי",
        )
        self.client.force_login(self.tutor)

        response = self.client.post(
            f"/reports/{update.id}/update/",
            data={
                "report_date": "03/05/2026",
                "content": "עידכון מעודכן",
            },
        )

        self.assertEqual(response.status_code, 302)
        update.refresh_from_db()
        self.assertEqual(update.report_date, datetime.date(2026, 5, 3))

    def test_assignment_detail_groups_progress_updates_by_month(self):
        assignment = self.create_assignment()
        MonthlyReport.objects.create(
            assignment=assignment,
            report_date=datetime.date(2026, 4, 5),
            content="עידכון ראשון",
        )
        MonthlyReport.objects.create(
            assignment=assignment,
            report_date=datetime.date(2026, 4, 18),
            content="עידכון שני",
        )
        self.client.force_login(self.tutor)

        response = self.client.get(f"/assignments/{assignment.id}/")

        self.assertContains(response, "2 עידכונים בחודש זה")
        self.assertContains(response, "05/04/2026")
        self.assertContains(response, "18/04/2026")
        self.assertContains(response, 'href="#activity-2026-04"')
        self.assertContains(response, 'href="#updates-2026-04"')

    def test_assignment_detail_shows_top_level_progress_update_button(self):
        assignment = self.create_assignment()
        self.client.force_login(self.tutor)

        response = self.client.get(f"/assignments/{assignment.id}/")

        self.assertContains(response, "הוסף עידכון התקדמות")
        self.assertContains(response, "הוסף שיעור")

    def test_assignment_detail_uses_singular_update_label_for_single_update(self):
        assignment = self.create_assignment()
        MonthlyReport.objects.create(
            assignment=assignment,
            report_date=datetime.date(2026, 4, 5),
            content="עידכון יחיד",
        )
        self.client.force_login(self.tutor)

        response = self.client.get(f"/assignments/{assignment.id}/")

        self.assertContains(response, "עידכון אחד בחודש זה")

    def test_session_create_page_renders_for_assignment(self):
        assignment = self.create_assignment()
        self.client.force_login(self.tutor)

        response = self.client.get(f"/assignment/{assignment.id}/sessions/create/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "הוספת שיעור עבור")

    def test_session_create_saves_and_redirects_to_assignment_month(self):
        assignment = self.create_assignment()
        self.client.force_login(self.tutor)

        response = self.client.post(
            f"/assignment/{assignment.id}/sessions/create/",
            data={
                "date": "10/04/2026",
                "duration": "01:00",
                "note": "חזרה",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Session.objects.filter(assignment=assignment).count(), 1)
        self.assertIn("#month-2026-04", response.url)
