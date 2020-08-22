from django.urls import path

from playground import views

urlpatterns = [
    path("", views.image_list, name="image_list"),
    path("image_list/", views.image_list, name="image_list"),
    path("upload", views.upload, name="upload"),
    path("delete/<int:image_id>", views.delete, name="delete"),
    path("transfer", views.transfer, name="transfer"),

    path("result_list/", views.result_list, name="result_list"),

]