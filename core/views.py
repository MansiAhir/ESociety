# core/views.py# core/views.py

import random
import string
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
from django.contrib.admin.views.decorators import staff_member_required



from .forms import (
    UserSignupForm,
    UserLoginForm,
    ForgotPasswordForm,
    OTPVerifyForm,
    SetNewPasswordForm,
)
from .models import (
    User,
    Visitor,
    Complaint,
    Facility,
    FacilityBooking,
    MaintenancePayment,
    Notice,
    EmergencyAlert,
)

# ─── Helpers ──────────────────────────────────────────────────────────────────
 
def _generate_otp():
    """Return a cryptographically random 6-digit OTP string."""
    return ''.join(random.choices(string.digits, k=6))
 
 
def _attach_otp(visitor):
    """Generate + save OTP and 24-hour expiry on a Visitor instance."""
    visitor.otp = _generate_otp()
    visitor.expiry_time = timezone.now() + timedelta(hours=24)
    visitor.save()
    return visitor.otp

# ─── Signup ───────────────────────────────────────────────────────────────────


def userSignupView(request):
    if request.method == "POST":
        form = UserSignupForm(request.POST or None)
        if form.is_valid():
            email = form.cleaned_data["email"]
            send_mail(
                subject="Welcome to E-society Management System",
                message="Thank you for registering with E-society Management System.",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
            )
            form.save()
            # Signal the login page to show the success popup
            messages.success(request, "Signup successful! Please login.")  # ✅
            return redirect("login")
        else:
            return render(request, "core/signup.html", {"form": form})
    else:
        form = UserSignupForm()
        return render(request, "core/signup.html", {"form": form})


# ─── Login ────────────────────────────────────────────────────────────────────


def userLoginView(request):
    if request.method == "POST":
        form = UserLoginForm(request.POST or None)
        errors = {}

        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            # user = authenticate(request, email=email, password=password)
            # Step 1 — does the email exist?
            try:
                User.objects.get(email=email)
            except User.DoesNotExist:
                errors["email"] = "No account found with this email address."
                return render(
                    request, "core/login.html", {"form": form, "errors": errors}
                )

            # Step 2 — is the password correct?
            user = authenticate(request, email=email, password=password)
            if user is None:
                errors["password"] = "Incorrect password. Please try again."
                return render(
                    request, "core/login.html", {"form": form, "errors": errors}
                )

            # Credentials correct — log in
            login(request, user)
            # Signal the dashboard/next page to show the login success popup
            messages.success(request, "LOGIN_SUCCESS")

            if user.role == "admin":
                return redirect("/admin/")
            elif user.role == "resident":
                return redirect("resident_dashboard")
            elif user.role == "security":
                return redirect("security_dashboard")
            else:
                return redirect("home")

        # Form itself invalid (e.g. empty fields)
        return render(request, "core/login.html", {"form": form, "errors": errors})

    else:
        form = UserLoginForm()
        return render(request, "core/login.html", {"form": form, "errors": {}})


# def _get_redirect_url(user):
#     if user.role == "admin":
#         return "/admin/"
#     elif user.role == "resident":
#         return "/resident/dashboard/"
#     elif user.role == "security":
#         return "/security/dashboard/"
#     return "/home/"


# ─── Logout ───────────────────────────────────────────────────────────────────


@login_required
def userLogoutView(request):
    logout(request)
    return redirect("login")


# ─── Forgot Password — Step 1: Enter email, send OTP ─────────────────────────


def forgotPasswordView(request):
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            try:
                User.objects.get(email=email)
            except User.DoesNotExist:
                form.add_error("email", "No account is registered with this email.")
                return render(request, "core/forgot_password.html", {"form": form})

            otp = "".join(random.choices(string.digits, k=6))
            cache.set(f"otp_{email}", otp, timeout=600)

            send_mail(
                subject="eSociety — Password Reset OTP",
                message=(
                    f"Your OTP for password reset is: {otp}\n\n"
                    "This OTP is valid for 10 minutes. Do not share it with anyone."
                ),
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
            )

            request.session["reset_email"] = email
            # Show "OTP sent" confirmation on the same page before redirecting to verify step
            messages.info(request, "OTP sent to your email address.")
            return redirect("verify_otp")
    else:
        form = ForgotPasswordForm()
    return render(request, "core/forgot_password.html", {"form": form})


