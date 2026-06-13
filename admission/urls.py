from django.urls import path
from .views import (
    AdmissionCurrentView, AdmissionHistoryView,
    AdmissionSubjectListCreateView, AdmissionSubjectDetailView,
    AdmissionDocumentListCreateView, AdmissionDocumentDetailView,
    FAQListCreateView, FAQFeaturedView, FAQDetailView,
    DarsJadvaliListCreateView, DarsJadvaliDetailView,
)

app_name = 'admission'

urlpatterns = [
    # Qabul ma'lumotlari
    path('admission/current/', AdmissionCurrentView.as_view(), name='admission-current'),
    path('admission/history/', AdmissionHistoryView.as_view(), name='admission-history'),

    # Imtihon fanlari
    path('admission/subjects/', AdmissionSubjectListCreateView.as_view(), name='admission-subjects'),
    path('admission/subjects/<int:pk>/', AdmissionSubjectDetailView.as_view(), name='admission-subject-detail'),

    # Talab qilinadigan hujjatlar
    path('admission/documents/', AdmissionDocumentListCreateView.as_view(), name='admission-documents'),
    path('admission/documents/<int:pk>/', AdmissionDocumentDetailView.as_view(), name='admission-document-detail'),

    # FAQ lar
    path('faqs/', FAQListCreateView.as_view(), name='faq-list'),
    path('faqs/featured/', FAQFeaturedView.as_view(), name='faq-featured'),
    path('faqs/<int:pk>/', FAQDetailView.as_view(), name='faq-detail'),

    # Dars jadvali
    path('dars-jadvali/', DarsJadvaliListCreateView.as_view(), name='dars-jadvali-list'),
    path('dars-jadvali/<int:pk>/', DarsJadvaliDetailView.as_view(), name='dars-jadvali-detail'),
]
