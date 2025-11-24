from django.contrib.auth.models import User
from django.db import models
from AdminApp.models import SubCategoryModel, DonationCategoryModel, DistrictsModel,StateModel
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.text import slugify
import uuid

class UserPostModel(models.Model):
    """
    Model representing posts made by users.

    Attributes:
        post_id (AutoField): The primary key for the post.
        user (ForeignKey): The user who made the post.
        title (CharField): The title of the post.
        description (TextField): The description of the post.
        quantity (IntegerField): The quantity of items in the post.
        sub_category (ForeignKey): The subcategory of the post.
        pick_up_time (DateTimeField): The pick-up time for the post.
        end_on (DateTimeField): The end time for the post (nullable).
        location (ForeignKey): The location of the post.
        address (TextField): The address of the post.
        images (ImageField): The image(s) associated with the post.
        contact_number (CharField): The contact number for the post.
        comments (TextField): Any additional comments on the post (nullable).
        create_at (DateTimeField): The creation time of the post.
        status (CharField): The status of the post.

    Meta:
        db_table (str): The name of the database table for the model.
    """
    post_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts', null=True)
    title = models.CharField(max_length=250, null=True)
    description = models.TextField(null=True)
    quantity = models.IntegerField(default=1)
    sub_category = models.ForeignKey(SubCategoryModel, on_delete=models.CASCADE, related_name='posts', null=True)
    pick_up_time = models.DateTimeField(null=True)
    end_on = models.DateTimeField(null=True, )
    location = models.ForeignKey(DistrictsModel, on_delete=models.CASCADE, related_name='posts', null=True)
    address = models.TextField(null=True)
    images = models.ImageField(upload_to='images/', null=True)
    contact_number = models.CharField(max_length=100, null=True)
    comments = models.TextField(max_length=300, null=True)

    create_at = models.DateTimeField(auto_now_add=True, null=True)
    status = models.CharField(max_length=100, default="Active")
    slug = models.SlugField(max_length=255, null=True, blank=True, unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) if self.title else "post"
            self.slug = f"{base}-{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'user_post_table'
    


@receiver(post_save, sender=UserPostModel)
def update_status(sender, instance, **kwargs):
    if instance.end_on and instance.end_on < timezone.now() and instance.status == 'Active':
        instance.status = 'Inactive'
        instance.save()


class UserDonationModel(models.Model):

    donation_id = models.AutoField(primary_key=True)

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='donations',
        null=True, blank=True
    )

    title = models.CharField(max_length=400, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    category = models.ForeignKey(
        DonationCategoryModel, on_delete=models.CASCADE,
        related_name='donations', null=True, blank=True
    )

    end_date = models.DateTimeField(null=True, blank=True)

    location = models.ForeignKey(
        DistrictsModel, on_delete=models.CASCADE,
        related_name='donations', null=True, blank=True
    )

    address = models.CharField(max_length=500, null=True, blank=True)

    donation_file = models.FileField(
        upload_to='files/', null=True, blank=True, default=None
    )

    hospital_name = models.CharField(
        max_length=500, null=True, blank=True, default=None
    )

    donation_user_name = models.CharField(max_length=500, null=True, blank=True)

    hospital_patient_id = models.CharField(max_length=500, null=True, blank=True)

    images = models.ImageField(upload_to='images/', null=True, blank=True)

    contact_number = models.CharField(max_length=100, null=True, blank=True)

    comments = models.TextField(max_length=500, null=True, blank=True)

    create_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    status = models.CharField(max_length=100, default="Pending", blank=True)

    slug = models.SlugField(max_length=255, null=True, blank=True, unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) if self.title else "donation"
            self.slug = f"{base}-{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'user_donation_table'


class UserProfileModel(models.Model):
    """
    Model representing images uploaded by users.

    Attributes:
        user_image_id (AutoField): The primary key for the user image.
        user_image (ImageField): The image uploaded by the user.
        user_phone (CharField): The phone number of the user.
        user (OneToOneField): The user who uploaded the image.

    Meta:
        db_table (str): The name of the database table for the model.
    """
    user_profile_id = models.AutoField(primary_key=True)
    profile_image = models.ImageField(upload_to='profile', null=True)
    phone = models.CharField(max_length=200, null=True,blank=True)
    full_name = models.CharField(max_length=200,null=True,blank=True)   
    state = models.ForeignKey(StateModel, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='image')
    location = models.CharField(max_length=255, null=True, blank=True, help_text="e.g. Queens, New York, NY")
    bio = models.TextField(max_length=500, null=True, blank=True)
    
   
    notify_messages = models.BooleanField(default=True)
    notify_donations = models.BooleanField(default=True)

    class Meta:
        db_table = "user_profile_table"
