import os
import random
import uuid
from io import BytesIO
from django.core.files import File
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone

import requests

from AdminApp.models import (
    MainCategoryModel, SubCategoryModel,
    DonationCategoryModel, StateModel, DistrictsModel, Poster
)
from UserApp.models import UserPostModel, UserDonationModel, UserProfileModel


# -----------------------------
# Helper — Download Image
# -----------------------------

def download_random_image():
    url = f"https://picsum.photos/600/400?random={uuid.uuid4().hex[:6]}"
    response = requests.get(url)
    if response.status_code == 200:
        return File(BytesIO(response.content), name=f"img_{uuid.uuid4().hex}.jpg")
    return None


class Command(BaseCommand):
    help = "Seed database with sample categories, users, posts, donations, posters"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("🚀 Starting Seeding..."))

        # -----------------------------
        # 1. States
        # -----------------------------
        states = ["Kerala", "Tamil Nadu", "Karnataka"]

        state_objs = []
        for s in states:
            state, created = StateModel.objects.get_or_create(state_name=s)
            state_objs.append(state)

        self.stdout.write(self.style.SUCCESS("✔ States created"))

        # -----------------------------
        # 2. Districts
        # -----------------------------
        districts = {
            "Kerala": ["Kottayam", "Ernakulam", "Kollam", "Thrissur"],
            "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai"],
            "Karnataka": ["Bengaluru", "Mysore", "Mangalore"]
        }

        district_objs = []
        for state in state_objs:
            for d in districts[state.state_name]:
                dist, created = DistrictsModel.objects.get_or_create(
                    district_name=d,
                    state_id=state
                )
                district_objs.append(dist)

        self.stdout.write(self.style.SUCCESS("✔ Districts created"))

        # -----------------------------
        # 3. Main Categories
        # -----------------------------
        main_categories = ["Furniture", "Electronics", "Clothes", "Books"]

        main_cat_objs = []
        for name in main_categories:
            cat, created = MainCategoryModel.objects.get_or_create(
                main_category_id=random.randint(1000, 9999),
                main_category_name=name,
            )
            main_cat_objs.append(cat)

        self.stdout.write(self.style.SUCCESS("✔ Main categories created"))

        # -----------------------------
        # 4. Sub Categories
        # -----------------------------
        sub_cat_map = {
            "Furniture": ["Chair", "Table", "Sofa"],
            "Electronics": ["Mobile", "Laptop", "TV"],
            "Clothes": ["Shirt", "Pants", "Kids Wear"],
            "Books": ["Novel", "Textbook", "Magazine"]
        }

        for main_cat in main_cat_objs:
            subs = sub_cat_map[main_cat.main_category_name]
            for s in subs:
                SubCategoryModel.objects.get_or_create(
                    sub_category_name=s,
                    main_category_id=main_cat
                )

        self.stdout.write(self.style.SUCCESS("✔ Sub categories created"))

        # -----------------------------
        # 5. Donation Categories
        # -----------------------------
        donation_cats = ["Blood Request", "Medical Support", "Education Help"]
        for name in donation_cats:
            DonationCategoryModel.objects.get_or_create(
                donation_category_id=random.randint(100, 999),
                donation_category_name=name
            )

        self.stdout.write(self.style.SUCCESS("✔ Donation categories created"))

        # -----------------------------
        # 6. Posters
        # -----------------------------
        for i in range(5):
            poster = Poster.objects.create(
                title=f"Donation Poster {i+1}",
                status=True
            )
            img = download_random_image()
            if img:
                poster.image.save(img.name, img, save=True)

        self.stdout.write(self.style.SUCCESS("✔ Posters added"))

        # -----------------------------
        # 7. Create Users + Profiles
        # -----------------------------
        users = []
        for i in range(10):
            user = User.objects.create_user(
                username=f"user{i}",
                email=f"user{i}@gmail.com",
                password="12345"
            )
            profile = UserProfileModel.objects.create(
                user=user,
                phone=f"98765432{i}",
                full_name=f"User {i}",
                state=random.choice(state_objs)
            )
            users.append(user)

        self.stdout.write(self.style.SUCCESS("✔ Users & Profiles created"))

        # -----------------------------
        # 8. Create User Posts
        # -----------------------------
        all_subs = SubCategoryModel.objects.all()
        for i in range(20):
            post = UserPostModel.objects.create(
                user=random.choice(users),
                title=f"Free Item {i}",
                description="This is a random donated item.",
                quantity=random.randint(1, 5),
                sub_category=random.choice(all_subs),
                pick_up_time=timezone.now(),
                end_on=timezone.now() + timezone.timedelta(days=random.randint(2, 10)),
                location=random.choice(district_objs),
                address="Sample address",
                contact_number="9999999999",
                comments="No comments"
            )
            img = download_random_image()
            if img:
                post.images.save(img.name, img, save=True)

        self.stdout.write(self.style.SUCCESS("✔ User Posts created"))

        # -----------------------------
        # 9. Create Donation Requests
        # -----------------------------
        donation_cat_objs = DonationCategoryModel.objects.all()
        for i in range(10):
            donation = UserDonationModel.objects.create(
                user=random.choice(users),
                title=f"Donation Help {i}",
                description="Need support for medical case",
                category=random.choice(donation_cat_objs),
                end_date=timezone.now() + timezone.timedelta(days=random.randint(5, 20)),
                location=random.choice(district_objs),
                address="Hospital XYZ",
                donation_user_name=f"Person {i}",
                hospital_patient_id=f"PID-{uuid.uuid4().hex[:5]}",
                contact_number="8888888888",
                comments="Urgent help required"
            )
            img = download_random_image()
            if img:
                donation.images.save(img.name, img, save=True)

        self.stdout.write(self.style.SUCCESS("✔ Donation Requests created"))
        self.stdout.write(self.style.SUCCESS("🎉 Seeding Completed Successfully!"))
