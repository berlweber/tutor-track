from django.urls import path
from . import views

urlpatterns = [
    path('', views.Home.as_view(), name='home'),
    path('assignments/', views.AssignmentList.as_view(), name='assignment-list'),
    path('assignments/create', views.AssignmentCreate.as_view(), name='assignment-create'),
    path('assignments/<int:pk>/', views.AssignmentDetail.as_view(), name='assignment-detail'),
    path('assignment/<int:pk>/add-session/', views.add_session, name='add-session'),
    path('sessions/<int:pk>/update/', views.SessionUpdate.as_view(), name='session-update'),
    path('sessions/<int:pk>/delete/', views.SessionDelete.as_view(), name='session-delete'),
    path('assignment/<int:pk>/update/', views.AssignmentUpdate.as_view(), name='assignment-update'),
    path('assignment/<int:pk>/delete/', views.AssignmentDelete.as_view(), name='assignment-delete'),
    path('assignment/<int:pk>/reports/create/', views.MonthlyReportCreate.as_view(), name='report-create'),
    path('reports/<int:pk>/update/', views.MonthlyReportUpdate.as_view(), name='report-update'),
    path('reports/<int:pk>/delete/', views.MonthlyReportDelete.as_view(), name='report-delete'),
    path('student/create', views.StudentCreate.as_view(), name='student-create'),
    path('assignments/dashboard/', views.dashboard, name='dashboard'),
]
