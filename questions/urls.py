from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('hot/', views.hot_questions, name='hot'),
    path('tag/<str:tag_name>/', views.tag_questions, name='tag'),
    path('question/<int:question_id>/', views.question_detail, name='question'),
    path('ask/', views.ask_view, name='ask'),
]