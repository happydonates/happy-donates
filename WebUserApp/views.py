from django.shortcuts import render,redirect
from UserApp.models import UserProfileModel
from AdminApp.models import StateModel
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from UserApp.models import UserPostModel
from AdminApp.models import MainCategoryModel, StateModel, DistrictsModel
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
def home(request):
    categories = MainCategoryModel.objects.all()
    category_id = request.GET.get('category')
    posts = UserPostModel.objects.filter(status='Active').select_related('location', 'sub_category', 'user').order_by('-create_at')

    if category_id:
        posts = posts.filter(sub_category__main_category_id=category_id)

    latest_posts = posts[:8]

    context = {
        'categories': categories,
        'latest_posts': latest_posts,
        'active_category_id': int(category_id) if category_id else None
    }
    return render(request, 'user/home.html', context)

def register_view(request):
    if request.user.is_authenticated:
        return redirect('user_home')
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


def login_user(request):
    if request.user.is_authenticated:
        return redirect('user_home')
    if request.method == "POST":
        email = request.POST.get("email").lower()
        password = request.POST.get("password")
        next_url = request.POST.get("next") or "/"

        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username
        except User.DoesNotExist:
            messages.error(request, "Invalid email or password.")
            return redirect("login_user")

        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, "Invalid email or password.")
            return redirect("login_user")

        login(request, user)
        if(user.is_superuser):
            return redirect('/admin_home/')
        return redirect(next_url)

    return render(request, "user/login.html")
@login_required(login_url='login_user')
def logout_user(request):
    logout(request)
    return redirect('login_user')

@login_required(login_url='login_user')
def user_profile(request):
    user_profile = None
    try:
        user_profile = UserProfileModel.objects.get(user=request.user)
    except UserProfileModel.DoesNotExist:
        user_profile = None

    return render(request, 'user/profile.html', {'user_profile': user_profile})





def browse_items(request):
    
    posts = UserPostModel.objects.filter(status='Active').select_related('location', 'sub_category__main_category_id', 'user').order_by('-create_at')


    search_query = request.GET.get('q', '')
    selected_categories = request.GET.getlist('categories')
    selected_state = request.GET.get('state')
    selected_district = request.GET.get('district')
    sort_by = request.GET.get('sort', 'newest')

    is_htmx = request.headers.get('HX-Request') == 'true'

    if search_query:
        posts = posts.filter(Q(title__icontains=search_query) | Q(location__district_name__icontains=search_query))

    if selected_categories:
        posts = posts.filter(sub_category__main_category_id__in=selected_categories)
        selected_categories = [int(x) for x in selected_categories]


    districts = DistrictsModel.objects.none() 

    if selected_state and selected_state.isdigit():
        posts = posts.filter(location__state_id=selected_state)
        districts = DistrictsModel.objects.filter(state_id=selected_state) 

    if selected_district and selected_district.isdigit():
        posts = posts.filter(location_id=selected_district)


    if sort_by == 'oldest':
        posts = posts.order_by('create_at')
    else:
        posts = posts.order_by('-create_at')

 
    paginator = Paginator(posts, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'categories': MainCategoryModel.objects.all(),
        'states': StateModel.objects.all(),
        'districts': districts,
        'selected_categories': selected_categories,
        'selected_state': int(selected_state) if selected_state and selected_state.isdigit() else '',
        'selected_district': int(selected_district) if selected_district and selected_district.isdigit() else '',
        'search_query': search_query,
        'current_sort': sort_by,
        'is_htmx': is_htmx, 
    }


    if is_htmx:
        return render(request, 'partials/post_list.html', context)


    return render(request, 'user/browse_items.html', context)




def single_item_view(request, slug):
    post = get_object_or_404(UserPostModel, slug=slug)

    similar_items = list(UserPostModel.objects.filter(
        sub_category=post.sub_category,
        location=post.location,
        status='Active'
    ).exclude(slug=slug).order_by('-create_at')[:4])

   
    if len(similar_items) < 4:
        needed = 4 - len(similar_items)
        
        # Get IDs we already have to avoid duplicates
        current_ids = [item.post_id for item in similar_items]
        current_ids.append(post.post_id) 

        more_items = list(UserPostModel.objects.filter(
            sub_category=post.sub_category,
            status='Active'
        ).exclude(post_id__in=current_ids).order_by('-create_at')[:needed])

        similar_items.extend(more_items)

    if len(similar_items) < 4:
        needed = 4 - len(similar_items)
        
     
        current_ids = [item.post_id for item in similar_items]
        current_ids.append(post.post_id)

        filler_items = list(UserPostModel.objects.filter(
            status='Active'
        ).exclude(post_id__in=current_ids).order_by('-create_at')[:needed])

        similar_items.extend(filler_items)

    context = {
        'post': post,
        'similar_items': similar_items,
    }
    return render(request, 'user/single_item.html', context)