# ─── Forgot Password — Step 2: Verify OTP ────────────────────────────────────


def verifyOTPView(request):
    email = request.session.get("reset_email")
    if not email:
        return redirect("forgot_password")

    if request.method == "POST":
        form = OTPVerifyForm(request.POST)
        if form.is_valid():
            entered_otp = form.cleaned_data["otp"]
            cached_otp = cache.get(f"otp_{email}")

            if cached_otp is None:
                form.add_error("otp", "OTP has expired. Please request a new one.")
                return render(request, "core/auth_verify_otp.html", {"form": form, "email": email})

            if entered_otp != cached_otp:
                form.add_error("otp", "Invalid OTP. Please try again.")
                return render(request, "core/auth_verify_otp.html", {"form": form, "email": email})

            # OTP verified — allow password reset
            cache.delete(f"otp_{email}")
            request.session["otp_verified"] = True
            return redirect("set_new_password")
    else:
        form = OTPVerifyForm()
    return render(request, "core/auth_verify_otp.html", {"form": form, "email": email})


# ─── Forgot Password — Step 3: Set new password ──────────────────────────────


def setNewPasswordView(request):
    email = request.session.get("reset_email")
    verified = request.session.get("otp_verified")

    if not email or not verified:
        return redirect("forgot_password")

    if request.method == "POST":
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            try:
                user = User.objects.get(email=email)
                user.set_password(form.cleaned_data["new_password1"])
                user.save()
            except User.DoesNotExist:
                return redirect("forgot_password")

            del request.session["reset_email"]
            del request.session["otp_verified"]

            messages.success(request, "PASSWORD_RESET_SUCCESS")
            return redirect("login")
    else:
        form = SetNewPasswordForm()
    return render(request, "core/set_new_password.html", {"form": form})


def home(request):
    return render(request, "home.html")


# ─────────────────────────────────────────────────────────
# RESIDENT DASHBOARD
# ─────────────────────────────────────────────────────────

@login_required
def resident_dashboard(request):
    if request.user.role != "resident":
        return redirect("login")

    resident = request.user
    new_otp = None
    new_visitor_name = None

    # ── Handle POST actions ──
    if request.method == "POST":
        action = request.POST.get("action")

        # Add complaint inline
        if action == "add_complaint":
            Complaint.objects.create(
                resident=resident,
                complaint_type=request.POST.get("complaint_type"),
                description=request.POST.get("description"),
                status="Pending",
                complaint_date=timezone.now().date(),
            )
            messages.success(request, "✅ Complaint submitted successfully.")
            return redirect("resident_dashboard")

        # Pre-approve visitor inline
        if action == "add_visitor":
            visitor_name = request.POST.get("visitor_name")
            visitor_type = request.POST.get("visitor_type")
            if visitor_name and visitor_type:
                v = Visitor.objects.create(
                    resident=resident,
                    visitor_name=visitor_name,
                    visitor_type=visitor_type,
                    approval_status="Approved",
                    entry_time=timezone.now(),
                )
                new_otp = _attach_otp(v)
                new_visitor_name = visitor_name
                messages.success(request, f"✅ {visitor_name} pre-approved. OTP: {new_otp}")

        # Book facility inline
        if action == "book_facility":
            facility_id  = request.POST.get("facility_id")
            booking_date = request.POST.get("booking_date")
            if facility_id and booking_date:
                facility = get_object_or_404(Facility, id=facility_id)
                FacilityBooking.objects.create(
                    resident=resident,
                    facility=facility,
                    booking_date=booking_date,
                    payment_status="Pending",
                )
                messages.success(request, f"✅ {facility.facility_name} booked for {booking_date}.")
                return redirect("resident_dashboard")

    # ── Queries ──
    all_payments         = MaintenancePayment.objects.filter(resident=resident).order_by("-id")
    pending_payments     = all_payments.filter(payment_status="Pending")
    total_pending_amount = sum(p.amount for p in pending_payments)

    my_complaints   = Complaint.objects.filter(resident=resident).order_by("-complaint_date")
    open_complaints = my_complaints.filter(status="Pending")

    visitor_requests      = Visitor.objects.filter(resident=resident).order_by("-entry_time")
    pending_visitor_count = visitor_requests.filter(approval_status="Pending").count()

    facilities  = Facility.objects.all()
    my_bookings = FacilityBooking.objects.filter(resident=resident).order_by("-booking_date")

    notices          = Notice.objects.all().order_by("-posted_date")
    emergency_alerts = EmergencyAlert.objects.all().order_by("-alert_date")

    return render(request, "dashboard/resident_dashboard.html", {
        "all_payments":          all_payments,
        "pending_payments":      pending_payments,
        "total_pending_amount":  total_pending_amount,
        "my_complaints":         my_complaints,
        "open_complaints":       open_complaints,
        "visitor_requests":      visitor_requests,
        "pending_visitor_count": pending_visitor_count,
        "facilities":            facilities,
        "my_bookings":           my_bookings,
        "notices":               notices,
        "emergency_alerts":      emergency_alerts,
        "new_otp":               new_otp,
        "new_visitor_name":      new_visitor_name,
    })


