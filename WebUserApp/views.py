from django.shortcuts import render,redirect
from UserApp.models import UserProfileModel
from AdminApp.models import StateModel
from django.contrib.auth.models import User
from django.contrib import messages
# Create your views here.

def home(request):
    return render(request, 'user/home.html')

def register_view(request):
    if request.method == "POST":
        full_name = request.POST.get('full_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        state_id = request.POST.get('state')

   
        if not full_name or not username or not email or not password or not password2:
            messages.error(request, "Please fill all required fields.")
            return redirect('user_registe')

        if password != password2:
            messages.error(request, "Passwords do not match.")
            return redirect('user_registe')

    
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('user_registe')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect('user_registe')

        parts = full_name.split()
        first_name = parts[0]
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

       
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

    
        profile = UserProfileModel(
            user=user,
            full_name=full_name  
        )

    
        if state_id:
            try:
                profile.state = StateModel.objects.get(pk=state_id)
            except StateModel.DoesNotExist:
                profile.state = None

        profile.save()

        messages.success(request, "Account created successfully.")
        return redirect('login_user')

    # If GET request
    states = StateModel.objects.all().order_by('state_name')
    return render(request, 'user/registration.html', {'states': states})


def login(request):
    return render(request, 'user/login.html')