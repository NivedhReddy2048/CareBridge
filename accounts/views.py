import csv
import io
import random
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction 

from appointments.models import Doctor 
from .decorators import role_required 

from .forms import (
    PatientRegistrationForm, 
    PatientLoginForm, 
    StaffLoginForm, 
    UserProfileForm,
    DoctorCreationForm,
    DoctorBulkUploadForm 
)

User = get_user_model()

# ==========================================
# 1. LANDING PAGE
# ==========================================
def home_view(request):
    return render(request, 'home.html')

# ==========================================
# 2. PATIENT LOGIN
# ==========================================
@never_cache
def patient_login_view(request):
    if request.user.is_authenticated:
        return redirect('patient_dashboard')

    if request.method == 'POST':
        form = PatientLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_active:
                messages.error(request, "Account not activated. Please verify your email.")
                return redirect('patient_login')
                
            login(request, user)
            if 'next' in request.GET:
                return redirect(request.GET.get('next'))
            return redirect('patient_dashboard')
        else:
            messages.error(request, "Invalid Credentials")
    else:
        form = PatientLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})

# ==========================================
# 3. STAFF LOGIN
# ==========================================
@never_cache
def staff_login_view(request):
    if request.user.is_authenticated:
        if request.user.role == 'doctor':
            return redirect('doctor_dashboard')
        elif request.user.role == 'admin':
            return redirect('/admin/')

    if request.method == 'POST':
        form = StaffLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.role == 'doctor':
                return redirect('doctor_dashboard')
            elif user.role == 'admin':
                return redirect('/admin/')
            else:
                return redirect('home')
        else:
            messages.error(request, "Invalid Staff ID or Password")
    else:
        form = StaffLoginForm()
    
    return render(request, 'accounts/staff_login.html', {'form': form})

# ==========================================
# 4. REGISTRATION
# ==========================================
@never_cache
def register_view(request):
    if request.user.is_authenticated:
        return redirect('patient_dashboard')

    if request.method == 'POST':
        import traceback
        import logging
        import time

        logger = logging.getLogger(__name__)
        start = time.time()

        try:
            form = PatientRegistrationForm(request.POST, request.FILES)
            
            if form.is_valid():
                user = form.save(commit=False)
                user.is_active = False 
                user.save()
                
                otp = str(random.randint(100000, 999999))
                request.session['reg_otp'] = otp
                request.session['reg_user_id'] = user.id
                request.session['reg_email'] = user.email
                
                try:
                    from django.core.mail import get_connection
                    connection = get_connection(timeout=10)
                    send_mail(
                        subject='CareBridge - Verify Your Account',
                        message=f'Welcome {user.first_name}!\n\nYour verification code is: {otp}',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=False,
                        connection=connection
                    )
                    logger.info(f"Successfully sent OTP email to {user.email} (OTP: {otp})")
                    messages.success(request, f"Verification code sent to {user.email}")
                    return redirect('verify_otp')
                    
                except Exception as e:
                    logger.exception("EMAIL SEND EXCEPTION:")
                    import traceback
                    print("\n=== EMAIL SEND FAILURE ===")
                    traceback.print_exc()
                    print("==========================\n")
                    user.delete()
                    messages.error(request, f"Error sending email. Registration cancelled. Error: {str(e)}")
            else:
                messages.error(request, "Registration Failed. Please check inputs.")
        except Exception as e:
            logger.exception("REGISTRATION ERROR:")
            print(traceback.format_exc())
            raise
        finally:
            print(f"REGISTRATION TOOK {time.time() - start} seconds")
    else:
        form = PatientRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

# ==========================================
# 5. OTP VERIFICATION
# ==========================================
@never_cache
def verify_otp_view(request):
    if 'reg_user_id' not in request.session:
        messages.error(request, "Session expired. Please register again.")
        return redirect('register')

    email = request.session.get('reg_email')

    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        session_otp = request.session.get('reg_otp')
        user_id = request.session.get('reg_user_id')

        if entered_otp == session_otp:
            try:
                user = User.objects.get(id=user_id)
                user.is_active = True
                user.save()
                
                del request.session['reg_otp']
                del request.session['reg_user_id']
                del request.session['reg_email']
                
                messages.success(request, "Account verified! You can now login.")
                return redirect('patient_login')
                
            except User.DoesNotExist:
                messages.error(request, "User not found. Register again.")
                return redirect('register')
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, 'accounts/verify_otp.html', {'email': email})

