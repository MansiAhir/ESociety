from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager   

# Create your models here.

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')  # ✅ important


        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_admin') is not True:
            raise ValueError('Superuser must have is_admin=True.')

        return self.create_user(email, password, **extra_fields)

# Create your models here.
class User(AbstractBaseUser):

    email = models.EmailField(unique=True)
    
    # Gender Choices
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
    
    # New Fields added here
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='M', blank=True, null=True)
    mobile = models.CharField(max_length=15, unique=True, blank=True, null=True)
        
    role_choice = (
        ('admin', 'Admin'),
        ('resident', 'Resident'),
        ('security', 'Security'),
    )
    role = models.CharField(max_length=10,choices=role_choice,default='resident')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)  # ✅ paste here

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()

    #override userName filed
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return self.is_admin
    
    def __str__(self):
        return self.email
    

# 3. Visitor
class Visitor(models.Model):

    VISITOR_TYPE = [
        ('Guest', 'Guest'),
        ('Delivery', 'Delivery'),
        ('Service', 'Service'),
        ('Cab', 'Cab'),
    ]


    APPROVAL_STATUS = [
        ('Approved', 'Approved'),
        ('Pending', 'Pending'),
        ('Rejected', 'Rejected'),
    ]

    visitor_name = models.CharField(max_length=100)
    visitor_type = models.CharField(max_length=20, choices=VISITOR_TYPE)
    resident = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6, null=True, blank=True)
    expiry_time = models.DateTimeField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    entry_time = models.DateTimeField(auto_now_add=True)  # ✅ optional but practical
    exit_time = models.DateTimeField(blank=True, null=True)
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS, default='Pending')  # ✅

    def __str__(self):
        return self.visitor_name


# 4. Complaint
class Complaint(models.Model):

    COMPLAINT_TYPE = [
        ('Plumbing', 'Plumbing'),
        ('Electrical', 'Electrical'),
        ('Other', 'Other'),
    ]

    STATUS = [
        ('Pending', 'Pending'),
        ('Resolved', 'Resolved'),
    ]

    resident = models.ForeignKey(User, on_delete=models.CASCADE)
    complaint_type = models.CharField(max_length=30, choices=COMPLAINT_TYPE)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS, default='Pending')  # ✅
    complaint_date = models.DateField(auto_now_add=True)  # ✅


    def __str__(self):
        return f"{self.resident} - {self.complaint_type}"


# 5. Facility
class Facility(models.Model):

    AVAILABILITY = [
        ('Available', 'Available'),
        ('Not Available', 'Not Available'),
    ]

    facility_name = models.CharField(max_length=50, unique=True)
    emoji = models.CharField(max_length=10, blank=True)  # 👈 ADD THIS
    booking_fee = models.DecimalField(max_digits=10, decimal_places=2)
    availability = models.CharField(max_length=20, choices=AVAILABILITY)

    def __str__(self):
        return self.facility_name


# 6. Facility Booking
class FacilityBooking(models.Model):

    PAYMENT_STATUS = [
        ('Paid', 'Paid'),
        ('Unpaid', 'Unpaid'),
    ]

    facility = models.ForeignKey(Facility, on_delete=models.CASCADE)
    resident = models.ForeignKey(User, on_delete=models.CASCADE)
    booking_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS)

    def __str__(self):
        return f"{self.facility} - {self.resident} ({self.start_time} - {self.end_time})"


# 7. Maintenance Payment
class MaintenancePayment(models.Model):

    PAYMENT_STATUS = [
        ('Paid', 'Paid'),
        ('Pending', 'Pending'),
    ]

    resident = models.ForeignKey(User, on_delete=models.CASCADE)
    month = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS)
    payment_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.resident} - {self.month}"


# 8. Notice
class Notice(models.Model):
    title = models.CharField(max_length=100)
    message = models.TextField()
    posted_date = models.DateField(auto_now_add=True)     # ✅


    def __str__(self):
        return self.title


# 9. Emergency Alert
class EmergencyAlert(models.Model):

    ALERT_TYPE = [
        ('Fire', 'Fire'),
        ('Security', 'Security'),
        ('Medical', 'Medical'),
    ]

    alert_type = models.CharField(max_length=30, choices=ALERT_TYPE)
    message = models.TextField()
    alert_date = models.DateTimeField(auto_now_add=True)  # ✅


    def __str__(self):
        return self.alert_type

