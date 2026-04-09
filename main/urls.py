from django.urls import path
from .views import StatisticListCreateView, StatisticDetailView, StatisticBulkUpdateView

app_name = 'main'

urlpatterns = [
    # GET  — barcha statistikalar (?lang= bilan til filtri)
    # POST — yangi statistika yaratish (admin)
    path('statistics/', StatisticListCreateView.as_view(), name='statistic-list-create'),

    # GET    — bitta statistika
    # PUT    — to'liq yangilash (admin)
    # PATCH  — qisman yangilash (admin)
    # DELETE — o'chirish (admin)
    path('statistics/<int:pk>/', StatisticDetailView.as_view(), name='statistic-detail'),

    # POST — bir nechta statistikani bir vaqtda yangilash (admin)
    path('statistics/bulk-update/', StatisticBulkUpdateView.as_view(), name='statistic-bulk-update'),
]
