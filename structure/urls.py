from django.urls import path
from .views import (
    DepartmentListView, DepartmentDetailView,
    TeacherListView, TeacherDetailView, TeacherByDepartmentView,
    ManagementListView, ManagementDetailView
)

app_name = 'structure'

urlpatterns = [
    # Department endpoints
    path('departments/', DepartmentListView.as_view(), name='department-list'),
    path('departments/<slug:slug>/', DepartmentDetailView.as_view(), name='department-detail'),
    
    # Teacher endpoints
    path('teachers/', TeacherListView.as_view(), name='teacher-list'),
    path('teachers/<slug:slug>/', TeacherDetailView.as_view(), name='teacher-detail'),
    path('teachers/by-department/<int:department_id>/', TeacherByDepartmentView.as_view(), name='teacher-by-department'),
    
    # Management endpoints
    path('management/', ManagementListView.as_view(), name='management-list'),
    path('management/<int:pk>/', ManagementDetailView.as_view(), name='management-detail'),
]
