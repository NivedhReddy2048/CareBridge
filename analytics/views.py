from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def admin_dashboard(request):
    """Renders the Super-Admin Analytics Dashboard using Bootstrap and Chart.js"""
    return render(request, 'analytics/admin_dashboard.html')
