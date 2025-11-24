from django.utils import timezone
from django.shortcuts import render,redirect
from UserApp.models import UserProfileModel
from AdminApp.models import StateModel
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from UserApp.models import UserPostModel,UserDonationModel
from AdminApp.models import MainCategoryModel, StateModel, DistrictsModel,DonationCategoryModel,SubCategoryModel
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.core.exceptions import PermissionDenied

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
            return redirect('user_register')

        if password != password2:
            messages.error(request, "Passwords do not match.")
            return redirect('user_register')

    
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('user_register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect('user_register')

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



@login_required(login_url='login_user') # Replace 'login_user' with your actual login URL name
def user_profile(request):
    """
    Renders the user profile page with their posts and profile data.
    """
    # 1. Fetch the user's posts
    # We use 'select_related' for foreign keys (location, sub_category) to minimize database queries
    user_posts = UserPostModel.objects.filter(user=request.user).select_related('location', 'sub_category').order_by('-create_at')

    # 2. Context to pass to the template
    context = {
        'posts': user_posts,
        # Note: 'user' is automatically passed to templates by Django's auth context processor,
        # so we don't strictly need to pass 'user' explicitly, but 'posts' is required.
    }

    return render(request, 'user/profile.html', context)





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



def donation_list(request):
    # 1. Base Query
    donations = UserDonationModel.objects.filter(status='Active').select_related('category', 'location', 'user').order_by('-create_at')
    
    # 2. Get Filters
    search_query = request.GET.get('q', '')
    selected_category = request.GET.get('category', '')
    sort_by = request.GET.get('sort', 'newest')
    
    # 3. Check HTMX
    is_htmx = request.headers.get('HX-Request') == 'true'

    # 4. Apply Filters
    if search_query:
        donations = donations.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__district_name__icontains=search_query)
        )

    if selected_category:
        donations = donations.filter(category__donation_category_name=selected_category)

    # 5. Apply Sorting
    if sort_by == 'oldest':
        donations = donations.order_by('create_at')
    elif sort_by == 'urgent':
        donations = donations.filter(end_date__gte=timezone.now()).order_by('end_date')
    else: # newest
        donations = donations.order_by('-create_at')

    # 6. Pagination (Show 6 items per page)
    paginator = Paginator(donations, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'categories': DonationCategoryModel.objects.values('donation_category_name').distinct(),
        'selected_category': selected_category,
        'search_query': search_query,
        'current_sort': sort_by,
        'is_htmx': is_htmx,
    }

    # 7. Render Partial if HTMX request, else Full Page
    if is_htmx:
        return render(request, 'partials/donation_list.html', context)

    return render(request, 'user/donations.html', context)





def donation_detail(request, slug):
    donation = get_object_or_404(UserDonationModel, slug=slug)
    
    # Days left calculation
    days_left = 0
    if donation.end_date:
        delta = donation.end_date - timezone.now()
        days_left = delta.days if delta.days > 0 else 0

    # Category Theme Logic
    category_name = donation.category.donation_category_name if donation.category else "General"
    
    style_config = {
        'Medical': {'color': 'rose', 'bg': 'bg-rose-50', 'text': 'text-rose-600', 'border': 'border-rose-200', 'icon': 'fa-heart-pulse'},
        'Education': {'color': 'blue', 'bg': 'bg-blue-50', 'text': 'text-blue-600', 'border': 'border-blue-200', 'icon': 'fa-graduation-cap'},
        'Food': {'color': 'emerald', 'bg': 'bg-emerald-50', 'text': 'text-emerald-600', 'border': 'border-emerald-200', 'icon': 'fa-bowl-food'},
        'Clothing': {'color': 'amber', 'bg': 'bg-amber-50', 'text': 'text-amber-600', 'border': 'border-amber-200', 'icon': 'fa-shirt'},
        'Others': {'color': 'slate', 'bg': 'bg-slate-50', 'text': 'text-slate-600', 'border': 'border-slate-200', 'icon': 'fa-hand-holding-heart'},
    }
    
    current_style = style_config.get(category_name, style_config['Others'])

    context = {
        'donation': donation,
        'days_left': days_left,
        'theme': current_style, 
    }
    return render(request, 'user/donation_detail.html', context)


