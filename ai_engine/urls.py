from django.urls import path
from . import apis

app_name = 'ai_engine'

urlpatterns = [
    path('triage/', apis.TriageAPIView.as_view(), name='triage'),
    path('summarize-report/', apis.SummarizeReportAPIView.as_view(), name='summarize_report'),
    path('recommend-doctors/', apis.RecommendDoctorsAPIView.as_view(), name='recommend_doctors'),
    path('chatbot/', apis.ChatbotAPIView.as_view(), name='chatbot'),
]
