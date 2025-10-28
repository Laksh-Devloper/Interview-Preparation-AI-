from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_resume, name='upload_resume'),
    path('interview/', views.interview_session, name='interview_session'),  # Add this line
    path('api/questions/', views.generate_questions, name='generate_questions'),  # Add this line
    path('api/analyze/', views.analyze_response, name='analyze_response'),  # Add this line
    path('api/report/', views.generate_report, name='generate_report'),  # Add this line
    path('results/', views.interview_results, name='interview_results'),  # Add this line
    path('success/', views.upload_success, name='upload_success'),
    path('api/save-results/', views.save_interview_results, name='save_results'),  # 👈 ADD THIS
    path('api/calculate-score/', views.calculate_score, name='calculate_score'),
    path('personality/', views.select_personality, name='select_personality'),
]