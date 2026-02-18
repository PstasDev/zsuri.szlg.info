from django.urls import path
from . import views

urlpatterns = [
    path('<int:event_id>/', views.event_detail, name='event_detail'),
    path('<int:event_id>/admin/', views.event_admin_dashboard, name='event_admin_dashboard'),
    path('<int:event_id>/results/overall/', views.event_results_overall, name='event_results_overall'),
    path('<int:event_id>/results/detailed/', views.event_results_detailed, name='event_results_detailed'),
]