# ─────────────────────────────────────────────────────────
# SECURITY DASHBOARD
# ─────────────────────────────────────────────────────────

@login_required
def security_dashboard(request):
    if request.user.role != "security":
        return redirect("login")

    today     = timezone.now().date()
    residents = User.objects.filter(role="resident").order_by("first_name")

    # ── Handle POST actions ──
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "log_visitor":
            resident_id  = request.POST.get("resident_id")
            visitor_name = request.POST.get("visitor_name")
            visitor_type = request.POST.get("visitor_type")
            if visitor_name and visitor_type and resident_id:
                resident = get_object_or_404(User, id=resident_id, role="resident")
                Visitor.objects.create(
                    visitor_name=visitor_name,
                    visitor_type=visitor_type,
                    resident=resident,
                    approval_status="Pending",
                    entry_time=timezone.now(),
                )
                messages.success(
                    request,
                    f"✅ {visitor_name} logged. Awaiting approval from {resident.first_name}."
                )
            return redirect("security_dashboard")

        if action == "mark_exit":
            visitor = get_object_or_404(Visitor, id=request.POST.get("visitor_id"))
            visitor.exit_time = timezone.now()
            visitor.save()
            messages.success(request, f"🚪 Exit marked for {visitor.visitor_name}.")
            return redirect("security_dashboard")

    # ── Queries ──
    all_visitors     = Visitor.objects.filter(entry_time__date=today).order_by("-entry_time")
    pending_visitors = all_visitors.filter(approval_status="Pending")
    visitors_inside  = all_visitors.filter(
        approval_status="Approved",
        is_verified=True,
        exit_time__isnull=True,
    )

    all_complaints   = Complaint.objects.all().order_by("-complaint_date")
    notices          = Notice.objects.all().order_by("-posted_date")
    emergency_alerts = EmergencyAlert.objects.all().order_by("-alert_date")

    return render(request, "dashboard/security_dashboard.html", {
        "total_visitors":   all_visitors.count(),
        "all_visitors":     all_visitors,
        "pending_visitors": pending_visitors,
        "visitors_inside":  visitors_inside,
        "residents":        residents,
        "all_complaints":   all_complaints,
        "notices":          notices,
        "emergency_alerts": emergency_alerts,
    })


# ─────────────────────────────────────────────────────────
# VISITORS
# ─────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────
# VISITOR MANAGEMENT
# ─────────────────────────────────────────────────────────
 
# ── 1. List all visitors ──────────────────────────────────
 
@login_required
def visitor_list(request):
    status_filter = request.GET.get("status", "")
 
    if request.user.role == "resident":
        qs = Visitor.objects.filter(resident=request.user)
    else:
        qs = Visitor.objects.all()
 
    if status_filter:
        qs = qs.filter(approval_status=status_filter)
 
    residents = User.objects.filter(role="resident").order_by("first_name")
    return render(
        request,
        "visitors/visitor_list.html",
        {
            "visitors": qs.order_by("-entry_time"),
            "residents": residents,
        },
    )
 
 
# ── 2. Add visitor page (GET) ─────────────────────────────
 
@login_required
def add_visitor_page(request):
    residents = User.objects.filter(role="resident").order_by("first_name")
    return render(request, "visitors/add_visitor.html", {"residents": residents})
 
 
# ── 3. Resident pre-approves visitor → OTP generated ─────
 
