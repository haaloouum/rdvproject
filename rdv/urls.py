from django.urls import path
from django.conf.urls.static import static
from .views import *
from django.conf import settings

urlpatterns = [
    path('signup/', signUp, name='get-users'),
    path('login/', logIn, name='login'),
    path('users/', listUsers, name='get-users'),
    path('get-appointements/', getAppointments, name='get-appointements'),
    path('update_user/', update_user, name='update_user'),
    path('search-doctors/', search_doctors, name='search-doctors'),
    path('search-patients/', search_patients, name='search-patients'),
    path('get-doctor/', getDoctor, name='get-doctor'),
    path('get-patient/', getPatient, name='get-patient'),
    path('like-doctor/', likeDoctor, name='like-doctor'),
    path('book-doctor/', bookDoctor, name='book-doctor'),
    path('book-ddoctor/', bookDDoctor, name='book-ddoctor'),
    path('get-schedules/', getSchedules, name='get-schedules'),
    path('get-dschedules/', getDoctorSchedules, name='get-dschedules'),

    path('update-password/', update_password, name='update-password'),
    path('cancel-appointment/', cancel_appointment, name='cancel-appointment'),
    path('complete-appointment/', complete_appointment, name='complete-appointment'),
]

