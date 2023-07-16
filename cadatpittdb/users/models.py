from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from .managers import CustomUserManager
from django.utils.translation import gettext_lazy as _
import uuid
from main.controlled_vocab import vocab
from markdown import markdown
import re

    
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
    # Enable ImageField option for profile photo?
    profile_photo_url = models.URLField(_('profile photo URL'), max_length=500, blank=True, default='')
    profile_public = models.BooleanField(_('profile_public'), default=False)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    email_confirmed = models.BooleanField(default=False)
    
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
        return f"{self.first_name} {self.last_name}"

    def get_full_name(self):
        return self.first_name + ' ' + self.last_name
    
    def get_short_name(self):
        return self.first_name
    
    def get_affiliations(self):
        affiliations = self.affiliation.split('|||')
        other_affiliations = []

        for affiliation in affiliations:
            if affiliation not in vocab['affiliation_type']:
                other_affiliations.append(affiliation)
        
        return affiliations, other_affiliations
    
    def get_bio(self):
        return get_markdown(self.bio)
    
    def get_datasets(self):
        return Dataset.objects.filter(creator=self).all()
    
    def get_saved_results(self):
        return Dataset.objects.filter(creator=self, saved_results=True).all()
    
    def get_pinned_datasets(self):
        return Dataset.objects.filter(pinned_by=self).all()
    
    def get_pinned_items(self):
        return Item.objects.filter(pinned_by=self).all()
    
    def get_pinned_item_ids(self):
        results = Item.objects.filter(pinned_by=self).all().values('item_id')
        item_ids = []
        
        for res in results:
            item_ids.append(res['item_id'])
        return item_ids
    

class Collection(models.Model):
    collection_id = models.CharField(_('collection ID'), max_length=200, primary_key=True)
    title = models.CharField(_('title'), max_length=200)
    url = models.CharField(_('url'), max_length=500, blank=True, default='')
    sites = models.CharField(_('sites'), max_length=100, blank=True, default='')
    has_dataset = models.BooleanField(_('has dataset'), default=False)
    date_added = models.DateTimeField(_('date added'), default=timezone.now)

    class Meta:
        verbose_name = 'collection'
        verbose_name_plural = 'collections'

    def __str__(self):
        return self.title
    
    def get_id(self):
        return self.collection_id
    
    def get_urls(self):
        return self.url.split('|||')
    
    def get_datasets(self):
        return Dataset.objects.filter(collections=self).all()
    
    def get_num_datasets(self):
        return Dataset.objects.filter(items__collections=self).distinct().count()
    

class Tag(models.Model):
    tag_id = models.BigAutoField(_('tag ID'), auto_created=True, primary_key=True)
    title = models.CharField(_('tag'), max_length=50, blank=True, default='')
    creator = models.ManyToManyField(CustomUser)
    date_created = models.DateTimeField(_('date created'), default=timezone.now)

    class Meta:
        verbose_name = 'tag'
        verbose_name_plural = 'tags'

    def __str__(self):
        return self.title
        
    def get_id(self):
        return self.tag_id
    
    def get_datasets(self):
        return Dataset.objects.filter(tags=self).all()
    
    def get_num_datasets(self):
        return Dataset.objects.filter(tags=self).count()


class Item(models.Model):
    item_id = models.CharField(_('item ID'), max_length=200, primary_key=True)
    title = models.CharField(_('title'), max_length=200)
    creator = models.CharField(_('creator'), max_length=200, blank=True, default='')
    date = models.CharField(_('date'), max_length=50, blank=True, default='')
    type = models.CharField(_('type'), max_length=25, blank=True, default='')
    thumbnail = models.URLField(_('thumbnail'), max_length=300, blank=True, default='')
    collections = models.ManyToManyField(Collection)
    tags = models.ManyToManyField(Tag)
    date_added = models.DateTimeField(_('date added'), default=timezone.now)
    pinned_by = models.ManyToManyField(CustomUser)

    class Meta:
        verbose_name = 'item'
        verbose_name_plural = 'items'

    def __str__(self):
        return self.title_
    
    def get_id(self):
        return self.item_id
    
    def get_datasets(self):
        return Dataset.objects.filter(items=self).all()
    
    def get_types(self):
        return self.type.split('|||')
    
    def get_tags(self):
        tags = []
        for tag in self.tags.get_all.value_list('title', flat=True):
            tags.append(tag)
        return tags
    

