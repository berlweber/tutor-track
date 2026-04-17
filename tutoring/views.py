from collections import OrderedDict
from django.db.models import Case, CharField, F, Value, When
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.views import LoginView
from django.urls import reverse, reverse_lazy
from django.views.generic import  ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_protect
import datetime

from .models import (
    Assignment,
    AttendanceAdjustment,
    MonthlyReport,
    Student,
    Session,
    HEBREW_MONTHS,
    format_duration_hhmm,
    month_label,
)
from .forms import (
    AssignmentForm,
    AttendanceAdjustmentForm,
    LoginForm,
    MonthlyReportForm,
    MonthPickerForm,
    SessionForm,
    StudentForm,
)


SORT_BY_STUDENT = "student"
SORT_BY_TUTOR = "tutor"
ASSIGNMENT_SORT_CHOICES = {SORT_BY_STUDENT, SORT_BY_TUTOR}


def calculate_session_length(start_time, end_time):
    start_dt = datetime.datetime.combine(datetime.date.today(), start_time)
    end_dt = datetime.datetime.combine(datetime.date.today(), end_time)
    return end_dt - start_dt


def month_start(date_value):
    return date_value.replace(day=1)


def shift_month(date_value, delta):
    year = date_value.year + ((date_value.month - 1 + delta) // 12)
    month = ((date_value.month - 1 + delta) % 12) + 1
    return datetime.date(year, month, 1)


def get_assignment_sort_mode(request):
    sort_mode = request.GET.get("sort", SORT_BY_STUDENT)
    if sort_mode not in ASSIGNMENT_SORT_CHOICES:
        return SORT_BY_STUDENT
    return sort_mode


def user_last_name_for_sort(user):
    if not user:
        return ""
    return (user.last_name or user.username or "").strip()


def user_first_name_for_sort(user):
    if not user:
        return ""
    return (user.first_name or user.username or "").strip()


def assignment_sort_key(assignment, sort_mode):
    student_last_name = assignment.student.resolved_last_name
    student_first_name = (assignment.student.first_name or "").strip()
    tutor_last_name = user_last_name_for_sort(assignment.tutor)
    tutor_first_name = user_first_name_for_sort(assignment.tutor)

    if sort_mode == SORT_BY_TUTOR:
        return (
            tutor_last_name,
            tutor_first_name,
            student_last_name,
            student_first_name,
            assignment.pk,
        )

    return (
        student_last_name,
        student_first_name,
        tutor_last_name,
        tutor_first_name,
        assignment.pk,
    )


def sort_assignments_for_display(assignments, sort_mode):
    return sorted(assignments, key=lambda assignment: assignment_sort_key(assignment, sort_mode))


def order_assignments_queryset(queryset, sort_mode):
    queryset = queryset.annotate(
        student_last_name_sort=Case(
            When(student__last_name="", then=F("student__name")),
            default=F("student__last_name"),
            output_field=CharField(),
        ),
        tutor_last_name_sort=Case(
            When(tutor__last_name="", then=F("tutor__username")),
            default=F("tutor__last_name"),
            output_field=CharField(),
        ),
        tutor_first_name_sort=Case(
            When(tutor__first_name="", then=F("tutor__username")),
            default=F("tutor__first_name"),
            output_field=CharField(),
        ),
        student_first_name_sort=Case(
            When(student__first_name="", then=Value("")),
            default=F("student__first_name"),
            output_field=CharField(),
        ),
    )

    if sort_mode == SORT_BY_TUTOR:
        return queryset.order_by(
            "tutor_last_name_sort",
            "tutor_first_name_sort",
            "student_last_name_sort",
            "student_first_name_sort",
            "pk",
        )

    return queryset.order_by(
        "student_last_name_sort",
        "student_first_name_sort",
        "tutor_last_name_sort",
        "tutor_first_name_sort",
        "pk",
    )


def get_visible_assignments(request):
    queryset = Assignment.objects.select_related("student", "tutor")
    if request.user.is_superuser:
        return queryset
    return queryset.filter(tutor=request.user)


def build_assignment_month_sections(assignment):
    grouped_items = OrderedDict()
    reports_by_month = {
        report.month: report
        for report in assignment.monthlyreport_set.all()
    }

    if assignment.is_monthly_billing:
        for adjustment in assignment.attendanceadjustment_set.all():
            month_key = datetime.date(adjustment.date.year, adjustment.date.month, 1)
            if month_key not in grouped_items:
                grouped_items[month_key] = []
            grouped_items[month_key].append(adjustment)
    else:
        for session in assignment.session_set.all():
            month_key = datetime.date(session.date.year, session.date.month, 1)
            if month_key not in grouped_items:
                grouped_items[month_key] = []
            grouped_items[month_key].append(session)

    for report_month in reports_by_month:
        grouped_items.setdefault(report_month, [])

    month_sections = []
    for month_key in sorted(grouped_items.keys(), reverse=True):
        month_items = grouped_items[month_key]
        if assignment.is_monthly_billing:
            total_adjustments = len(month_items)
            total_reduction = sum(
                (adjustment.deduction_amount for adjustment in month_items),
                start=0,
            )
            month_sections.append(
                {
                    "month": month_key,
                    "month_display": month_label(month_key),
                    "adjustments": month_items,
                    "total_adjustments": total_adjustments,
                    "total_reduction": total_reduction,
                    "total_earnings": (assignment.monthly_rate or 0) - total_reduction,
                    "report": reports_by_month.get(month_key),
                }
            )
        else:
            total_duration = sum(
                (session.duration or datetime.timedelta(0) for session in month_items),
                start=datetime.timedelta(0),
            )
            total_sessions = len(month_items)
            month_sections.append(
                {
                    "month": month_key,
                    "month_display": month_label(month_key),
                    "sessions": month_items,
                    "total_duration": format_duration_hhmm(total_duration),
                    "total_earnings": total_sessions * assignment.session_rate,
                    "total_sessions": total_sessions,
                    "report": reports_by_month.get(month_key),
                }
            )

    return month_sections


def build_assignment_detail_context(assignment, *, session_form=None, adjustment_form=None):
    context = {
        "assignment": assignment,
        "month_sections": build_assignment_month_sections(assignment),
    }
    if assignment.is_monthly_billing:
        context["adjustment_form"] = adjustment_form or AttendanceAdjustmentForm()
    else:
        context["session_form"] = session_form or SessionForm(
            initial={"duration": assignment.session_length}
        )
    return context


# Create your views here.
class Home(LoginView):
    template_name = 'home.html'
    authentication_form = LoginForm

class AssignmentList(LoginRequiredMixin, ListView):
    model = Assignment
    template_name = "tutoring/assignment_list.html"

    def get_queryset(self):
        assignments = get_visible_assignments(self.request)
        return order_assignments_queryset(assignments, get_assignment_sort_mode(self.request))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_sort"] = get_assignment_sort_mode(self.request)
        return context

class AssignmentCreate(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Assignment
    form_class = AssignmentForm

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        form.instance.session_length = calculate_session_length(
            form.instance.start_time,
            form.instance.end_time,
        )
        return super().form_valid(form)
    
class AssignmentDetail(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Assignment

    def test_func(self): 
        obj = self.get_object()
        return self.request.user.is_superuser or obj.tutor == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(build_assignment_detail_context(self.object))
        return context

class AssignmentUpdate(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Assignment
    form_class = AssignmentForm

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        form.instance.session_length = calculate_session_length(
            form.instance.start_time,
            form.instance.end_time,
        )
        return super().form_valid(form)

class AssignmentDelete(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Assignment
    success_url = reverse_lazy('assignment-list')

    def test_func(self):
        return self.request.user.is_superuser

class StudentCreate(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Student
    form_class = StudentForm

    def test_func(self):
        return self.request.user.is_superuser
    
def must_be_yours(func):
    def check_and_call(request, *args, **kwargs):
        pk = kwargs["pk"]
        assignment = Assignment.objects.get(pk=pk)
        if not (assignment.tutor.id == request.user.id) and not request.user.is_superuser:
            return HttpResponse("It is not your assignment! You are not permitted to update it!",
                        content_type="application/json", status=403)
        return func(request, *args, **kwargs)
    return check_and_call


class AssignmentOwnerMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        obj = self.get_object()
        assignment = getattr(obj, "assignment", obj)
        return self.request.user.is_superuser or assignment.tutor == self.request.user


class SessionUpdate(AssignmentOwnerMixin, UpdateView):
    model = Session
    form_class = SessionForm
    template_name = "tutoring/session_form.html"

    def get_success_url(self):
        month_str = self.object.date.strftime('%Y-%m')
        return reverse("assignment-detail", kwargs={"pk": self.object.assignment_id}) + f"#month-{month_str}"


class SessionDelete(AssignmentOwnerMixin, DeleteView):
    model = Session
    template_name = "tutoring/session_confirm_delete.html"

    def get_success_url(self):
        month_str = self.object.date.strftime('%Y-%m')
        return reverse("assignment-detail", kwargs={"pk": self.object.assignment_id}) + f"#month-{month_str}"


class AttendanceAdjustmentUpdate(AssignmentOwnerMixin, UpdateView):
    model = AttendanceAdjustment
    form_class = AttendanceAdjustmentForm
    template_name = "tutoring/adjustment_form.html"

    def get_success_url(self):
        month_str = self.object.date.strftime('%Y-%m')
        return reverse("assignment-detail", kwargs={"pk": self.object.assignment_id}) + f"#month-{month_str}"


class AttendanceAdjustmentDelete(AssignmentOwnerMixin, DeleteView):
    model = AttendanceAdjustment
    template_name = "tutoring/adjustment_confirm_delete.html"

    def get_success_url(self):
        month_str = self.object.date.strftime('%Y-%m')
        return reverse("assignment-detail", kwargs={"pk": self.object.assignment_id}) + f"#month-{month_str}"


class MonthlyReportCreate(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = MonthlyReport
    form_class = MonthlyReportForm
    template_name = "tutoring/report_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.assignment = get_object_or_404(Assignment, pk=self.kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        return self.request.user.is_superuser or self.assignment.tutor == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["assignment"] = self.assignment
        return context

    def get_initial(self):
        initial = super().get_initial()
        month_value = self.request.GET.get("month")
        if month_value:
            try:
                initial["month"] = datetime.datetime.strptime(month_value, "%Y-%m").date()
            except ValueError:
                pass
        return initial

    def form_valid(self, form):
        if MonthlyReport.objects.filter(
            assignment=self.assignment,
            month=form.cleaned_data["month"],
        ).exists():
            form.add_error("month", "כבר קיים דוח לחודש הזה עבור השיבוץ הזה.")
            return self.form_invalid(form)
        form.instance.assignment = self.assignment
        return super().form_valid(form)

    def get_success_url(self):
        # Get the month from the object after it's been saved
        month_str = self.object.month.strftime('%Y-%m')
        return reverse("assignment-detail", kwargs={"pk": self.assignment.id}) + f"#month-{month_str}"


class MonthlyReportUpdate(AssignmentOwnerMixin, UpdateView):
    model = MonthlyReport
    form_class = MonthlyReportForm
    template_name = "tutoring/report_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["assignment"] = self.object.assignment
        return context

    def form_valid(self, form):
        if MonthlyReport.objects.filter(
            assignment=self.object.assignment,
            month=form.cleaned_data["month"],
        ).exclude(pk=self.object.pk).exists():
            form.add_error("month", "כבר קיים דוח לחודש הזה עבור השיבוץ הזה.")
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        month_str = self.object.month.strftime('%Y-%m')
        return reverse("assignment-detail", kwargs={"pk": self.object.assignment_id}) + f"#month-{month_str}"


class MonthlyReportDelete(AssignmentOwnerMixin, DeleteView):
    model = MonthlyReport
    template_name = "tutoring/report_confirm_delete.html"

    def get_success_url(self):
        month_str = self.object.month.strftime('%Y-%m')
        return reverse("assignment-detail", kwargs={"pk": self.object.assignment_id}) + f"#month-{month_str}"

@must_be_yours
@csrf_protect
@login_required
def add_session(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    if assignment.is_monthly_billing:
        return redirect(reverse('assignment-detail', kwargs={'pk': pk}))
    form = SessionForm(request.POST)
    if form.is_valid():
        new_session = form.save(commit=False)
        new_session.assignment_id = pk
        new_session.save()
        month_str = new_session.date.strftime('%Y-%m')
        return redirect(reverse('assignment-detail', kwargs={'pk': pk}) + f'#month-{month_str}')
    return render(
        request,
        "tutoring/assignment_detail.html",
        build_assignment_detail_context(assignment, session_form=form),
        status=400,
    )


@must_be_yours
@csrf_protect
@login_required
def add_adjustment(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    if assignment.is_session_billing:
        return redirect(reverse('assignment-detail', kwargs={'pk': pk}))

    form = AttendanceAdjustmentForm(request.POST)
    if form.is_valid():
        new_adjustment = form.save(commit=False)
        new_adjustment.assignment_id = pk
        new_adjustment.save()
        month_str = new_adjustment.date.strftime('%Y-%m')
        return redirect(reverse('assignment-detail', kwargs={'pk': pk}) + f'#month-{month_str}')
    return redirect(reverse('assignment-detail', kwargs={'pk': pk}))

def calculate_totals(assignment, month, year):
    if month == 'all':
        sessions = Session.objects.filter(assignment__id=assignment.id)
        adjustments = AttendanceAdjustment.objects.filter(assignment__id=assignment.id)
        report = None
    else:
        sessions = Session.objects.filter(assignment__id=assignment.id).filter(date__month=month).filter(date__year=year)
        adjustments = AttendanceAdjustment.objects.filter(assignment__id=assignment.id).filter(date__month=month).filter(date__year=year)
        report = MonthlyReport.objects.filter(
            assignment_id=assignment.id,
            month=datetime.date(year, month, 1),
        ).first()

    total_sessions = sessions.count()
    total_adjustments = adjustments.count()
    if assignment.is_monthly_billing:
        total_reduction = sum(
            (adjustment.deduction_amount for adjustment in adjustments),
            start=0,
        )
        total_earnings = (assignment.monthly_rate or 0) - total_reduction
        assignment.activity_count = total_adjustments
        assignment.activity_label = "הפחתות"
    else:
        total_earnings = total_sessions * assignment.session_rate
        assignment.activity_count = total_sessions
        assignment.activity_label = "שיעורים"

    assignment.total_sessions = total_sessions
    assignment.total_adjustments = total_adjustments
    assignment.total_earnings = total_earnings
    assignment.monthly_report = report

    return assignment

@login_required
def dashboard(request):
    selected_month = month_start(datetime.date.today())
    current_sort = get_assignment_sort_mode(request)

    if request.method == 'GET':
        form = MonthPickerForm(request.GET)
        if form.is_valid():
            selected_month = month_start(form.cleaned_data["month"])
            if request.GET.get("move") in {"prev", "next"}:
                selected_month = shift_month(
                    selected_month,
                    -1 if request.GET["move"] == "prev" else 1,
                )
                form = MonthPickerForm(initial={"month": selected_month})
    else:
        form = MonthPickerForm(initial={"month": selected_month})

    year = selected_month.year
    month = selected_month.month

    assignments = order_assignments_queryset(get_visible_assignments(request), current_sort)

    school_assignments = []
    parents_assignments = []
    fund_assignments = []
    school_total_cost = 0
    parents_total_cost = 0
    fund_total_cost = 0
    for assignment in assignments:
        assignment = calculate_totals(assignment, month, year)
        if assignment.sponsor == 'S':
            school_assignments.append(assignment)
            school_total_cost = school_total_cost + assignment.total_earnings
        elif assignment.sponsor == 'P':
            parents_assignments.append(assignment)
            parents_total_cost = parents_total_cost + assignment.total_earnings
        else:
            fund_assignments.append(assignment)
            fund_total_cost = fund_total_cost + assignment.total_earnings

    grand_total = school_total_cost + parents_total_cost + fund_total_cost

    return render(request, 'tutoring/dashboard.html', {
        'school_assignments': school_assignments,
        'parents_assignments': parents_assignments,
        'fund_assignments': fund_assignments,
        'school_total_cost': school_total_cost,
        'parents_total_cost': parents_total_cost,
        'fund_total_cost': fund_total_cost,
        'grand_total': grand_total,
        'month': HEBREW_MONTHS[month],
        'year': year,
        'month_picker': form,
        'current_sort': current_sort,
        'selected_month_value': selected_month.strftime("%Y-%m"),
        'prev_month_value': shift_month(selected_month, -1).strftime("%Y-%m"),
        'next_month_value': shift_month(selected_month, 1).strftime("%Y-%m"),
    })