@login_required
def add_visitor(request):
    """
    Resident pre-approves a visitor.
    - Creates Visitor with status=Approved
    - Immediately generates OTP
    - Returns OTP in context so resident can share with guest
    """
    if request.method == "POST" and request.user.role == "resident":
        visitor = Visitor.objects.create(
            visitor_name=request.POST.get("visitor_name"),
            visitor_type=request.POST.get("visitor_type"),
            resident=request.user,
            approval_status="Approved",
        )
        otp = _attach_otp(visitor)
 
        residents = User.objects.filter(role="resident").order_by("first_name")
        messages.success(request, f"✅ Visitor pre-approved! Share the OTP below with your guest.")
        return render(
            request,
            "visitors/add_visitor.html",
            {
                "residents": residents,
                "new_otp": otp,
                "new_visitor_name": visitor.visitor_name,
            },
        )
 
    residents = User.objects.filter(role="resident").order_by("first_name")
    return render(request, "visitors/add_visitor.html", {"residents": residents})
 
 
# ── 4. Security logs visitor at gate → status Pending ─────
 
@login_required
def log_visitor(request):
    """
    Security guard logs a new visitor at the gate.
    Status is always set to Pending — resident must approve.
    OTP is generated only after resident approves.
    """
    if request.method == "POST" and request.user.role == "security":
        resident = get_object_or_404(User, id=request.POST.get("resident_id"))
        Visitor.objects.create(
            visitor_name=request.POST.get("visitor_name"),
            visitor_type=request.POST.get("visitor_type"),
            resident=resident,
            approval_status="Pending",   # always Pending; resident approves
        )
        messages.success(
            request,
            f"✅ Visitor logged. Awaiting approval from {resident.first_name} {resident.last_name}."
        )
    return redirect("security_dashboard")
 
 
# ── 5. Resident (or security) approves / rejects visitor ──
 
@login_required
def approve_visitor(request, visitor_id):
    """
    Resident approves or rejects a pending visitor.
    On approval: OTP is generated and stored.
    Security can also approve/reject in emergencies.
    """
    if request.method == "POST":
        visitor = get_object_or_404(Visitor, id=visitor_id)
        action = request.POST.get("action")
 
        if action == "approve":
            visitor.approval_status = "Approved"
            otp = _attach_otp(visitor)   # generates OTP + saves
            messages.success(
                request,
                f"✅ {visitor.visitor_name} approved. OTP {otp} generated — visible on the visitor list."
            )
        elif action == "reject":
            visitor.approval_status = "Rejected"
            visitor.otp = None
            visitor.expiry_time = None
            visitor.save()
            messages.error(request, f"❌ {visitor.visitor_name} rejected.")
 
    return redirect(request.META.get("HTTP_REFERER", "visitor_list"))
 
 
# ── 6. Security verifies OTP at gate ──────────────────────
 
@login_required
def verify_otp_page(request, visitor_id):
    """Show the OTP verification form for a specific visitor (security only)."""
    if request.user.role != "security":
        return redirect("login")
 
    visitor = get_object_or_404(Visitor, id=visitor_id)
    return render(request, "visitors/verify_otp.html", {"visitor": visitor})
 
 
@login_required
def verify_otp(request, visitor_id):
    """
    Security submits the OTP entered by/shown by the visitor.
    On match and not expired → mark is_verified=True (entry allowed).
    On mismatch or expired → show error.
    """
    if request.user.role != "security":
        return redirect("login")
 
    visitor = get_object_or_404(Visitor, id=visitor_id)
 
    if request.method == "POST":
        entered_otp = request.POST.get("otp", "").strip()
 
        if visitor.approval_status != "Approved":
            messages.error(request, "❌ This visitor has not been approved by the resident.")
            return render(request, "visitors/verify_otp.html", {"visitor": visitor})
 
        if visitor.is_verified:
            messages.error(request, "ℹ️ OTP already used — visitor has already entered.")
            return render(request, "visitors/verify_otp.html", {"visitor": visitor})
 
        if visitor.expiry_time and timezone.now() > visitor.expiry_time:
            messages.error(request, "❌ OTP has expired. Ask the resident to generate a new one.")
            return render(request, "visitors/verify_otp.html", {"visitor": visitor})
 
        if entered_otp == visitor.otp:
            visitor.is_verified = True
            visitor.save()
            messages.success(
                request,
                f"✅ OTP verified! {visitor.visitor_name} may enter. Entry logged."
            )
            return redirect("visitor_list")
        else:
            messages.error(request, "❌ Incorrect OTP. Please check and try again.")
            return render(request, "visitors/verify_otp.html", {"visitor": visitor})
 
    return render(request, "visitors/verify_otp.html", {"visitor": visitor})
 
 
