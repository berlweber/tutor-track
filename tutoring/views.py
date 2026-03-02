from django.shortcuts import redirect, render
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.generic import  ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from .models import Assignment, Student
from .forms import SessionForm

# Create your views here.
class Home(LoginView):
    template_name = 'home.html'
    

class AssignmentList(ListView):
    model = Assignment

class AssignmentCreate(CreateView):
    model = Assignment
    fields = '__all__'

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    
class AssignmentDetail(DetailView):
    model = Assignment

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['session_form'] = SessionForm()
        return context

class AssignmentUpdate(UpdateView):
    model = Assignment
    fields = ['goal', 'hourly_rate', 'sponsor', 'start_time', 'end_time']

class AssignmentDelete(DeleteView):
    model = Assignment
    success_url = reverse_lazy('assignment-list')

class StudentCreate(CreateView):
    model = Student
    fields = '__all__'

def add_session(request, pk):
    form = SessionForm(request.POST)
    if form.is_valid():
        new_session = form.save(commit=False)
        new_session.assignment_id = pk
        new_session.save()
    return redirect('assignment-detail', pk=pk)