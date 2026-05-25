from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from accounts.decorators import role_required
from .models import Appointment, Doctor
from accounts.models import CustomUser 
from datetime import datetime
from dashboard.utils import send_notification
import difflib 
from collections import defaultdict
import string

# ==========================================
#        SMART SYMPTOM LOGIC V2
# ==========================================

def analyze_symptoms(symptoms):
    """
    Scans paragraph text for medical keywords.
    Returns a dict of {Specialization: Score}.
    """
    symptoms_text = symptoms.lower()
    # Remove punctuation to handle "pain, fever." correctly
    symptoms_text = symptoms_text.translate(str.maketrans('', '', string.punctuation))
    user_words = symptoms_text.split()
    
    # Expanded Knowledge Base
    knowledge_base = {
        'Cardiologist': {'heart': 10, 'chest': 10, 'attack': 20, 'breath': 8, 'bp': 5, 'pulse': 5, 'palpitations': 8},
        'Dermatologist': {'skin': 10, 'rash': 10, 'acne': 8, 'hair': 5, 'itch': 5, 'spots': 5, 'allergy': 5},
        'Orthopedic': {'bone': 10, 'fracture': 20, 'joint': 10, 'knee': 10, 'back': 8, 'spine': 8, 'shoulder': 8, 'leg': 5, 'muscle': 5, 'ortho': 10},
        'Neurologist': {'headache': 10, 'migraine': 15, 'dizzy': 8, 'faint': 8, 'seizure': 20, 'numb': 8, 'memory': 5, 'brain': 15, 'neuro': 10},
        'Pediatrician': {'baby': 15, 'child': 10, 'infant': 15, 'growth': 5, 'vaccination': 10, 'kids': 5},
        'Dentist': {'tooth': 10, 'teeth': 10, 'gum': 8, 'cavity': 10, 'jaw': 8, 'mouth': 5, 'dental': 10},
        'ENT': {'ear': 10, 'throat': 10, 'nose': 8, 'sinus': 8, 'voice': 5, 'flu': 5, 'cold': 5, 'cough': 5},
        'Psychiatrist': {'depression': 15, 'anxiety': 10, 'mental': 10, 'stress': 8, 'sleep': 8, 'mood': 5, 'panic': 10},
        'Gynecologist': {'period': 10, 'pregnant': 20, 'pregnancy': 20, 'menstrual': 10, 'birth': 15, 'women': 5, 'cramps': 5}
    }
    
    scores = defaultdict(int)

    for word in user_words:
        for spec, keywords in knowledge_base.items():
            # 1. Exact Match
            if word in keywords:
                scores[spec] += keywords[word]
            else:
                # 2. Fuzzy Match (Typos)
                matches = difflib.get_close_matches(word, keywords.keys(), n=1, cutoff=0.85)
                if matches:
                    scores[spec] += keywords[matches[0]]

    return scores


