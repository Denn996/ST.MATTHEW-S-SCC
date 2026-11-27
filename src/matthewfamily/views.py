from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from matthewfamily.models import CommunityMember, WeeklyService


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
    """Handles new member signup via signup.html and holds the account in pending state."""
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if len(first_name) < 3 or not first_name.isalpha():
            messages.error(request, "First name must contain at least 3 letters.")
            return redirect("signup")

        if len(last_name) < 3 or not last_name.isalpha():
            messages.error(request, "Last name must contain at least 3 letters.")
            return redirect("signup")
        
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("signup")

        if User.objects.filter(username=username).exists():
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

        messages.success(
            request,
            "Registration submitted! Your account is awaiting St. Matthew SCC admin approval before you can log in."
        )
        return redirect("registration/login.html")

    return render(request, "registration/signup.html")


def login(request):
    """Authenticates only admin-approved (is_active=True) members."""
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password')

        # Explicitly catch unapproved accounts before authenticate() returns None
        existing_user = User.objects.filter(username=username).first()
        if existing_user and not existing_user.is_active and existing_user.check_password(password):
            messages.warning(
                request,
                "Your account is still pending approval from the St. Matthew SCC Admin."
            )
            return redirect('login')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next') or request.POST.get('next') or 'index'
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'registration/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been signed out safely.')
    return redirect('login')


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
    return redirect('pending_approvals.html')


@staff_member_required(login_url='login')
@require_POST
def reject_member(request, user_id):
    """Deletes a rejected registration request."""
    member = get_object_or_404(User, id=user_id, is_active=False)
    username = member.username
    member.delete()
    messages.error(request, f"Registration request for {username} was rejected and removed.")
    return redirect('pending_approvals.html')