@login_required(login_url='login_user')
def donate_item(request):
    # 1. Fetch data for dropdowns
    subcategories = SubCategoryModel.objects.all()
    districts = DistrictsModel.objects.all()

    if request.method == 'POST':
        try:
            # 2. Extract data from request.POST
            title = request.POST.get('title')
            subcategory_id = request.POST.get('sub_category')
            condition = request.POST.get('condition') # Not in model, we'll append to description
            raw_description = request.POST.get('description')
            district_id = request.POST.get('location')
            address = request.POST.get('address')
            contact = request.POST.get('contact_number')
            
            # 3. Handle File Upload
            image = request.FILES.get('images')

            # 4. Data validation/Preparation
            # Combine condition into description since 'condition' isn't in the model
            full_description = f"{raw_description}\n\nCondition: {condition}"
            
            sub_cat_instance = SubCategoryModel.objects.get(pk=subcategory_id) if subcategory_id else None
            district_instance = DistrictsModel.objects.get(pk=district_id) if district_id else None

            # 5. Create and Save the Object
            new_post = UserPostModel.objects.create(
                user=request.user,
                title=title,
                sub_category=sub_cat_instance,
                description=full_description,
                location=district_instance,
                address=address,
                contact_number=contact,
                images=image,
                status="Active"
            )
            
            messages.success(request, "Donation posted successfully!")
            return redirect('user_profile') # Or redirect to a success page/listing

        except Exception as e:
            messages.error(request, f"Error posting donation: {e}")

    context = {
        'subcategories': subcategories,
        'districts': districts
    }
    return render(request, 'user/donate_item.html', context)




@login_required(login_url='login_user')
def edit_profile(request):
    user = request.user
    profile, created = UserProfileModel.objects.get_or_create(user=user)

    if request.method == 'POST':
        # 1. Update User Data
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()

        # 2. Update Profile Data
        profile.phone = request.POST.get('phone', '')
        profile.location = request.POST.get('location', '')
        profile.bio = request.POST.get('bio', '')

        # 3. Handle Image
        if 'profile_image' in request.FILES:
            profile.profile_image = request.FILES['profile_image']

        # 4. Handle Toggles
        profile.notify_messages = request.POST.get('notify_messages') == 'on'
        profile.notify_donations = request.POST.get('notify_donations') == 'on'

        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('user_profile')

    return render(request, 'user/edit_profile.html', {'user': user, 'profile': profile})

@login_required(login_url='login_user')
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        logout(request) 
        user.delete()   
        messages.success(request, "Your account has been deleted.")
        return redirect('user_home') 
    return redirect('edit_profile')


@login_required(login_url='login_user')
def edit_donate_item(request, slug):
    # 1. Fetch the post and ensure the user owns it
    post = get_object_or_404(UserPostModel, slug=slug)
    
    # Security check: Prevent editing other people's posts
    if post.user != request.user:
        raise PermissionDenied

    # 2. Fetch dropdown data
    subcategories = SubCategoryModel.objects.all()
    districts = DistrictsModel.objects.all()

    if request.method == 'POST':
        try:
            # 3. Update Text Fields
            post.title = request.POST.get('title')
            post.description = request.POST.get('description')
            post.address = request.POST.get('address')
            post.contact_number = request.POST.get('contact_number')
            post.status = request.POST.get('status', 'Active')

            # 4. Update Foreign Keys
            sub_cat_id = request.POST.get('sub_category')
            location_id = request.POST.get('location')

            if sub_cat_id:
                post.sub_category = SubCategoryModel.objects.get(pk=sub_cat_id)
            if location_id:
                post.location = DistrictsModel.objects.get(pk=location_id)

            # 5. Handle Image Update (Replaces old image if new one is uploaded)
            if 'images' in request.FILES:
                post.images = request.FILES['images']

            # 6. Save changes
            post.save()
            
            messages.success(request, "Donation updated successfully!")
            return redirect('user_home') # Change this to your dashboard or detail view url

        except Exception as e:
            messages.error(request, f"Error updating donation: {e}")

    context = {
        'post': post,
        'subcategories': subcategories,
        'districts': districts
    }
    return render(request, 'user/edit_donate_item.html', context)




def public_profile_view(request, username):
    # 1. Fetch the specific user object by username or show 404
    profile_user = get_object_or_404(User, username=username)

    # 2. Get their "UserPostModel" items (Contributions)
    # Ordering by newest first
    user_posts = profile_user.posts.all().order_by('-create_at')

    # 3. Calculate some basic stats
    total_donations = user_posts.count()
    
    # 4. Access the profile data safely
    # Note: In your model, related_name='image', so we access profile via profile_user.image
    try:
        user_profile = profile_user.image
    except AttributeError:
        user_profile = None

    context = {
        'profile_user': profile_user,
        'user_profile': user_profile,
        'user_posts': user_posts,
        'total_donations': total_donations,
    }
    
    return render(request, 'user/user_public_profile.html', context)