@login_required
@role_required(allowed_roles=['patient'])
def symptom_check_view(request):
    """
    Stage 1: Input Symptoms
    Stage 2: Rate Severity (Explicit Tie-Breaker)
    Stage 3: Show Recommendations
    """
    
    # --- PHASE 2: HANDLE SEVERITY RATING & TIE-BREAKING ---
    if request.method == 'POST' and 'severity_rating' in request.POST:
        specs_str = request.POST.get('conflicting_specs', '') 
        symptoms_text = request.POST.get('original_symptoms', '')
        
        conflicting_specs = specs_str.split(',')
        user_ratings = {} # Store raw user ratings (1-10) to detect ties
        final_scores = {} # Store calculated weighted scores
        
        # 1. Capture Ratings
        for spec in conflicting_specs:
            try:
                rating = int(request.POST.get(f'rating_{spec}', 1)) # 1-10
            except ValueError:
                rating = 1
            
            user_ratings[spec] = rating
            
            # Calculate Weighted Score (Backup tie-breaker)
            ai_scores = analyze_symptoms(symptoms_text)
            base_score = ai_scores.get(spec, 0)
            final_scores[spec] = base_score * rating 

        # 2. STRICT TIE-BREAKER CHECK
        # Sort specs by User Rating ONLY first
        # [('Neurologist', 8), ('Orthopedic', 8)]
        sorted_by_rating = sorted(user_ratings.items(), key=lambda x: x[1], reverse=True)

        winner = None
        score = 0
        docs = []
        
        # If top 2 ratings are IDENTICAL (e.g., both 8/10), Force General Physician
        if len(sorted_by_rating) >= 2 and sorted_by_rating[0][1] == sorted_by_rating[1][1]:
            # Tie Detected -> Recommend General Physician
            winner = 'General Physician'
            docs = Doctor.objects.filter(specialization='General Physician').order_by('-experience_years')
            score = 0 # No specific score for fallback
        
        else:
            # No Rating Tie -> Pick the one with the highest User Rating
            # (If ratings are different, say 9 vs 8, the 9 wins regardless of AI weight)
            winner = sorted_by_rating[0][0]
            docs = Doctor.objects.filter(specialization=winner).select_related('user').order_by('-experience_years')
            score = final_scores[winner]

        results_groups = [{
            'specialization': winner,
            'doctors': docs,
            'score': score
        }]
        
        return render(request, 'appointments/symptom_check.html', {
            'is_result': True,
            'results_groups': results_groups,
            'symptoms': symptoms_text,
            'user_favorites': request.user.favorite_doctors.values_list('id', flat=True)
        })

    # --- PHASE 1: INITIAL SYMPTOM SUBMISSION ---
    if request.method == 'POST':
        symptoms = request.POST.get('symptoms')
        if not symptoms:
            messages.error(request, "Please describe your symptoms.")
            return redirect('symptom_check')
            
        scores = analyze_symptoms(symptoms)
        valid_scores = sorted([(k, v) for k, v in scores.items() if v > 0], key=lambda x: x[1], reverse=True)
        
        # CASE A: NO MATCH -> Fallback
        if not valid_scores:
            gp_docs = Doctor.objects.filter(specialization='General Physician').order_by('-experience_years')
            return render(request, 'appointments/symptom_check.html', {
                'is_result': True,
                'fallback': True,
                'symptoms': symptoms,
                'results_groups': [{'specialization': 'General Physician', 'doctors': gp_docs}]
            })

        # CASE B: SINGLE CLEAR WINNER
        # If only 1 match OR the top score is double the second score (Clear winner)
        if len(valid_scores) == 1 or (valid_scores[0][1] > valid_scores[1][1] * 2):
            winner = valid_scores[0][0]
            docs = Doctor.objects.filter(specialization=winner).order_by('-experience_years')
            return render(request, 'appointments/symptom_check.html', {
                'is_result': True,
                'results_groups': [{'specialization': winner, 'doctors': docs}],
                'symptoms': symptoms,
                'user_favorites': request.user.favorite_doctors.values_list('id', flat=True)
            })
            
        # CASE C: CONFLICT / MULTIPLE MATCHES -> ASK USER SEVERITY
        top_candidates = [x[0] for x in valid_scores[:3]] # Take top 3 max
        
        return render(request, 'appointments/symptom_check.html', {
            'ask_severity': True, # Trigger Modal/Form
            'candidates': top_candidates,
            'symptoms': symptoms
        })

    return render(request, 'appointments/symptom_check.html', {'is_result': False})


# ==========================================
#           SLOT LOCKING API (AJAX)
# ==========================================
@require_GET
@login_required
def get_booked_slots(request):
    """
    Returns a list of 'HH:MM' strings that are CONFIRMED for a doctor on a date.
    Used by frontend to disable buttons.
    """
    doctor_id = request.GET.get('doctor_id')
    date_str = request.GET.get('date') # YYYY-MM-DD
    
    if not doctor_id or not date_str:
        return JsonResponse({'slots': []})
    
    # Find confirmed appointments
    booked = Appointment.objects.filter(
        doctor_id=doctor_id, 
        date=date_str, 
        status='confirmed' # Only lock confirmed ones
    ).values_list('time', flat=True)
    
    # Convert time objects to "09:00" strings
    slots = [t.strftime('%H:%M') for t in booked]
    
    return JsonResponse({'slots': slots})


# ==========================================
#           FAVORITE TOGGLE API
# ==========================================
@login_required
def toggle_favorite_doctor(request, doctor_id):
    if request.method == 'POST':
        doctor = get_object_or_404(Doctor, id=doctor_id)
        if request.user in doctor.favorited_by.all():
            doctor.favorited_by.remove(request.user)
            liked = False
        else:
            doctor.favorited_by.add(request.user)
            liked = True
        return JsonResponse({'status': 'success', 'liked': liked})
    return JsonResponse({'status': 'error'}, status=400)


