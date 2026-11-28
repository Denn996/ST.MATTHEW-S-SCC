from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from matthewfamily.models import CommunityMember, WeeklyService
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.utils.http import url_has_allowed_host_and_scheme


@login_required(login_url='login')
def index(request):
    if request.method == 'POST':
        WeeklyService.objects.update_or_create(
            service_day='WEDNESDAY',
            defaults={
                'venue': request.POST.get('wed_venue'),
                'time_range': request.POST.get('wed_time'),
                'animator': request.POST.get('wed_animator'),
                'notes': f"Animation by {request.POST.get('wed_animator')}. Intercessory Rosary, Scripture reflection, and check-in.",
            }
        )
        WeeklyService.objects.update_or_create(
            service_day='THURSDAY',
            defaults={
                'venue': request.POST.get('thu_venue'),
                'time_range': request.POST.get('thu_time'),
            }
        )
        messages.success(request, 'Weekly venues saved to database!')
        return redirect('index')

    wednesday = WeeklyService.objects.filter(service_day='WEDNESDAY').first()
    thursday = WeeklyService.objects.filter(service_day='THURSDAY').first()
    members = CommunityMember.objects.all().order_by('full_name')

    return render(request, 'index.html', {
        'wednesday': wednesday,
        'thursday': thursday,
        'members': members,
    })


@login_required(login_url='login')
def calendar(request):
    return render(request, 'calendar.html')


@login_required(login_url='login')
def treasury(request):
    return render(request, 'treasury.html')


def signup(request):
    """Handles new member signup via registration/signup.html and holds the account in pending state."""
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == "POST":
        username = request.POST.get("username", "").strip().lower()
        email = request.POST.get("email", "").strip().lower()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if len(username) < 3:
            messages.error(request, "Username must be at least 3 characters long.")
            return redirect("signup")

        if len(first_name) < 3 or not first_name.isalpha():
            messages.error(request, "First name must contain at least 3 letters.")
            return redirect("signup")

        if len(last_name) < 3 or not last_name.isalpha():
            messages.error(request, "Last name must contain at least 3 letters.")
            return redirect("signup")

        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters long.")
            return redirect("signup")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("signup")

        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, "That username is already taken.")
            return redirect("signup")

        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
        )
        user.is_active = False  # Blocks login until an admin approves
        user.save()

        # Notify admin of the new pending member
        approval_url = request.build_absolute_uri(reverse('pending_approvals'))
        send_mail(
            subject=f"New St. Matthew SCC Member Awaiting Approval: {user.get_full_name() or user.username}",
            message=(
                f"{user.get_full_name()} ({user.username}) just registered and is waiting for approval.\n\n"
                f"Review and approve here: {approval_url}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_NOTIFICATION_EMAIL],
            fail_silently=True,
        )

        messages.success(
            request,
            "Registration submitted! Your account is awaiting St. Matthew SCC admin approval before you can log in."
        )
        return redirect("login")

    return render(request, "registration/signup.html")

@never_cache
@csrf_protect
def login(request):
    """Authenticates only admin-approved (is_active=True) members."""
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip().lower()
        password = request.POST.get('password', '')

        # Explicitly catch unapproved accounts before authenticate() returns None
        existing_user = User.objects.filter(username__iexact=username).first()
        if existing_user and not existing_user.is_active and existing_user.check_password(password):
            messages.warning(
                request,
                "Your account is still pending approval from the St. Matthew SCC Admin."
            )
            return redirect('login')

        # Use exact stored username in case an older account had uppercase letters
        lookup_username = existing_user.username if existing_user else username
        user = authenticate(request, username=lookup_username, password=password)

        if user is not None:
            auth_login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('index')
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'registration/login.html')

@staff_member_required(login_url='login')
def pending_approvals(request):
    """Admin-only queue of all unapproved member accounts."""
    pending_users = User.objects.filter(is_active=False, is_staff=False).order_by('-date_joined')
    return render(request, 'pending_approvals.html', {'pending_users': pending_users})


@staff_member_required(login_url='login')
@require_POST
def approve_member(request, user_id):
    """Activates a pending member and adds them to the CommunityMember directory."""
    member = get_object_or_404(User, id=user_id, is_active=False)
    member.is_active = True
    member.save()

    full_name = member.get_full_name().strip() or member.username
    CommunityMember.objects.get_or_create(full_name=full_name)

    messages.success(request, f"{full_name} has been approved and added to the community directory.")
    return redirect('pending_approvals')


@staff_member_required(login_url='login')
@require_POST
def reject_member(request, user_id):
    """Deletes a rejected registration request."""
    member = get_object_or_404(User, id=user_id, is_active=False)
    username = member.username
    member.delete()
    messages.error(request, f"Registration request for {username} was rejected and removed.")
    return redirect('pending_approvals')