# ==========================================
# 6. LOGOUT
# ==========================================
def logout_view(request):
    logout(request)
    return redirect('home')

# ==========================================
# 7. PROFILE EDIT
# ==========================================
@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            
            if request.user.role == 'patient':
                return redirect('patient_dashboard')
            elif request.user.role == 'doctor':
                return redirect('doctor_dashboard')
            else:
                return redirect('home')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'accounts/edit_profile.html', {'form': form})

# ==========================================
# 8. STAFF PASSWORD RESET
# ==========================================
def staff_password_reset(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        if not username:
            messages.error(request, "Please enter your Staff ID.")
            return render(request, 'accounts/staff_password_reset.html')
        try:
            user = User.objects.get(username=username)
            if user.role not in ['doctor', 'admin']:
                messages.error(request, "This ID is not authorized.")
                return render(request, 'accounts/staff_password_reset.html')
            otp = str(random.randint(100000, 999999))
            request.session['reset_otp'] = otp
            request.session['reset_user_id'] = user.id
            send_mail(
                'Staff Password Reset',
                f'Your code is: {otp}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True
            )
            messages.success(request, f"Code sent to email linked to {username}")
            return redirect('staff_password_reset_verify')
        except User.DoesNotExist:
            messages.error(request, "Staff ID not found.")
    return render(request, 'accounts/staff_password_reset.html')

def staff_password_reset_verify(request):
    if 'reset_otp' not in request.session:
        return redirect('staff_password_reset')
    if request.method == 'POST':
        entered = request.POST.get('otp')
        actual = request.session.get('reset_otp')
        if entered == actual:
            request.session['reset_verified'] = True
            return redirect('staff_password_reset_confirm')
        else:
            messages.error(request, "Invalid Code.")
    return render(request, 'accounts/staff_password_reset_verify.html')

def staff_password_reset_confirm(request):
    if not request.session.get('reset_verified'):
        return redirect('staff_password_reset')
    if request.method == 'POST':
        p1 = request.POST.get('new_password')
        p2 = request.POST.get('confirm_password')
        uid = request.session.get('reset_user_id')
        if p1 == p2:
            user = User.objects.get(id=uid)
            user.set_password(p1)
            user.save()
            del request.session['reset_otp']
            del request.session['reset_user_id']
            del request.session['reset_verified']
            messages.success(request, "Password reset! Please login.")
            return redirect('staff_login')
        else:
            messages.error(request, "Passwords do not match.")
    return render(request, 'accounts/staff_password_reset_confirm.html')

# ==========================================
# 9. GENERAL HELPERS
# ==========================================
def resend_otp_view(request):
    import traceback
    import logging
    import time

    logger = logging.getLogger(__name__)
    start = time.time()

    try:
        if 'reg_otp' in request.session and 'reg_email' in request.session:
            otp = request.session['reg_otp']
            email = request.session['reg_email']
            
            from django.core.mail import get_connection
            connection = get_connection(timeout=10)
            send_mail(
                'Resend: Verification Code',
                f'Your code is: {otp}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
                connection=connection
            )
            logger.info(f"Successfully resent OTP email to {email} (OTP: {otp})")
            messages.success(request, "OTP resent successfully.")
    except Exception as e:
        logger.exception("RESEND OTP ERROR:")
        print(traceback.format_exc())
        messages.error(request, f"Error sending verification email: {str(e)}")
    finally:
        print(f"RESEND OTP TOOK {time.time() - start} seconds")
    return redirect('verify_otp')

def verify_otp_view_placeholder(request):
    return redirect('verify_otp')

# ==========================================
# 10. DOCTOR CREATION (SINGLE ENTRY)
# ==========================================
@login_required
@role_required(allowed_roles=['admin'])
def add_doctor_view(request):
    if request.method == 'POST':
        form = DoctorCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Doctor added successfully! Specialization & Department synced.")
            return redirect('/admin/') 
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = DoctorCreationForm()

    return render(request, 'accounts/add_doctor.html', {'form': form})

# ==========================================
# 11. BULK UPLOAD DOCTORS (SMART CSV)
# ==========================================
@login_required
@role_required(allowed_roles=['admin'])
def bulk_upload_doctors_view(request):
    """
    Reads a CSV file, intelligently maps columns (handling variations like 'Email Address' vs 'email'),
    creates Doctor User accounts with UNIQUE UUID usernames in format dXXXXXXcb, 
    and automatically syncs their Profile & Department.
    """
    if request.method == "POST":
        form = DoctorBulkUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            
            if not csv_file.name.endswith('.csv'):
                messages.error(request, "Please upload a valid CSV file.")
                return redirect('bulk_upload_doctors')

            try:
                # 1. Read & Decode (Handle BOM for Excel)
                decoded_file = csv_file.read().decode('utf-8-sig') 
                io_string = io.StringIO(decoded_file)
                reader = csv.DictReader(io_string) 
            except Exception as e:
                messages.error(request, f"Error reading file: {e}")
                return redirect('bulk_upload_doctors')

            # 2. Get Headers & Normalize
            csv_headers = [h.strip().lower() for h in reader.fieldnames] if reader.fieldnames else []
            
            # 3. Flexible Column Matching Logic
            column_variants = {
                'email': ['email', 'e-mail', 'email address', 'mail', 'email_id'],
                'first_name': ['first name', 'firstname', 'fname', 'f_name', 'first'],
                'last_name': ['last name', 'lastname', 'lname', 'l_name', 'last', 'surname'],
                'password': ['password', 'pass', 'pwd', 'login_pass'],
                'specialization': ['specialization', 'specialty', 'department', 'dept', 'role'] 
            }

            # 4. Map Columns
            header_map = {}
            missing_cols = []

            for db_field, variants in column_variants.items():
                found = False
                for variant in variants:
                    if variant in csv_headers:
                        original_header = reader.fieldnames[csv_headers.index(variant)]
                        header_map[db_field] = original_header
                        found = True
                        break
                if not found:
                    missing_cols.append(db_field)

            if missing_cols:
                messages.error(request, f"Missing columns: {', '.join(missing_cols)}. Please check CSV headers.")
                return redirect('bulk_upload_doctors')

            # 5. Process Rows
            success_count = 0
            error_count = 0
            
            for row in reader:
                try:
                    # Extract Data Safely using the Map
                    email = row.get(header_map['email'], '').strip()
                    first_name = row.get(header_map['first_name'], '').strip()
                    last_name = row.get(header_map['last_name'], '').strip()
                    password = row.get(header_map['password'], '').strip()
                    specialization = row.get(header_map['specialization'], '').strip()

                    # Basic Validation
                    if not email or not password or not first_name:
                        error_count += 1
                        continue

                    if User.objects.filter(email=email).exists():
                        print(f"Skipping {email}: Already exists.")
                        error_count += 1
                        continue

                    # ATOMIC TRANSACTION: Ensure User & Profile created together
                    with transaction.atomic():
                        # --- UNIQUE ID LOGIC: d + 6 random digits + cb ---
                        # Example: d839102cb
                        unique_username = f"d{random.randint(100000, 999999)}cb"
                        
                        user = User.objects.create_user(
                            username=unique_username,
                            email=email,
                            password=password,
                            first_name=first_name,
                            last_name=last_name
                        )
                        user.role = 'doctor'
                        user.save()

                        # B. Sync Profile
                        clean_spec = specialization.title() # e.g. "Cardiologist"
                        profile, created = Doctor.objects.get_or_create(user=user)
                        profile.specialization = clean_spec
                        profile.save() # Triggers Auto-Department Sync

                    success_count += 1

                except Exception as e:
                    print(f"Row Error: {e}")
                    error_count += 1

            messages.success(request, f"Upload Complete: {success_count} added, {error_count} skipped/failed.")
            
            # --- REDIRECT FIX: Points to correct Admin Doctor List ---
            return redirect('/admin/accounts/doctor/') 

    else:
        form = DoctorBulkUploadForm()

    return render(request, 'accounts/bulk_upload_doctors.html', {'form': form})