class Dataset(models.Model):
    dataset_id = models.BigAutoField(_('dataset ID'), auto_created=True, primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, editable=False)
    title = models.CharField(_('title'), max_length=200, blank=True, default='')
    items = models.ManyToManyField(Item)
    removed_items = models.ManyToManyField(Item, related_name='removed_items')
    description = models.CharField(_('description'), max_length=5000, blank=True, default='')
    filters = models.JSONField(_('filters'), blank=True, default=dict)
    tags = models.ManyToManyField(Tag)
    creator = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='creator')
    editors = models.ManyToManyField(CustomUser, related_name='editor')
    date_created = models.DateTimeField(_('date created'), default=timezone.now)
    last_modified = models.DateTimeField(_('last modified'), blank=True, default=timezone.now)
    public = models.BooleanField(_('public'), default=False)
    saved_results = models.BooleanField(_('is saved results'), default=False)
    pinned_by = models.ManyToManyField(CustomUser, related_name='pinner')

    class Meta:
        verbose_name = 'dataset'
        verbose_name_plural = 'datasets'

    def __str__(self):
        return self.title
        
    def get_id(self):
        return self.dataset_id
    
    def get_description(self):
        return get_markdown(self.description)
    
    def get_tags(self):
        tags = []
        for tag in self.tags.values_list('title', flat=True):
            tags.append(tag)
        return tags
    
    def get_item_ids(self):
        results = self.items.all().values('item_id')
        item_ids = []
        
        for res in results:
            item_ids.append(res['item_id'])
        return item_ids


class Message(models.Model):
    message_id = models.BigAutoField(_('dataset ID'), auto_created=True, primary_key=True)
    email = models.EmailField(_('email address'))
    full_name = models.CharField(_('full name'), max_length=150)
    inquiry_type = models.CharField(_('inquiry type'), max_length=100, blank=True, default='')
    subject = models.CharField(_('subject'), max_length=200, blank=True, default='')
    message = models.CharField(_('message'), max_length=5000, blank=True, default='')
    date_submitted = models.DateTimeField(_('date submitted'), default=timezone.now)

    class Meta:
        verbose_name = 'message'
        verbose_name_plural = 'messages'



class Page(models.Model):
    page_id = models.CharField(_('page ID'), max_length=200, primary_key=True)
    title = models.CharField(_('title'), max_length=200)
    url = models.CharField(_('url'), max_length=300, blank=True, default='')
    content = models.CharField(_('content'), max_length=8000, blank=True, default='')

    class Meta:
        verbose_name = 'page'
        verbose_name_plural = 'pages'

    def __str__(self):
        return self.title

    
def get_markdown(input=str) -> str:
    if input:
        text = input
        # Ensure hyperlink prefix
        # pattern for Markdown hyperlink
        pattern = r'\[[^!?\s]*\]\([^!?\s]*\)'
        
        for match in re.finditer(pattern, text):
            hyperlink = match[0]
            # Check if hyperlink is not prefixed
            if re.match(r'\[[^!?\s]*\]\([^http][^!?\s]*', hyperlink) or \
                re.match(r'\[[^!?\s]*\]\([^www.][^!?\s]*', hyperlink) or \
                re.match(r'\[[^!?\s]*\]\([^\\][^!?\s]*', hyperlink):
                prefixed_hyperlink = hyperlink.replace("(", "(//")
                text = text.replace(hyperlink, prefixed_hyperlink)

        # Strip enclosing paragraph marks, <p> ... </p>, which markdown() forces
        text = re.sub("(^<P>|</P>$)", "", markdown(text), flags=re.IGNORECASE)

        # Add target
        text = text.replace("<a href", "<a target='_blank' href")

        return text
    return input

