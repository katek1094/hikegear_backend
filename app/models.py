from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.password_validation import validate_password
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from simple_history.models import HistoricalRecords
from . import constants


class MyUserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        validate_password(password)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, **extra_fields)

    def create(self, email, password):
        raise Exception('do not use this method with MyUser model!')


class MyUser(AbstractUser):
    first_name = None
    last_name = None
    username = None
    email = models.EmailField(verbose_name='email_address', max_length=255, unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = MyUserManager()

    def __str__(self):
        return self.email


class CreatedUpdated(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TrackedHistory(models.Model):
    history = HistoricalRecords(inherit=True)

    class Meta:
        abstract = True


class Profile(models.Model):
    user = models.OneToOneField(MyUser, related_name='profile', on_delete=models.CASCADE, primary_key=True)
    private_gear = models.JSONField(default=list)

    def __str__(self):
        return self.user.__str__()


@receiver(post_save, sender=MyUser)
def create_profile(sender, instance=None, created=False, **kwargs):
    if created:
        Profile.objects.create(user=instance)


class Backpack(CreatedUpdated):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='backpacks')
    name = models.CharField(max_length=constants.backpack_max_name_length, default='', blank=True)
    description = models.TextField(max_length=constants.backpack_max_description_length, default='', blank=True)
    list = models.JSONField(default=list)
    shared = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Brand(CreatedUpdated, TrackedHistory):
    name = models.CharField(max_length=100, unique=True)
    author = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Subcategory(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='subcategories')

    class Meta:
        verbose_name_plural = 'subcategories'
        constraints = [models.UniqueConstraint(fields=['name', 'category'], name='subcategory_constraint')]

    def __str__(self):
        return self.name


class Product(CreatedUpdated, TrackedHistory):
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT)
    subcategory = models.ForeignKey(Subcategory, on_delete=models.PROTECT)
    name = models.CharField(max_length=constants.product_name_max_length)
    url = models.URLField(default='', blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['brand', 'subcategory', 'name'], name='product_constraint')]

    def __str__(self):
        return self.name

    @property
    def reviews_amount(self):
        return self.reviews.count()

    @property
    def full_name(self):
        if self.subcategory.name != 'inne':
            return f'{self.subcategory.name} {self.brand.name} {self.name}'
        else:
            return f'{self.brand.name} {self.name}'


class Review(CreatedUpdated, TrackedHistory):
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    weight_net = models.IntegerField(blank=True, null=True)
    weight_gross = models.IntegerField(blank=True, null=True)
    summary = models.CharField(max_length=constants.review_summary_max_length)
    text = models.TextField(max_length=constants.review_text_max_length)

    class Meta:  # test if constraint are the same as serializers validators?
        constraints = [models.UniqueConstraint(fields=['author', 'product'], name='review_constraint')]

    def __str__(self):
        return self.summary
