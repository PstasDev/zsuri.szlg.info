from django.urls import path
from . import views

urlpatterns = [
    path('<int:event_id>/category/<int:category_id>/', views.vote_category, name='vote_category'),
]