# ── 7. Security marks exit ────────────────────────────────
 
@login_required
def mark_exit(request):
    """Security marks the exit time of a verified visitor."""
    if request.method == "POST" and request.user.role == "security":
        visitor = get_object_or_404(Visitor, id=request.POST.get("visitor_id"))
        visitor.exit_time = timezone.now()
        visitor.save()
        messages.success(request, f"✅ Exit marked for {visitor.visitor_name}.")
    return redirect(request.META.get("HTTP_REFERER", "security_dashboard"))
 


# ─────────────────────────────────────────────────────────
# COMPLAINTS
# ─────────────────────────────────────────────────────────


@login_required
def complaint_list(request):
    if request.user.role == "resident":
        qs = Complaint.objects.filter(resident=request.user).order_by("-complaint_date")
    else:
        qs = Complaint.objects.all().order_by("-complaint_date")

    return render(
        request,
        "complaints/complaint_list.html",
        {
            "complaints": qs,
            "pending_count": qs.filter(status="Pending").count(),
            "resolved_count": qs.filter(status="Resolved").count(),
        },
    )


@login_required
def add_complaint_page(request):
    return render(request, "complaints/add_complaint.html")


@login_required
def raise_complaint(request):
    """Resident submits a new complaint."""
    if request.method == "POST" and request.user.role == "resident":
        Complaint.objects.create(
            resident=request.user,
            complaint_type=request.POST.get("complaint_type"),
            description=request.POST.get("description"),
            status="Pending",
        )
        messages.success(request, "✅ Complaint submitted! Tracking ID assigned.")
    return redirect("complaint_list")


# ─────────────────────────────────────────────────────────
# FACILITIES
# ─────────────────────────────────────────────────────────


@login_required
def facility_list(request):
    facilities = Facility.objects.all()
    my_bookings = FacilityBooking.objects.filter(resident=request.user).order_by(
        "-booking_date"
    )
    return render(
        request,
        "facilities/facility_list.html",
        {
            "facilities": facilities,
            "my_bookings": my_bookings,
        },
    )

@login_required
def booking_list(request):
    my_bookings = FacilityBooking.objects.filter(
        resident=request.user
    ).order_by('-booking_date')
    
    facilities = Facility.objects.all()
    
    paid_count   = my_bookings.filter(payment_status='Paid').count()
    unpaid_count = my_bookings.filter(payment_status='Unpaid').count()

    return render(request, 'facilities/booking_list.html', {
        'my_bookings':  my_bookings,
        'facilities':   facilities,
        'paid_count':   paid_count,
        'unpaid_count': unpaid_count,
    })

# @login_required
# def book_facility_page(request):
#     facilities       = Facility.objects.all()
#     selected_facility = request.GET.get('facility')
#     return render(request, 'facilities/book_facility.html', {
#         'facilities':        facilities,
#         'selected_facility': int(selected_facility) if selected_facility else None,
#     })



@login_required
def book_facility(request):
    facilities = Facility.objects.all()
    selected_facility = request.GET.get("facility")

    if request.method == "POST":
        if request.user.role != "resident":
            messages.error(request, "❌ Only residents can book facilities.")
            return redirect("facility_list")

        facility = get_object_or_404(Facility, id=request.POST.get("facility_id"))

        if facility.availability == "Not Available":
            messages.error(request, "❌ This facility is currently unavailable.")
            return render(
                request,
                "facilities/book_facility.html",
                {
                    "facilities": facilities,
                    "selected_facility": None,
                },
            )

        FacilityBooking.objects.create(
            facility=facility,
            resident=request.user,
            booking_date=request.POST.get("booking_date"),
            start_time = request.POST.get("start_time"),
            end_time = request.POST.get("end_time"),
            payment_status=request.POST.get("payment_status")
        )
        messages.success(request, f"✅ {facility.facility_name} booked successfully!")
        return redirect("facility_list")

    # GET — just show the form
    return render(
        request,
        "facilities/book_facility.html",
        {
            "facilities": facilities,
            "selected_facility": int(selected_facility) if selected_facility else None,
        },
    )


