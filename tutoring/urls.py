from django.urls import path
from . import views

urlpatterns = [
    path('', views.Home.as_view(), name='home'),
    path('assignments/', views.AssignmentList.as_view(), name='assignment-list'),
    path('assignments/create', views.AssignmentCreate.as_view(), name='assignment-create'),
    path('assignments/<int:pk>/', views.AssignmentDetail.as_view(), name='assignment-detail'),
    path('assignment/<int:pk>/add-session/', views.add_session, name='add-session'),
    path('assignment/<int:pk>/update/', views.AssignmentUpdate.as_view(), name='assignment-update'),
    path('assignment/<int:pk>/delete/', views.AssignmentDelete.as_view(), name='assignment-delete'),
    path('student/create', views.StudentCreate.as_view(), name='student-create'),
]