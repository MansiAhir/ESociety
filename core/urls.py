from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path("home/", views.home, name="home"),
    path("signup/", views.userSignupView, name="signup"),
    path("login/", views.userLoginView, name="login"),
    path('logout/', views.userLogoutView, name='logout'),

    # Forgot-password flow (3 steps)
    path("forgot-password/",   views.forgotPasswordView,  name="forgot_password"),
    path("verify-otp/",        views.verifyOTPView,       name="verify_otp"),
    path("set-new-password/",  views.setNewPasswordView,  name="set_new_password"),

    # ── Dashboards ──────────────────────────────────────
    path('resident/',  views.resident_dashboard, name='resident_dashboard'),
    path('security/',  views.security_dashboard, name='security_dashboard'),



    # ── Visitor Management ──────────────────────────────────────────────────
    # List all visitors (both roles)
    path('visitors/',           views.visitor_list,    name='visitor_list'),
 
    # Add visitor page (GET) — shared entry point for both roles
    path('visitors/add/',       views.add_visitor_page, name='add_visitor'),
 
    # Resident: pre-approve + generate OTP  (POST → add_visitor)
    path('visitors/create/',    views.add_visitor,      name='add_visitor'),
 
    # Security: log new visitor at gate (POST → Pending status)
    path('visitors/log/',       views.log_visitor,      name='log_visitor'),
 
    # Resident (or security): approve / reject  (POST)
    path('visitors/<int:visitor_id>/approve/', views.approve_visitor, name='approve_visitor'),
 
    # Security: OTP verification page (GET)
    path('visitors/<int:visitor_id>/verify/',  views.verify_otp_page, name='verify_otp_page'),
 
    # Security: OTP verification submit (POST)
    path('visitors/<int:visitor_id>/verify/submit/', views.verify_otp, name='verify_otp'),
 
    # Security: mark exit (POST)
    path('visitors/exit/',      views.mark_exit,        name='mark_exit'),



    # ── Complaints ──────────────────────────────────────
    path('complaints/',         views.complaint_list,     name='complaint_list'),
    path('complaint/add/',        views.add_complaint_page, name='add_complaint'),
    path('complaint/raise/',      views.raise_complaint,    name='raise_complaint'),

    # Facilities
    path('facility/',                views.facility_list,       name='facility_list'),
    path('facility/book/',           views.book_facility,       name='book_facility'),
    # path('facility/book/page/',      views.book_facility_page,  name='book_facility_page'),
    path('facility/bookings/',       views.booking_list,        name='booking_list'),


    # Payments
    path("payments/",                    views.payment_list,     name="payment_list"),
    path("payments/<int:payment_id>/pay/", views.pay_maintenance, name="pay_maintenance"),
    path("payments/<int:payment_id>/invoice/", views.invoice,    name="invoice"),
    path("admin-panel/bills/",           views.admin_create_bill, name="admin_create_bill"),


    # ── Notices ─────────────────────────────────────────
    # ── Emergency ───────────────────────────────────────
    # Notices & Alerts
    path("notices/", views.notice_list, name="notice_list"),
    path("alerts/",  views.alert_panel, name="alert_panel"),

]
