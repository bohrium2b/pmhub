from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="signup-index"),
    path("concert/create", views.createconcert, name="createconcert"),
    path("concert", views.listconcert, name="listconcert"),
    path("concert/<int:concert_id>/signup", views.newperformance, name="signupconcert"),
    path("concert/<int:concert_id>", views.concertpage, name="concertpage"),
    path("concert/<int:concert_id>/edit", views.editconcert, name="editconcert"),
    path("concert/<int:concert_id>/delete", views.deleteconcert, name="deleteconcert"),
    path("concert/<int:concert_id>/lock", views.lockconcert, name="lockconcert"),
    path("myconcerts", views.myconcerts, name="myconcerts"),
    path("concert/json", views.concertjson, name="concertjson"),
    path("calendar", views.calendar, name="calendar"),
    path("concert/<int:concert_id>/<int:performance_id>/edit", views.editperformance, name="editperformance"),
    path("concert/<int:concert_id>/<int:performance_id>/delete", views.deleteperformance, name="deleteperformance"),
]