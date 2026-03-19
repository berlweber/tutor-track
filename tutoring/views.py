from django.shortcuts import redirect, render
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.generic import  ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_protect
import datetime

from .models import Assignment, Student, Session
from .forms import SessionForm

# Create your views here.
class Home(LoginView):
    template_name = 'home.html'

class AssignmentList(LoginRequiredMixin, ListView):
    model = Assignment

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Assignment.objects.all()
        else:
            return Assignment.objects.filter(tutor = self.request.user)

class AssignmentCreate(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Assignment
    fields = '__all__'

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    
class AssignmentDetail(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Assignment

    def test_func(self): 
        obj = self.get_object()
        return self.request.user.is_superuser or obj.tutor == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['session_form'] = SessionForm()
        return context

class AssignmentUpdate(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Assignment
    fields = ['goal', 'hourly_rate', 'sponsor', 'start_time', 'end_time']

    def test_func(self):
        return self.request.user.is_superuser

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

@must_be_yours
@csrf_protect
@login_required
def add_session(request, pk):
    form = SessionForm(request.POST)
    if form.is_valid():
        new_session = form.save(commit=False)
        new_session.assignment_id = pk
        new_session.save()
    return redirect('assignment-detail', pk=pk)

def calculate_totals(assignment):
    sessions = Session.objects.filter(assignment__id=assignment.id)
    # create a list and fill it with all the timedelta's /duration in a second's format, which counnts as here as minutes
    durations_list = []
    for session in sessions:
        durations_list.append(session.duration)
        
    # sums up all timedelta's/durations in to one number, 
    # get the total second (which counts as minutes) as a normal int, finaly, multilplies it  by 60 to get the total hours
    total_hours = sum(durations_list, start=datetime.timedelta(0)).total_seconds() / 60
    total_earnings = total_hours * assignment.hourly_rate
    assignment.total_hours = total_hours
    assignment.total_earnings = total_earnings

    return assignment

        # breakpoint()

# assignments = Assignment.objects.all()
# calculate_totals_for_sponsors(assignments)
# print('printing', sessions[1].duration + sessions[2].duration)

@login_required
def dashboard(request):
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
        assignment = calculate_totals(assignment)
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
        'grand_total': grand_total
    })