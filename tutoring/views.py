from django.shortcuts import redirect, render
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.generic import  ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_protect

from .models import Assignment, Student
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
        if not (assignment.tutor.id == request.user.id) or request.user.is_superuser: 
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