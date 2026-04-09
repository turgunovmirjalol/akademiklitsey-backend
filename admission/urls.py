from django.urls import path
from .views import (
    AdmissionCurrentView, AdmissionHistoryView,
    AdmissionSubjectsView, AdmissionSubjectDetailView,
    AdmissionDocumentsView, AdmissionDocumentDetailView,
    FAQListView, FAQFeaturedView, FAQDetailView
)

app_name = 'admission'

urlpatterns = [
    # Qabul ma'lumotlari
    path('admission/current/', AdmissionCurrentView.as_view(), name='admission-current'),
    path('admission/history/', AdmissionHistoryView.as_view(), name='admission-history'),

    # Imtihon fanlari
    path('admission/subjects/', AdmissionSubjectsView.as_view(), name='admission-subjects'),
    path('admission/subjects/<int:pk>/', AdmissionSubjectDetailView.as_view(), name='admission-subject-detail'),

    # Talab qilinadigan hujjatlar
    path('admission/documents/', AdmissionDocumentsView.as_view(), name='admission-documents'),
    path('admission/documents/<int:pk>/', AdmissionDocumentDetailView.as_view(), name='admission-document-detail'),

    # FAQ lar
    path('faqs/', FAQListView.as_view(), name='faq-list'),
    path('faqs/featured/', FAQFeaturedView.as_view(), name='faq-featured'),
    path('faqs/<int:pk>/', FAQDetailView.as_view(), name='faq-detail'),
]
