from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from .managers import CustomUserManager
from django.utils.translation import gettext_lazy as _
import uuid

    
class CustomUser(AbstractBaseUser, PermissionsMixin):
    user_id = models.BigAutoField(_('user ID'), auto_created=True, primary_key=True)
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=150)
    last_name = models.CharField(_('last name'), max_length=150)
    username = models.CharField(_('username'), max_length=25, unique=True)
    pronouns = models.CharField(_('pronouns'), max_length=25, blank=True, default='')
    title = models.CharField(_('title'), max_length=100, blank=True, default='')
    affiliation = models.CharField(_('affiliation'), max_length=100, blank=True, default='')
    bio = models.CharField(_('bio'), max_length=5000, blank=True, default='')
    website = models.URLField(_('website'), max_length=500, blank=True, default='')
    profile_photo_url = models.URLField(_('profile photo URL'), max_length=500, blank=True, default='')
    profile_public = models.BooleanField(_('profile_public'), default=False)
    
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'email', 'affiliation']

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.first_name + ' ' + self.last_name
    
    def get_short_name(self):
        return self.first_name
    
    def get_affiliations(self):
        return self.affiliation.split('|')
    

class Collection(models.Model):
    collection_id = models.CharField(_('collection ID'), max_length=200, primary_key=True)
    title = models.CharField(_('title'), max_length=200)

    class Meta:
        verbose_name = 'collection'
        verbose_name_plural = 'collections'

    def __str__(self):
        return self.collection_id
    
    def get_title(self):
        return self.title


class Item(models.Model):
    item_id = models.CharField(_('item ID'), max_length=200, primary_key=True)
    title = models.CharField(_('title'), max_length=200)
    type = models.CharField(_('type'), max_length=25, blank=True, default='')
    collections = models.ManyToManyField(Collection)
    date_added = models.DateTimeField(_('date added'), default=timezone.now)

    class Meta:
        verbose_name = 'item'
        verbose_name_plural = 'items'

    def __str__(self):
        return self.item_id
    
    def get_title(self):
        return self.title
    

class Dataset(models.Model):
    dataset_id = models.BigAutoField(_('dataset ID'), auto_created=True, primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, editable=False)
    title = models.CharField(_('title'), max_length=200, blank=True, default='')
    description = models.CharField(_('description'), max_length=5000, blank=True, default='')
    search_paremeters = models.CharField(_('search parameters'), max_length=500)
    items = models.ManyToManyField(Item)
    number_items = models.IntegerField(_('number of items'))
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date_created = models.DateTimeField(_('date created'), default=timezone.now)
    last_modified = models.DateTimeField(_('last modified'), blank=True, null=True)
    public = models.BooleanField(_('public'), default=False)

    class Meta:
        verbose_name = 'dataset'
        verbose_name_plural = 'datasets'

    def __str__(self):
        return self.item_id
        
    def get_title(self):
        return self.title


class PinnedDataset(models.Model):
    fk_dataset_id = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    fk_user_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date_pinned = models.DateTimeField(_('date pinned'), default=timezone.now)

    class Meta:
        verbose_name = 'pinned dataset'
        verbose_name_plural = 'pinned datasets'


class PinnedItem(models.Model):
    fk_dataset_id = models.ForeignKey(Item, on_delete=models.CASCADE)
    fk_user_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date_pinned = models.DateTimeField(_('date pinned'), default=timezone.now)

    class Meta:
        verbose_name = 'pinned item'
        verbose_name_plural = 'pinned items'
    