# ─── FINANCIAL MANAGEMENT ─────────────────────────────────────────────────────

@login_required
def payment_list(request):
    """Resident: view all bills + pay pending ones."""
    if request.user.role != "resident":
        return redirect("login")

    all_payments = MaintenancePayment.objects.filter(
        resident=request.user
    ).order_by("-id")
    pending_payments = all_payments.filter(payment_status="Pending")
    total_pending    = sum(p.amount for p in pending_payments)

    return render(request, "finance/payment_list.html", {
        "all_payments":    all_payments,
        "pending_payments": pending_payments,
        "total_pending":   total_pending,
        "paid_count":      all_payments.filter(payment_status="Paid").count(),
        "pending_count":   pending_payments.count(),
    })


@login_required
def pay_maintenance(request, payment_id):
    """Mark a pending bill as Paid → redirect to invoice."""
    payment = get_object_or_404(MaintenancePayment, id=payment_id, resident=request.user)
    if payment.payment_status == "Pending":
        payment.payment_status = "Paid"
        payment.payment_date   = timezone.now().date()
        payment.save()
        messages.success(request, f"PAYMENT_SUCCESS:{payment.id}")
    return redirect("invoice", payment_id=payment.id)


@login_required
def invoice(request, payment_id):
    """Show a printable invoice for a Paid bill."""
    payment = get_object_or_404(MaintenancePayment, id=payment_id, resident=request.user)
    return render(request, "finance/invoice.html", {"payment": payment})


# ── Admin: create bills ───────────────────────────────────────────────────────

@login_required
def admin_create_bill(request):
    """Admin: generate maintenance bills for all residents."""
    if request.user.role != "admin":
        return redirect("login")

    residents = User.objects.filter(role="resident")

    if request.method == "POST":
        month  = request.POST.get("month")
        amount = request.POST.get("amount")

        if not month or not amount:
            messages.error(request, "Month and amount are required.")
        else:
            created = 0
            for resident in residents:
                # Avoid duplicates for same resident+month
                _, new = MaintenancePayment.objects.get_or_create(
                    resident=resident,
                    month=month,
                    defaults={"amount": amount, "payment_status": "Pending"},
                )
                if new:
                    created += 1
            messages.success(request, f"✅ Bills generated for {created} resident(s) — {month}.")
            return redirect("admin_create_bill")

    # For display: recent bills
    recent_bills = MaintenancePayment.objects.select_related("resident").order_by("-id")[:50]
    return render(request, "finance/admin_create_bill.html", {
        "residents":    residents,
        "recent_bills": recent_bills,
    })


# ─────────────────────────────────────────────────────────
# NOTICES
# ─────────────────────────────────────────────────────────


@login_required
def notice_list(request):
    notices = Notice.objects.all().order_by("-posted_date")
    return render(request, "notices/notice_list.html", {"notices": notices})


@login_required
def add_notice_page(request):
    if request.user.role != "admin":
        messages.error(request, "❌ Only admins can post notices.")
        return redirect("notice_list")
    recent_notices = Notice.objects.all().order_by("-posted_date")[:5]
    return render(
        request, "notices/add_notice.html", {"recent_notices": recent_notices}
    )


@login_required
def add_notice(request):
    """Admin posts a new notice."""
    if request.method == "POST":
        if request.user.role != "admin":
            messages.error(request, "❌ Permission denied.")
            return redirect("notice_list")
        Notice.objects.create(
            title=request.POST.get("title"),
            message=request.POST.get("message"),
        )
        messages.success(request, "✅ Notice posted to all residents!")
    return redirect("notice_list")


# ─────────────────────────────────────────────────────────
# EMERGENCY ALERTS
# ─────────────────────────────────────────────────────────


@login_required
def alert_panel(request):
    alert_type = request.GET.get("type", "")
    qs = EmergencyAlert.objects.all().order_by("-alert_date")
    if alert_type:
        qs = qs.filter(alert_type=alert_type)

    all_alerts = EmergencyAlert.objects.all()

    return render(
        request,
        "emergency/alert_panel.html",
        {
            "alerts": qs,
            "total_alerts": all_alerts.count(),
            "fire_count": all_alerts.filter(alert_type="Fire").count(),
            "security_count": all_alerts.filter(alert_type="Security").count(),
            "medical_count": all_alerts.filter(alert_type="Medical").count(),
        },
    )
