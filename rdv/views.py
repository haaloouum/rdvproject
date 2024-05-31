from .models import *
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password,make_password
from django.contrib.auth.decorators import login_required
import json
from django.contrib.auth import authenticate
from django.utils import timezone
from django.shortcuts import render
from django.db.models import Q
from datetime import datetime, timedelta
from django.db.models import F, Window
from django.db.models.functions import RowNumber

def listUsers(request):
    users = CUser.objects.all().order_by('id').values('name', 'username')
    print({'users': list(users)})
    return JsonResponse({'users': list(users)})

def likeDoctor(request):
    doc_id = int(request.GET.get('doc_id', 0))
    user_id = int(request.GET.get('user_id', 0))
    isFavorite = True and request.GET.get('isFavorite', 0) == 'true' or False
    try:
        d = Doctor.objects.get(pk=doc_id)
        p = Patient.objects.get(user=user_id)
        if isFavorite:
            Like.objects.filter(patient = p, doctor = doc_id).delete()
        else:
            Like(patient=p, doctor=d).save()
        return JsonResponse({'message': isFavorite and 'Disliked!' or 'Liked!'}, status=201)

    except Doctor.DoesNotExist:
        return JsonResponse({'error': 'Doctor not found'}, status=404)

def getDoctor(request):
    doc_id = int(request.GET.get('doc_id', 0))
    user_id = int(request.GET.get('user_id', 0))
    try:
        d = Doctor.objects.get(pk=doc_id)
        p = Patient.objects.get(user=user_id)
        isFavorite = Like.objects.filter(patient = p, doctor = doc_id).exists()

        if d.is_allweek:
            disponibilities = ['Avalible all work days.']
        elif d.is_all_weeknoweekend:
            disponibilities = ['Avalible everday - Weekends included.']
        else:
            disponibilities = [dispo.__str__() for dispo in d.disponibilities.all()]
        
        doctor_data = {'name': f"{d.user.name} {d.user.last_name}", 'category': d.specialty.designation, 'about': d.description, 
        'location': f"{d.address} - {d.city.designation}", 'disponibilities': disponibilities, 'image_url': '', 'isFavorite': isFavorite, 'id': d.id }
    
        return JsonResponse({'message': 'Fetch success!', 'doctor_data': doctor_data }, status=201)

    except Doctor.DoesNotExist:
        return JsonResponse({'error': 'Doctor not found'}, status=404)

def getPatient(request):
    patient_id = int(request.GET.get('patient_id', 0))
    user_id = int(request.GET.get('user_id', 0))
    
    try:
        doctor = Doctor.objects.get(user=user_id)
        patient = Patient.objects.get(pk=patient_id)
        
        
        completed_appointments = Rdv.objects.filter(patient=patient, doctor=doctor, state='completed').select_related('doctor')

        completed_appointments_data = [
            {
                'date': appointment.time.strftime("%Y-%m-%d %H:%M:%S"),
                #'details': f" with Dr. {appointment.doctor.user.name} {appointment.doctor.user.last_name}",
            }
            for appointment in completed_appointments
        ]

        patient_data = {
            'name': f"{patient.user.name} {patient.user.last_name}",
            'image_url': '',  # Add image URL if available
            'id': patient.id,
            'completed_appointments': completed_appointments_data,
        }
    
        return JsonResponse({'message': 'Fetch success!', 'patient_data': patient_data}, status=201)

    except Doctor.DoesNotExist:
        return JsonResponse({'error': 'Doctor not found'}, status=404)
    except Patient.DoesNotExist:
        return JsonResponse({'error': 'Patient not found'}, status=404)

def bookDoctor(request):
    doc_id = int(request.GET.get('doc_id', 0))
    user_id = int(request.GET.get('user_id', 0))
    hour = request.GET.get('hour', '')
    selectedDate = request.GET.get('selectedDate', '')
    selected_date = timezone.make_aware(datetime.strptime(selectedDate, '%Y-%m-%d %H:%M:%S.%f'))
    selected_hour = datetime.strptime(hour, '%H:%M:%S')
    time = selected_date.replace(hour=selected_hour.hour, minute=selected_hour.minute, second=selected_hour.second)

    try:
        p = Patient.objects.get(user=user_id)
        d = Doctor.objects.get(pk=doc_id)
        Rdv(patient=p, state='booked', doctor=d, time=time).save()

        return JsonResponse({'message': 'Appointement Booked!' }, status=201)

    except Doctor.DoesNotExist:
        return JsonResponse({'error': 'Doctor not found'}, status=404)