# ==========================================
#               BOOKING VIEW
# ==========================================
@login_required
@role_required(allowed_roles=['patient'])
def book_appointment_view(request):
    # Auto-Sync
    users = CustomUser.objects.filter(role='doctor')
    for u in users: Doctor.objects.get_or_create(user=u)

    # Logic to sort favorites
    all_docs = Doctor.objects.all().select_related('user')
    fav_ids = set(request.user.favorite_doctors.values_list('id', flat=True))
    sorted_docs = sorted(all_docs, key=lambda d: d.id in fav_ids, reverse=True)

    pre_selected_doctor_id = request.GET.get('doc_id')

    if request.method == 'POST':
        doctor_id = request.POST.get('doctor')
        date = request.POST.get('date')
        time = request.POST.get('time')
        reason = request.POST.get('reason')

        if not all([doctor_id, date, time]):
            messages.error(request, "Missing fields.")
            return redirect('book_appointment')
            
        # SERVER-SIDE LOCK CHECK
        # Before creating, ensure no one else confirmed this slot
        if Appointment.objects.filter(doctor_id=doctor_id, date=date, time=time, status='confirmed').exists():
            messages.error(request, "Sorry! This slot was just booked by someone else.")
            return redirect('book_appointment')

        doctor = get_object_or_404(Doctor, id=doctor_id)
        appointment = Appointment.objects.create(patient=request.user, doctor=doctor, date=date, time=time, reason=reason, status='pending')
        
        send_notification(doctor.user, f"New Request: {request.user.first_name} for {date} at {time}", 'appointment')
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'appointment_id': appointment.id})
            
        messages.success(request, "Request Sent! Waiting for doctor confirmation.")
        return redirect('patient_dashboard')

    return render(request, 'appointments/book_appointment.html', {
        'doctors': sorted_docs,
        'pre_selected_doctor_id': pre_selected_doctor_id,
        'user_favorites': fav_ids
    })

# ==========================================
#         OTHER PATIENT ACTIONS
# ==========================================

@login_required
@role_required(allowed_roles=['patient'])
def cancel_appointment_view(request, pk):
    appointment = get_object_or_404(Appointment, id=pk, patient=request.user)
    if appointment.status in ['pending', 'confirmed']:
        appointment.status = 'cancelled'
        appointment.save()
        send_notification(appointment.doctor.user, f"Appointment Cancelled by {request.user.first_name}", 'system')
        messages.success(request, "Appointment cancelled.")
    else:
        messages.error(request, "Cannot cancel this appointment.")
    return redirect('patient_dashboard')

@login_required
@role_required(allowed_roles=['patient'])
def appointment_history_view(request):
    appointments = Appointment.objects.filter(patient=request.user).order_by('-date', '-time')
    return render(request, 'appointments/appointment_history.html', {'appointments': appointments})


# ==========================================
#               DOCTOR VIEWS
# ==========================================

@login_required
@role_required(allowed_roles=['doctor'])
def confirm_appointment_view(request, pk):
    try: doctor_profile = request.user.doctor_profile
    except Doctor.DoesNotExist:
        messages.error(request, "Doctor profile missing.")
        return redirect('doctor_dashboard')
    
    appointment = get_object_or_404(Appointment, id=pk, doctor=doctor_profile)
    if appointment.status == 'pending':
        # Double Booking Guard
        if Appointment.objects.filter(doctor=doctor_profile, date=appointment.date, time=appointment.time, status='confirmed').exists():
             messages.error(request, "Slot conflict! You already have a confirmed appointment at this time.")
             return redirect('doctor_dashboard')

        appointment.status = 'confirmed'
        appointment.save()
        send_notification(appointment.patient, f"Confirmed by Dr. {doctor_profile.user.last_name}", 'appointment')
        messages.success(request, "Appointment confirmed.")
    return redirect('doctor_dashboard')

@login_required
@role_required(allowed_roles=['doctor'])
def complete_appointment_view(request, pk):
    try: doctor_profile = request.user.doctor_profile
    except Doctor.DoesNotExist:
        return redirect('doctor_dashboard')
    
    appointment = get_object_or_404(Appointment, id=pk, doctor=doctor_profile)
    if appointment.status == 'confirmed':
        appointment.status = 'completed'
        appointment.completed_at = datetime.now()
        appointment.save()
        messages.success(request, "Appointment marked as completed.")
        return redirect('doctor_upload_report', appointment_id=appointment.id)
    return redirect('doctor_dashboard')

