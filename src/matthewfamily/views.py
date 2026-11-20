from django.http import request
from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from matthewfamily.models import CommunityMember, WeeklyService

# Create your views here.
@login_required(login_url='login')
def index(request):
    if request.method == 'POST':
        # Save Wednesday updates
        WeeklyService.objects.update_or_create(
            service_day='WEDNESDAY',
            defaults={
                'venue': request.POST.get('wed_venue'),
                'time_range': request.POST.get('wed_time'),
                'animator': request.POST.get('wed_animator'),
                'notes': f"Animation by {request.POST.get('wed_animator')}. Intercessory Rosary, Scripture reflection, and check-in.",
            }
        )
        # Save Thursday updates
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

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'Passwords do not match. Please try again.')
            return render(request, 'registration/signup.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'That username is already taken. Choose another one.')
            return render(request, 'registration/signup.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return render(request, 'registration/signup.html')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
        )
        user.save()

        messages.success(request, 'Account created! Please sign in to access the St. Matthew SCC portal.')
        return redirect('login')

    return render(request, 'registration/signup.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            next_url = request.POST.get('next') or 'index'
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password. Need an account? Register below.')

    return render(request, 'registration/login.html', {'next': request.GET.get('next', '')})


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been signed out safely.')
    return redirect('login')