def getSchedules(request):
    doc_id = int(request.GET.get('doc_id', 0))
    date_str = request.GET.get('date', '')
    try:
        doctor = Doctor.objects.get(pk=doc_id)
        date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S.%f').date()
        available_slots = combine_and_filter_hours(date, doctor)

        return JsonResponse({'message': 'Fetch success!', 'schedule': available_slots }, status=201)

    except Doctor.DoesNotExist:
        return JsonResponse({'error': 'Doctor not found'}, status=404)

def getDoctorSchedules(request):
    user_id = int(request.GET.get('user_id', 0))
    date_str = request.GET.get('date', '')

    try:
        doctor = Doctor.objects.get(user=user_id)
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        available_slots = combine_and_filter_hours(date, doctor)       
        return JsonResponse({'message': 'Fetch success!', 'schedule': available_slots}, status=201)
    except Doctor.DoesNotExist:
        return JsonResponse({'error': 'Doctor not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def bookDDoctor(request):
    patient_id = int(request.GET.get('patient_id', 0))
    user_id = int(request.GET.get('user_id', 0))
    hour = request.GET.get('hour', '')
    selectedDate = request.GET.get('selectedDate', '')

    try:
        selected_date = timezone.make_aware(datetime.strptime(selectedDate, '%Y-%m-%dT%H:%M:%S'))
        selected_hour = datetime.strptime(hour, '%H:%M:%S')
        time = selected_date.replace(hour=selected_hour.hour, minute=selected_hour.minute, second=selected_hour.second)

        d = Doctor.objects.get(user=user_id)
        p = Patient.objects.get(pk=patient_id)
        Rdv.objects.create(patient=p, state='booked', doctor=d, time=time)

        return JsonResponse({'message': 'Appointment Booked!'}, status=201)
    except Doctor.DoesNotExist:
        return JsonResponse({'error': 'Doctor not found'}, status=404)
    except Patient.DoesNotExist:
        return JsonResponse({'error': 'Patient not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
@csrf_exempt
def cancel_appointment(request):
    app_id = int(request.GET.get('app_id', 0))
    try:
        appointment = Rdv.objects.get(pk=app_id)
        print(appointment)
        appointment.state = 'canceled'
        appointment.save()
        return JsonResponse({'message': 'Appointment canceled successfully'}, status=201)
    except Rdv.DoesNotExist:
        return JsonResponse({'error': 'Appointment not found'}, status=404)
    
def complete_appointment(request):
    app_id = int(request.GET.get('app_id', 0))
    try:
        appointment = Rdv.objects.get(pk=app_id)
        appointment.state = 'completed'
        appointment.save()
        return JsonResponse({'message': 'Appointment completed successfully'}, status=201)
    except Rdv.DoesNotExist:
        return JsonResponse({'error': 'Appointment not found'}, status=404)

def get_hourly_slots(start_time, end_time):
    slots = []
    current_time = start_time
    while current_time < end_time:
        next_time = current_time + timedelta(hours=1)
        slots.append((current_time, next_time))
        current_time = next_time
    return slots

def combine_and_filter_hours(date, doctor):
    if doctor.is_allweek and date.strftime('%A').lower() not in ['friday', 'saturday']:
        workdays = [date.strftime('%A').lower()]
    elif doctor.is_all_weeknoweekend:
        workdays = [date.strftime('%A').lower()]
    else:
        workdays = [dispo for dispo in doctor.disponibilities.all() if date.strftime('%A').lower() == dispo.day.lower()]
    
    all_slots = []

    for dispo in workdays:
        if isinstance(dispo, str) or doctor.is_all_weeknoweekend or doctor.is_allweek:
            start_time_morning = datetime.combine(date, datetime.strptime("08:00", '%H:%M').time())
            end_time_morning = datetime.combine(date, datetime.strptime("12:00", '%H:%M').time())
            all_slots.extend(get_hourly_slots(start_time_morning, end_time_morning))

            start_time_afternoon = datetime.combine(date, datetime.strptime("13:00", '%H:%M').time())
            end_time_afternoon = datetime.combine(date, datetime.strptime("17:00", '%H:%M').time())
            all_slots.extend(get_hourly_slots(start_time_afternoon, end_time_afternoon))
        else:
            start_time = datetime.combine(date, datetime.strptime(f"{dispo.start_hour}:{dispo.start_minute}", '%H:%M').time())
            end_time = datetime.combine(date, datetime.strptime(f"{dispo.end_hour}:{dispo.end_minute}", '%H:%M').time())
            all_slots.extend(get_hourly_slots(start_time, end_time))
    
    booked_slots = Rdv.objects.filter(doctor=doctor,time__date=date,state='booked').values_list('time', flat=True)
    booked_slots_naive = [slot.replace(tzinfo=None) for slot in booked_slots]
    available_slots = [slot[0].time() for slot in all_slots if slot[0] not in booked_slots_naive]
    return available_slots

def search_doctors(request):
    name = request.GET.get('name', '')
    city = request.GET.get('city', '')
    specialty = request.GET.get('specialty', '')

    doctors = Doctor.objects.filter(Q(user__name__icontains=name) | Q(user__last_name__icontains=name),
    city__designation__icontains=city, specialty__designation__icontains=specialty).distinct()

    doctor_list = [{'doctor_name': f"{d.user.name} {d.user.last_name}",  'category': d.specialty.designation, 'city': d.city.designation, 'id': d.id }for d in doctors]
    
    return JsonResponse({'message': 'Fetch success!', 'doctor_list': doctor_list }, status=201)

def search_patients(request):
    name = request.GET.get('name', '')
    patients = Patient.objects.filter(Q(user__name__icontains=name) | Q(user__last_name__icontains=name))
    patient_list = []
    for p in patients:
        app = Rdv.objects.filter(patient_id=p)
        appointements = getAppList(app, 'patient', p, None)
        patient_list.append({'patient_name': f"{p.user.name} {p.user.last_name}", 'id': p.id, 'appointements': getAppList(app, 'patient', p, None)})
    
    return JsonResponse({'message': 'Fetch success!', 'patient_list': patient_list }, status=201)
    
@csrf_exempt
def signUp(request):
    if request.method == 'POST':
        json_data = json.loads(request.body.decode('utf-8'))
        name = json_data.get('name')
        last_name = json_data.get('last_name')
        email = json_data.get('email')
        phone_number = json_data.get('phone_number')
        password = json_data.get('password')

        if CUser.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Email already exists'}, status=400)

        new_cuuser = CUser(name=name, last_name=last_name, email=email, 
        phone_number=phone_number, password=password, username=email, 
        active=True, user_type='patient')
        new_cuuser.save()
        patient = Patient(user=new_cuuser)
        patient.save()

        return JsonResponse({'message': 'User created successfully', 'user_data': getUserData(new_cuuser)}, status=201)

    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def logIn(request):
    if request.method == 'POST':
        json_data = json.loads(request.body.decode('utf-8'))
        email = json_data.get('email')
        password = json_data.get('password')
        try:
            user = CUser.objects.get(email=email)
        except CUser.DoesNotExist:
            return JsonResponse({'error': 'Invalid email!'}, status=400)
        
        if password == user.password:
            return JsonResponse({'message': 'Authentication success!', 'user_data': getUserData(user) }, status=201)
        
        else:
            return JsonResponse({'error': 'Invalid password!'}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)

def getUserData(user):
    user_data = { 'id': user.id, 'type': user.user_type, 'last_name': user.last_name, 'first_name': user.name, 'email': user.email, 'phone': user.phone_number, }
    if user.user_type == 'patient':
        user_data['favoriteDoctors'] = [{'doctor_name': f"{like.doctor.user.name} {like.doctor.user.last_name}",  'category': like.doctor.specialty.designation, 
            'city': like.doctor.city.designation, 'id': like.doctor.id } for like in user.patient.likes()]
        user_data['patient_id'] = user.patient.id
    elif user.user_type == 'doctor':
        user_data['doctor_id'] = user.doctor.id
    return user_data

@csrf_exempt
def getAppointments(request):
    try:
        user_id = request.GET.get('user_id')
        #max_fetch = int(request.GET.get('max_fetch', 2))
        type_user = request.GET.get('type_user', 'patient')
        if type_user == 'patient':
            p = Patient.objects.get(user=user_id)
            app = Rdv.objects.filter(patient_id=p)
            return JsonResponse({'message': 'Data Fetched!', 'appointements': getAppList(app, type_user, p, None)}, status=201)
        elif type_user == 'doctor':
            d = Doctor.objects.get(user=user_id)
            #rdvs_with_row_number = Rdv.objects.annotate(row_number=Window(expression=RowNumber(), partition_by=F('state'), order_by=F('id').asc()))
            #app = rdvs_with_row_number.filter(row_number__lte=10, doctor_id=d)
            app = Rdv.objects.filter(doctor_id=d)
            return JsonResponse({'message': 'Data Fetched!', 'appointements': getAppList(app, type_user, None, d)}, status=201)
    except Rdv.DoesNotExist:
        return JsonResponse({'error': 'Patient not found'}, status=404)

def getAppList(app, type_user, p=None, d=None):
    appointments = []
    for a in app:
        if a.doctor.is_allweek:
            disponibilities = ['Avalible all work days.']
        elif a.doctor.is_all_weeknoweekend:
            disponibilities = ['Avalible everday - Weekends included.']
        else:
            disponibilities = [dispo.__str__() for dispo in a.doctor.disponibilities.all()]
        doctor_data = {}
        patient_data = {}
        if type_user == 'patient':
            doctor_data = {'name': f"{a.doctor.user.name} {a.doctor.user.last_name}", 'category': a.doctor.specialty.designation, 'about': a.doctor.description, 
                'location': f"{a.doctor.address} - {a.doctor.city.designation}", 'disponibilities': disponibilities, 'image_url': '', 'id': a.doctor.id }
            isFavorite = Like.objects.filter(patient = p, doctor = a.doctor).exists()
            doctor_data['isFavorite'] = isFavorite
        elif type_user == 'doctor':
            patient_data = {'name': f"{a.patient.user.name} {a.patient.user.last_name}", 'id': a.patient.id }

        appointments.append({'date': a.time.strftime('%Y-%m-%d'), 'day': a.time.strftime('%A'), 'time': a.time.strftime('%H:%M'), 
        'state': a.state, 'doctor_data': doctor_data, 'id': a.id, 'patient_data': patient_data})

    return appointments

@csrf_exempt
def update_user(request):
    try:
        user_id = request.GET.get('user_id')
        new_value = request.GET.get('new_value')
        type_change = request.GET.get('type')
        print(user_id, new_value, type_change)
        user = CUser.objects.get(pk = user_id)
        if type_change == 'email':
            user.email = new_value
        elif type_change == 'contact':
            user.phone_number = new_value
        elif type_change == 'password':
            user.password = new_value
        
        user.save()
        return JsonResponse({'message': 'Email updated successfully'})
    
    except CUser.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

@csrf_exempt
def update_password(request):
    if request.method == 'POST':
        json_data = json.loads(request.body.decode('utf-8'))
        user_id = json_data.get('user_id')
        current_password = json_data.get('current_password')
        new_password = json_data.get('new_password')
        print(current_password, new_password, user_id)

        user = CUser.objects.get(pk=int(user_id))
        
        if not current_password or not new_password:
            return JsonResponse({'error': 'Current password or new password not provided'}, status=400)
        
        if user.password != current_password:
            return JsonResponse({'error': 'Current password is incorrect'}, status=400)
        
        user.password = new_password
        user.save()
        
        return JsonResponse({'message': 'Password updated successfully'}, status=201)