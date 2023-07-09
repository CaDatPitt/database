from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.index_vw),
    path("about/", views.about_vw),
    path("browse/", views.browse_vw),
    path("contact/", views.contact_vw),
    path("create/", views.create_vw),
    path("dashboard/", views.dashboard_vw),
    path("dataset/", views.dataset_vw),
    path("delete-dataset/", views.delete_dataset_vw),
    path("documentation/", views.documentation_vw),
    path("download/", views.download_vw),
    path("faq/", views.faq_vw),
    path("help/", views.help_vw),
    path("item/", views.item_vw),
    path("login/", views.login_vw),
    path("pin-dataset/", views.pin_dataset_vw),
    path("pin-item/", views.pin_item_vw),
    path("logout/", views.logout_vw),
    path("profile/", views.profile_vw),
    path("remove-item/", views.remove_item_vw),
    path("retrieve/", views.retrieve_vw),
    path("signup/", views.signup_vw),
    path("tag-item/", views.tag_item_vw),
]
