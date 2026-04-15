from collections import OrderedDict
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
    MonthlyReport,
    Student,
    Session,
    HEBREW_MONTHS,
    format_duration_hhmm,
    month_label,
)
from .forms import (
    AssignmentForm,
    LoginForm,
    MonthlyReportForm,
    MonthPickerForm,
    SessionForm,
)


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


def build_assignment_month_sections(assignment):
    grouped_sessions = OrderedDict()
    reports_by_month = {
        report.month: report
        for report in assignment.monthlyreport_set.all()
    }

    for session in assignment.session_set.all():
        month_key = datetime.date(session.date.year, session.date.month, 1)
        if month_key not in grouped_sessions:
            grouped_sessions[month_key] = []
        grouped_sessions[month_key].append(session)

    month_sections = []
    for month_key, sessions in grouped_sessions.items():
        total_duration = sum(
            (session.duration or datetime.timedelta(0) for session in sessions),
            start=datetime.timedelta(0),
        )
        total_sessions = len(sessions)
        month_sections.append(
            {
                "month": month_key,
                "month_display": month_label(month_key),
                "sessions": sessions,
                "total_duration": format_duration_hhmm(total_duration),
                "total_earnings": total_sessions * assignment.session_rate,
                "total_sessions": total_sessions,
                "report": reports_by_month.get(month_key),
            }
        )

    return month_sections


# Create your views here.
class Home(LoginView):
    template_name = 'home.html'
    authentication_form = LoginForm

class AssignmentList(LoginRequiredMixin, ListView):
    model = Assignment

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Assignment.objects.all()
        else:
            return Assignment.objects.filter(tutor = self.request.user)

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
        context['session_form'] = SessionForm(
            initial={"duration": self.object.session_length}
        )
        context["month_sections"] = build_assignment_month_sections(self.object)
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
    fields = '__all__'

    def test_func(self):
        return self.request.user.is_superuser
    
def must_be_yours(func):
    def check_and_call(request, *args, **kwargs):
        pk = kwargs["pk"]
        assignment = Assignment.objects.get(pk=pk)
        if not (assignment.tutor.id == request.user.id) and not request.user.is_superuser:
            return HttpResponse("It is not your assignment! You are not permitted to add sessions to it!",
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

    def get_success_url(self):
        return reverse("assignment-detail", kwargs={"pk": self.object.assignment_id}) + "#previous-sessions"


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
    form = SessionForm(request.POST)
    if form.is_valid():
        new_session = form.save(commit=False)
        new_session.assignment_id = pk
        new_session.save()
        month_str = new_session.date.strftime('%Y-%m')
        return redirect(reverse('assignment-detail', kwargs={'pk': pk}) + f'#month-{month_str}')
    return redirect(reverse('assignment-detail', kwargs={'pk': pk}))

def calculate_totals(assignment, month, year):
    if month == 'all':
        sessions = Session.objects.filter(assignment__id=assignment.id) ## add a aggregation to return ordered by month for details page
        report = None
    else:
        sessions = Session.objects.filter(assignment__id=assignment.id).filter(date__month=month).filter(date__year=year)
        report = MonthlyReport.objects.filter(
            assignment_id=assignment.id,
            month=datetime.date(year, month, 1),
        ).first()
    total_sessions = sessions.count()
    total_earnings = total_sessions * assignment.session_rate
    assignment.total_sessions = total_sessions
    assignment.total_earnings = total_earnings
    assignment.monthly_report = report

    return assignment

@login_required
def dashboard(request):
    selected_month = month_start(datetime.date.today())

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

    assignments = ''
    if request.user.is_superuser:
        assignments = Assignment.objects.all()
    else:
        assignments = Assignment.objects.filter(tutor = request.user)

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
        'selected_month_value': selected_month.strftime("%Y-%m"),
        'prev_month_value': shift_month(selected_month, -1).strftime("%Y-%m"),
        'next_month_value': shift_month(selected_month, 1).strftime("%Y-%m"),
    })
