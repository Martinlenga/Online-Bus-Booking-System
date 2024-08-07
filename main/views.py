from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .forms import RegisterForm, LoginForm, BookingDetailsForm, BusForm ,BookingForm,FeedbackForm
from .models import OtpToken, Profile, Route, Schedule, Bus, Seat, Booking,User,Feedback
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from collections import defaultdict
from django.db.models import Avg, Count
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.http import HttpResponse
from django_daraja.mpesa.core import MpesaClient
from django.views.decorators.csrf import csrf_exempt
from django.http import FileResponse
from reportlab.pdfgen import canvas
from notifications.models import Notification
import json
from datetime import datetime
import base64
import matplotlib
matplotlib.use('Agg') # Use the Agg backend for non-interactive plots
import matplotlib.pyplot as plt
from io import BytesIO
import json
import requests
import io 
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Frame, PageTemplate
from reportlab.lib import colors
from .genrateAcesstoken import get_access_token


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required(login_url="/login")
def index(request):
    if request.user.is_superuser:
        # Redirect superuser to admin_template or handle differently as needed
        return redirect('admin_template')
    
    try:
        user_profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        # Handle case where user profile doesn't exist
        messages.error(request, "User profile not found.")
        return redirect('index')  # Redirect to regular home or handle appropriately
    
    return render(request, "main/home.html", {'user_profile': user_profile})

def home(request):
    return render(request,'main/base.html')


def signUp(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('verify-email',username=request.POST['username'])
    else:
        form = RegisterForm()
    
    return render(request,'registration/sign_up.html',{"form":form})


def verifyEmail(request, username):
    user = get_user_model().objects.get(username=username)
    user_otp = OtpToken.objects.filter(user=user).last()
    
    
    if request.method == 'POST':
        # valid token
        if user_otp.otp_code == request.POST['otp_code']:
            
            # checking for expired token
            if user_otp.otp_expires_at > timezone.now():
                user.is_active=True
                user.save()
                messages.success(request, "Account activated successfully!! You can Login.")
                return redirect("login")
            
            # expired token
            else:
                messages.warning(request, "The OTP has expired, get a new OTP!")
                return redirect("verify-email", username=user.username)
        
        
        # invalid otp code
        else:
            messages.warning(request, "Invalid OTP entered, enter a valid OTP!")
            return redirect("verify-email", username=user.username)
        
    context = {}
    return render(request, "verify_token.html", context)


def resendOtp(request):
    
    if request.method == 'POST':
        
                user_email = request.POST["otp_email"]
                
                if get_user_model().objects.filter(email=user_email).exists():
                    user = get_user_model().objects.get(email=user_email)
                    otp = OtpToken.objects.create(user=user, otp_expires_at=timezone.now() + timezone.timedelta(minutes=5))
                    
                    
                    # email variables
                    subject="Email Verification"
                    message = f"""
                                        Hi {user.username}, here is your OTP {otp.otp_code} 
                                        it expires in 5 minute, use the url below to redirect back to the website
                                        http://127.0.0.1:8000/verify-email/{user.username}
                                        
                                        """
                    sender = "chegegitiche254@gmail.com"
                    receiver = [user.email, ]
                
                
                    # send email
                    send_mail(
                            subject,
                            message,
                            sender,
                            receiver,
                            fail_silently=False,
                        )
                    
                    messages.success(request, "A new OTP has been sent to your email-address")
                    return redirect("verify-email", username=user.username)

                else:
                    messages.warning(request, "This email dosen't exist in the database")
                    return redirect("resend-otp")
       
           
    context = {}
    return render(request, "resend_otp.html", context)



def signIn(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:    
            login(request, user)
            messages.success(request, f"Hi {request.user.username}, you are now logged-in")
            return redirect("index")
        
        else:
            messages.warning(request, "Invalid credentials")
            return redirect("signin")
        
    return render(request, "login.html")

def login_user(request):
    request.session['id'] = 1  
    
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            if user.is_superuser:
                return redirect('admin_template')  # Replace with your admin template URL name
            else:
                return redirect('index')  # Replace with your home template URL name
        else:
            messages.error(request, "There was an error logging in. Please try again.")
            return redirect('login')
    
    else:
        return render(request, 'registration/login.html', {})


@login_required
def admin(request):
    # Ensure only superusers can access this view
    if not request.user.is_superuser:
        messages.error(request, "You are not authorized to view this page.")
        return redirect('index')

    total_users = Profile.objects.count()
    total_buses = Bus.objects.count()
    total_routes = Route.objects.count()
    total_schedules = Schedule.objects.count()
    average_rating = Feedback.objects.aggregate(Avg('rating'))['rating__avg']
    
    # Update to count the capacities
    capacity_counts = Bus.objects.values('capacity').annotate(count=Count('id'))
    bus_data = {
        "labels": [f'Capacity {capacity["capacity"]}' for capacity in capacity_counts],
        "data": [capacity['count'] for capacity in capacity_counts],
    }

    # Round the average rating to a whole number if it exists
    if average_rating is not None:
        average_rating = round(average_rating)

    context = {
        'total_users': total_users,
        'total_buses': total_buses,
        'total_routes': total_routes,
        'total_schedules': total_schedules,
        'bus_data': json.dumps(bus_data),
        'avg_rating': average_rating,
    }

    return render(request, 'admin_template.html', context)

def user_stats(request):
    # Fetch all users
    users = User.objects.all()

    # Aggregate data daily
    today = datetime.today()
    days = [today - timedelta(days=i) for i in range(365)]

    daily_user_counts = defaultdict(int)

    for user in users:
        day = user.date_joined.strftime('%Y-%m-%d')
        daily_user_counts[day] += 1

    # Prepare data for Matplotlib
    sorted_days = sorted(daily_user_counts.keys())
    cumulative_user_counts = []
    cumulative_count = 0

    for day in sorted_days:
        cumulative_count += daily_user_counts[day]
        cumulative_user_counts.append(cumulative_count)

    # Create a line chart
    plt.figure(figsize=(14, 10))
    plt.plot(sorted_days, cumulative_user_counts, marker='o', linestyle='-', color='b')

    # Add title and labels
    plt.title('Cumulative User Growth', fontsize=30)
    plt.xlabel('Day', fontsize=22)
    plt.ylabel('Total Users', fontsize=24)
    plt.xticks(rotation=45, fontsize=16, ha='right')  # Align labels to the right for better readability
    plt.yticks(fontsize=20)

    # Adjust layout to fit all elements
    plt.tight_layout()

    # Save the plot to a BytesIO object
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()

    return render(request, 'user_stats.html', {'chart': image_base64})

def logout_user(request):
    if request.user.is_superuser:
        # Logic for superuser logout
        # For example, redirect to admin dashboard or a different page
        logout(request)
        messages.success(request, "Admin Logged Out Successfully.")
        return redirect('home')  # Replace 'admin_dashboard' with your admin dashboard URL name
    else:
        # Logic for normal user logout
        # For example, redirect to home page
        logout(request)
        messages.success(request, "You Were Logged Out Successfully.")
        return redirect('home')  # Replace 'home' with your home page URL name

@login_required(login_url="/login")
def settings(request):
    user_profile = Profile.objects.get(user=request.user)
    
    if request.method == 'POST':
        image = request.FILES.get('profile_img', user_profile.profile_img)
        
        bio = request.POST.get('bio', '')
        address = request.POST.get('address', '')
        primary_email = request.POST.get('primary_email', '')
        secondary_email = request.POST.get('secondary_email', '')
        payment_method = request.POST.get('payment_method', '')
        phone_number = request.POST.get('phone_number', '')
        gender = request.POST.get('gender', '')

        user_profile.profile_img = image
        user_profile.bio = bio
        user_profile.address = address
        user_profile.primary_email = primary_email
        user_profile.secondary_email = secondary_email
        user_profile.payment_method = payment_method
        user_profile.phone_number = phone_number
        user_profile.gender = gender
        user_profile.save()

        return redirect('settings')

    return render(request, 'setting.html', {'user_profile': user_profile})

#dashboard
#dashboard
@login_required(login_url="/login")
def users(request):
    profiles = Profile.objects.select_related('user').all()

    context = {
        'profiles': profiles,
    }

    return render(request, 'users.html', context)

def add_user(request):
    if request.method == 'POST':
        # Handle form submission
        username = request.POST.get('username')
        payment_method = request.POST.get('payment_method')
        address = request.POST.get('address')
        primary_email = request.POST.get('primary_email')

        # Assuming 'request.user' gives the authenticated user instance
        user_instance = request.user

        # Create a new profile instance
        Profile.objects.create(
            user=user_instance,
            payment_method=payment_method,
            address=address,
            primary_email=primary_email
        )

        # Redirect to a success page or another view
        return redirect('users')  # Redirect to users list page, adjust the name as per your URLconf

    # If not a POST request, render the form
    return render(request, 'add_user.html')

def edit_user(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    user_instance = profile.user  # Retrieve the related User instance

    if request.method == 'POST':
        # Handle form submission
        payment_method = request.POST.get('payment_method')
        address = request.POST.get('address')
        primary_email = request.POST.get('primary_email')

        # Update profile fields
        profile.payment_method = payment_method
        profile.address = address
        profile.primary_email = primary_email
        profile.save()

        # Redirect to a success page or another view
        return redirect('users')  # Redirect to users list page, adjust the name as per your URLconf

    # If not a POST request, render the form with pre-filled data
    return render(request, 'edit_user.html', {'profile': profile})

def delete_user(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    user = profile.user

    if request.method == 'POST':
        # Perform deletion
        user.delete()
        # Optionally, delete associated profile if needed
        profile.delete()
        return redirect('users')  # Redirect to users list page after deletion

    # Handle GET request (optional: render confirmation template or redirect)
    return redirect('users')  # Redirect to users list page if not POST

@login_required(login_url="/login")
def routes_admin(request):
    routes = Route.objects.all()

    context = {
        'routes': routes,
    }

    return render(request, 'routes_admin.html', context)

@login_required(login_url="/login")
def add_route(request):
    if request.method == 'POST':
        route_id = request.POST.get('routeID')
        origin = request.POST.get('origin')
        destination = request.POST.get('destination')
        distance = request.POST.get('distance')
        fare = request.POST.get('fare')

        Route.objects.create(
            routeID=route_id,
            origin=origin,
            destination=destination,
            distance=distance,
            fare=fare
        )

        return redirect('routes_admin')

    return render(request, 'add_route.html')

@login_required(login_url="/login")
def edit_route(request, route_id):
    route = get_object_or_404(Route, routeID=route_id)

    if request.method == 'POST':
        route.routeID = request.POST.get('routeID')
        route.origin = request.POST.get('origin')
        route.destination = request.POST.get('destination')
        route.distance = request.POST.get('distance')
        route.fare = request.POST.get('fare')
        route.save()

        return redirect('routes_admin')

    context = {
        'route': route,
    }
    return render(request, 'edit_route.html', context)

@login_required(login_url="/login")
def delete_route(request, route_id):
    route = get_object_or_404(Route, routeID=route_id)

    if request.method == 'POST':
        route.delete()
        return redirect('routes')

    context = {
        'route': route,
    }
    return render(request, 'delete_route.html', context)



@login_required(login_url="/login")
def buses(request):
    buses = Bus.objects.all()

    context = {
        'buses': buses,
    }

    return render(request, 'buses.html', context)

def add_bus(request):
    if request.method == 'POST':
        form = BusForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('buses')  # Redirect to a view showing all buses
    else:
        form = BusForm()
    
    return render(request, 'add_bus.html', {'form': form})

def edit_bus(request, pk):
    bus = get_object_or_404(Bus, pk=pk)
    if request.method == 'POST':
        form = BusForm(request.POST, instance=bus)
        if form.is_valid():
            form.save()
            return redirect('buses')  # Redirect to buses list page after editing bus
    else:
        form = BusForm(instance=bus)
    
    return render(request, 'edit_bus.html', {'form': form, 'bus': bus})

def delete_bus(request, pk):
    bus = get_object_or_404(Bus, pk=pk)
    if request.method == 'POST':
        bus.delete()
        return redirect('buses')  # Redirect to buses list page after deleting bus
    
    return render(request, 'delete_bus.html', {'bus': bus})


@login_required(login_url="/login")
def schedules(request):
    schedules = Schedule.objects.all()

    context = {
        'schedules': schedules,
    }

    return render(request, 'schedule.html', context)

@login_required(login_url="/login")
def add_schedule(request):
    if request.method == 'POST':
        bus_id = request.POST.get('bus')
        route_id = request.POST.get('route')
        departure_time = request.POST.get('departureTime')
        arrival_time = request.POST.get('arrivalTime')
        date = request.POST.get('date')

        bus = Bus.objects.get(id=bus_id)
        route = Route.objects.get(routeID=route_id)

        Schedule.objects.create(
            bus=bus,
            route=route,
            departureTime=departure_time,
            arrivalTime=arrival_time,
            date=date
        )

        return redirect('schedule')

    buses = Bus.objects.all()
    routes = Route.objects.all()
    context = {
        'buses': buses,
        'routes': routes,
    }
    return render(request, 'add_schedule.html', context)

@login_required(login_url="/login")
def edit_schedule(request, schedule_id):
    schedule = get_object_or_404(Schedule, scheduleID=schedule_id)

    if request.method == 'POST':
        bus_id = request.POST.get('bus')
        route_id = request.POST.get('route')
        departure_time = request.POST.get('departureTime')

        bus = Bus.objects.get(id=bus_id)
        route = Route.objects.get(routeID=route_id)

        schedule.bus = bus
        schedule.route = route
        schedule.departureTime = departure_time
        schedule.save()

        return redirect('schedule')

    buses = Bus.objects.all()
    routes = Route.objects.all()
    context = {
        'schedule': schedule,
        'buses': buses,
        'routes': routes,
    }
    return render(request, 'edit_schedule.html', context)

@login_required(login_url="/login")
def delete_schedule(request, schedule_id):
    schedule = get_object_or_404(Schedule, scheduleID=schedule_id)

    if request.method == 'POST':
        schedule.delete()
        return redirect('schedule')

    context = {
        'schedule': schedule,
    }
    return render(request, 'delete_schedule.html', context)


def gender(request):
    # Count the number of each gender in the system
    male_count = Profile.objects.filter(gender='male').count()
    female_count = Profile.objects.filter(gender='female').count()
    other_count = Profile.objects.filter(gender='other').count()

    # Prepare data for the chart
    labels = ['Male', 'Female', 'Other']
    counts = [male_count, female_count, other_count]
    colors = ['#093f93', '#06763a', '#c80c0c']

    # Create a bar chart
    plt.figure(figsize=(12, 8))
    bars = plt.bar(labels, counts, color=colors)

    # Add title and labels with increased font size
    plt.title('Gender Distribution', fontsize=30)
    plt.xlabel('Gender', fontsize=26)
    plt.ylabel('Count', fontsize=26)
    plt.ylim(0, max(counts) + 10)  # Adjust y-axis limits

    # Increase font size for ticks
    plt.xticks(fontsize=20)
    plt.yticks(fontsize=20)

    # Add the value on top of each bar with increased font size
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval, int(yval), va='bottom', fontsize=18, ha='center')  # ha: horizontal alignment

    # Save the plot to a BytesIO object
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()

    return render(request, 'gender.html', {'chart': image_base64})

@login_required
def rating_distribution(request):
    # Aggregate ratings
    feedback_list = Feedback.objects.all()
    rating_counts = defaultdict(int)

    for feedback in feedback_list:
        rating_counts[feedback.rating] += 1  # Assuming feedback has a `rating` field

    # Prepare data for the chart
    labels = [1, 2, 3, 4, 5]
    counts = [rating_counts.get(rating, 0) for rating in labels]
    colors = ['#093f93', '#06763a', '#c80c0c', '#f39c12', '#e74c3c']

    # Create a bar chart
    plt.figure(figsize=(4, 2))  # Adjusted size for better fit
    bars = plt.bar(labels, counts, color=colors)

    # Add title and labels with increased font size
    plt.title('User Ratings Distribution', fontsize=20)
    plt.xlabel('Ratings', fontsize=12)
    plt.ylabel('Number of Users', fontsize=12)
    plt.ylim(0, max(counts) + 5)  # Adjust y-axis limits

    # Increase font size for ticks
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)

    # Add the value on top of each bar
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval, int(yval), va='bottom', fontsize=12, ha='center')

    # Save the plot to a BytesIO object
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    buf.seek(0)
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close()

    return render(request, 'rating_distribution.html', {'chart': image_base64})

#customer views

@login_required(login_url="/login")
def routes_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    if not profile.phone_number:
        messages.error(request, "Please update your phone number to proceed.")
        return redirect('settings')
        
    routes = Route.objects.all()
    return render(request, 'routes.html', {'routes': routes})

@login_required(login_url="/login")
def search_view(request):
    if request.method == 'POST':
        origin = request.POST.get('origin')
        destination = request.POST.get('destination')
        date = request.POST.get('date')

        try:
            # Query schedules based on the selected origin, destination, and date, and filter active buses
            schedules = Schedule.objects.filter(
                route__origin=origin, 
                route__destination=destination, 
                date=date,
                bus__status='Active'  # Ensure only active buses are considered
            )

            if schedules.exists():
                # Calculate total amount
                total_amount = sum(schedule.route.fare for schedule in schedules)

                # Retrieve active buses associated with the schedules
                buses = [schedule.bus for schedule in schedules]

                # Calculate available seats for each bus
                for bus in buses:
                    bus.available_seats = Seat.objects.filter(bus=bus, is_available=True).count()

                return render(request, 'search.html', {
                    'origin': origin,
                    'destination': destination,
                    'date': date,
                    'schedules': schedules,
                    'buses': buses,
                    'total_amount': total_amount,
                    'origins': Route.objects.values_list('origin', flat=True).distinct(),
                    'destinations': Route.objects.values_list('destination', flat=True).distinct(),
                })
            else:
                message = f"No schedules found from {origin} to {destination} on {date}."
        except Exception as e:
            message = f"An error occurred: {str(e)}"

        routes = Route.objects.all()
        return render(request, 'routes.html', {'routes': routes, 'message': message})

    else:
        routes = Route.objects.all()
        return render(request, 'routes.html', {'routes': routes})


@login_required
def seat_selection_view(request, bus_id):
    bus = get_object_or_404(Bus, id=bus_id)
    schedule = get_object_or_404(Schedule, bus=bus)
    route = schedule.route
    fare = route.fare
    
    # Fetch seats associated with the bus
    seats = Seat.objects.filter(bus=bus)
    
    # Organize seats into rows, with 4 seats per row
    seat_rows = []
    row = []
    for index, seat in enumerate(seats):
        row.append(seat)
        if (index + 1) % 4 == 0:  # 4 seats per row
            seat_rows.append(row)
            row = []
    if row:
        seat_rows.append(row)
    
    # Adjust the last row to join the seats at the back
    if seat_rows:
        last_row = seat_rows[-1]
        if len(last_row) == 3:
            # Add an extra seat to join the last row
            last_row.append(last_row[-1])
    
    if request.method == 'POST':
        selected_seats_str = request.POST.get('selected_seats', '')
        if selected_seats_str:
            selected_seats = selected_seats_str.split(',')
            # Redirect to booking details or process selected seats
            return redirect('booking_details', selected_seats=selected_seats)
    
    return render(request, 'seat_selection.html', {'seat_rows': seat_rows, 'bus': bus, 'fare': fare})


@login_required(login_url="/login/")
def booking_details(request, selected_seats):
    selected_seat_ids = selected_seats.split(',')
    selected_seat_objects = Seat.objects.filter(id__in=selected_seat_ids)
    seat_numbers = ','.join([seat.seat_number for seat in selected_seat_objects])

    user_profile = get_object_or_404(Profile, user=request.user)

    first_seat = selected_seat_objects.first()
    bus = first_seat.bus
    schedule = get_object_or_404(Schedule, bus=bus)
    route = schedule.route

    fare = route.fare
    total_amount = fare * len(selected_seat_objects)

    if request.method == 'POST':
        form = BookingDetailsForm(request.POST)
        if form.is_valid():

            print("Form is valid. Saving booking...")

            booking = Booking.objects.create(
                user=user_profile,
                scheduleID=schedule,
                seatNumber=seat_numbers,
                totalPrice=total_amount
            )
            

            return redirect('booking')
    else:
        initial_data = {
            'payment_method': user_profile.payment_method,
        }
        form = BookingDetailsForm(initial=initial_data)

    context = {
        'form': form,
        'selected_seats': selected_seat_objects,
        'origin': route.origin,
        'destination': route.destination,
        'departure_time': schedule.departureTime,
        'arrival_time': schedule.arrivalTime,
        'total_amount': total_amount,
        'payment_method_choices': Profile.PAYMENT_METHOD_CHOICES,
    }
    return render(request, 'booking_details.html', context)

@login_required(login_url="/login/")
def payment(request, booking_user):
    cl = MpesaClient()
    user_profile = Profile.objects.get(user=request.user)
    # Use a Safaricom phone number that you have access to, for you to be able to view the prompt.
    phone_number = user_profile.phone_number
    amount = 500
    account_reference = 'reference'
    transaction_desc = 'Description'
    callback_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest';
    response = cl.stk_push(phone_number, amount, account_reference, transaction_desc, callback_url)

    if response.status_code == 200:
        messages.success(request, 'Payment prompt sent to your phone')
        booking.save()
        booking = get_object_or_404(Booking, user=booking_user)
        return render(request, 'payment.html', {'booking': booking})
    else:
        messages.error(request, 'Failed to send payment prompt to your phone')
        return render(request, 'booking_details.html', context)
    



@login_required
def lockscreen(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        user = authenticate(username=request.user.username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')  # Redirect to the desired page
        else:
            messages.error(request, 'Invalid password')
    return render(request, 'lockscreen.html')

def booking(request):
    cl = MpesaClient()
    user_profile = Profile.objects.get(user=request.user)
    # Use a Safaricom phone number that you have access to, for you to be able to view the prompt.
    phone_number = user_profile.phone_number
    amount = 100
    account_reference = 'reference'
    transaction_desc = 'Description'
    callback_url = 'https://2810-197-237-29-99.ngrok-free.app/';
    response = cl.stk_push(phone_number, amount, account_reference, transaction_desc, callback_url)
    
    if response.status_code == 200:
        messages.success(request, 'Payment prompt sent to your phone')
         # Retrieve booking details from session
        booking_details = request.session.get('booking_details')
    
    # Print the booking details to debug
        print("Booking Details:", booking_details)
        payment_success = True

    else:
        messages.error(request, 'Failed to send payment prompt to your phone')

    return render(request, 'booking.html')
     
@csrf_exempt
def mpesa_callback(request):  
            access_token_response = get_access_token(request)
            access_token = access_token_response.content.decode('utf-8')
            access_token_json = json.loads(access_token)
            access_token = access_token_json.get('access_token')
            query_url = 'https://2810-197-237-29-99.ngrok-free.app/'
            business_short_code = '174379'
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
            password = base64.b64encode((business_short_code + passkey + timestamp).encode()).decode()
            checkout_request_id = 'ws_CO_04072023004444401768168060'

            query_headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + access_token
            }

            query_payload = {
                'BusinessShortCode': business_short_code,
                'Password': password,
                'Timestamp': timestamp,
                'CheckoutRequestID': checkout_request_id
            }
            
            try:
                response = requests.post(query_url, headers=query_headers, json=query_payload)
                response.raise_for_status()
                # Raise exception for non-2xx status codes
                response_data = response.json()
                
                if 'ResultCode' in response:
                    result_code = response['ResultCode']
                    if result_code == '1037':
                        message = "1037 Timeout in completing transaction"
                    elif result_code == '1032':
                        message = "1032 Transaction has been canceled by the user"
                    elif result_code == '1':
                        message = "1 The balance is insufficient for the transaction"
                    elif result_code == '0':
                        message = "0 The transaction was successful"
                    else:
                        message = "Unknown result code: " + result_code
                else:
                    message = "Error in response"
                
                return JsonResponse({'message': message})  # Return JSON response
            except Exception as e:
   
                return JsonResponse({'error': 'Error: ' + str(e)})  # Return JSON response for any other error


@login_required
def admin(request):
    # Ensure only superusers can access this view
    if not request.user.is_superuser:
        messages.error(request, "You are not authorized to view this page.")
        return redirect('index')

    total_users = Profile.objects.count()
    total_buses = Bus.objects.count()
    total_routes = Route.objects.count()
    total_schedules = Schedule.objects.count()
    average_rating = Feedback.objects.aggregate(Avg('rating'))['rating__avg']
    
    # Update to count the capacities
    capacity_counts = Bus.objects.values('capacity').annotate(count=Count('id'))
    bus_data = {
        "labels": [f'Capacity {capacity["capacity"]}' for capacity in capacity_counts],
        "data": [capacity['count'] for capacity in capacity_counts],
    }

    # Round the average rating to a whole number if it exists
    if average_rating is not None:
        average_rating = round(average_rating)

    context = {
        'total_users': total_users,
        'total_buses': total_buses,
        'total_routes': total_routes,
        'total_schedules': total_schedules,
        'bus_data': json.dumps(bus_data),
        'avg_rating': average_rating,
    }

    return render(request, 'admin_template.html', context)


def generate_pdf(request):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)

    elements = []

    # Fetch user and profile details
    user = request.user
    profile = Profile.objects.get(user=request.user)
    

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=18, spaceAfter=14)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, spaceAfter=10)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=12)
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=12, textColor=colors.darkgrey, fontName='Times-Roman', spaceBefore=20)

    # Title
    elements.append(Paragraph('BUS TICKET', title_style))
    elements.append(Paragraph(f'Booking ID: 1410250349', normal_style))
    elements.append(Spacer(1, 0.2 * inch))

    # Trip Details
    trip_details = [
        ['Trip Details'],
        ['Bus:', 'KCY'],
        ['Date:', '07-24-2024, 00:00'],
        ['Departure from:', 'Nairobi'],
        ['Arrive to:', 'Kisumu'],
        ['Ticket Type:', 'Regular 1'],
        ['Seats:', '1'],
    ]

    trip_table = Table(trip_details, colWidths=[2 * inch, 4.5 * inch])
    trip_table.setStyle(TableStyle([
        ('SPAN', (0, 0), (-1, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(trip_table)
    elements.append(Spacer(1, 0.2 * inch))

    # Customer and Booking Details
    customer_details = [
        ['Customer and Booking Details'],
        ['Customer Name:', user.username],
        ['Phone:', profile.phone_number],
        ['Booking Total:', '100'],
        ['Online Deposit Payment:', 'through cash'],
    ]

    customer_table = Table(customer_details, colWidths=[2 * inch, 4.5 * inch])
    customer_table.setStyle(TableStyle([
        ('SPAN', (0, 0), (-1, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(customer_table)
    elements.append(Spacer(1, 0.2 * inch))

    # Footer (optional)
    footer_text = "Notes:Thank you for the payment"
    elements.append(Paragraph(footer_text, footer_style))

    doc.build(elements)


    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename='invoice.pdf')



@login_required(login_url="/login")
def booking_form(request):
    bookings = Booking.objects.all()

    context = {
        'bookings': bookings,
    }

    return render(request, 'booking_form.html', context)

def add_booking(request):
     if request.method == 'POST':
        route_id = request.POST.get('routeID')
        origin = request.POST.get('origin')
        destination = request.POST.get('destination')
        distance = request.POST.get('distance')
        fare = request.POST.get('fare')

        Route.objects.create(
            routeID=route_id,
            origin=origin,
            destination=destination,
            distance=distance,
            fare=fare
        )

        return redirect('routes_admin')

     return render(request, 'add_booking.html')

def edit_booking(request, booking_id):
    booking = get_object_or_404(Booking, bookingID=booking_id)

    if request.method == 'POST':
        booking.seatNumber = request.POST.get('seatNumber')
        booking.bookingDate = request.POST.get('bookingDate')
        booking.totalPrice = request.POST.get('totalPrice')
        booking.save()
        return redirect('admin_template')  # Adjust to redirect to the desired page

    return render(request, 'edit_booking.html', {'booking': booking})

def delete_booking(request, booking_id):
    booking = get_object_or_404(Booking, bookingID=booking_id)  # Use the correct field here
    if request.method == 'POST':
        booking.delete()
        return redirect('bookings')  # Redirect to the bookings list after deletion
    return render(request, 'delete_booking.html', {'booking': booking})



def search_results(request):
    query = request.GET.get('q', '')
    error_message = None

    users = User.objects.filter(username__icontains=query)
    buses = Bus.objects.filter(busNumber__icontains=query)
    schedules = Schedule.objects.filter(route__origin__icontains=query) | Schedule.objects.filter(route__destination__icontains=query)
    routes = Route.objects.filter(origin__icontains=query) | Route.objects.filter(destination__icontains=query)

    if not users.exists() and not buses.exists() and not schedules.exists() and not routes.exists():
        error_message = "No results found for your query."

    context = {
        'query': query,
        'users': users,
        'buses': buses,
        'schedules': schedules,
        'routes': routes,
        'error_message': error_message,
    }

    return render(request, 'search_results.html', context)

@login_required
def submit_feedback(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user.profile  # Assuming Profile is linked to User
            feedback.save()
            return redirect('index')  # Redirect to the desired page
    else:
        form = FeedbackForm()

    # Create a list of stars with IDs
    stars = [{'id': i, 'value': 6 - i} for i in range(1, 6)]  # Generates [{'id': 1, 'value': 5}, ..., {'id': 5, 'value': 1}]

    return render(request, 'submit_feedback.html', {'form': form, 'stars': stars})

@login_required
def feedback_list(request):
    feedback_list = Feedback.objects.all().order_by('-createdAt')
      # Assuming you want the newest feedback first
    paginator = Paginator(feedback_list, 3)  # Show 10 feedbacks per page

    page_number = request.GET.get('page')
    feedbacks = paginator.get_page(page_number)
    return render(request, 'feedback_list.html', {'feedbacks': feedbacks})


def mark_all_as_read(request):
    if request.method == 'POST':
        notifications = request.user.notifications.unread()
        for notification in notifications:
            notification.mark_as_read()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'fail'}, status=400)


@login_required
def unread_notifications(request):
    # Query for unread notifications
    unread_notifications = request.user.notifications.all()

    # Mark all as read
    unread_notifications.mark_all_as_read()

     # Set up pagination
    paginator = Paginator(unread_notifications, 5)  # Show 10 notifications per page
    page_number = request.GET.get('page')
    notifications = paginator.get_page(page_number)

    # Render the page with the notifications
    context = {'notifications': notifications}
    return render(request, 'unread_notifications.html', context)


@login_required
def booking_number(request):
    if request.method == 'POST':
        phone_form = PhoneNumberForm(request.POST)  # Handle phone form submission
        if  phone_form.is_valid():
            # Your existing logic for handling booking details form submission
            phone_number = phone_form.cleaned_data['phone_number']
            # Redirect to the booking view with phone number as a query parameter
            return redirect(f'booking1?phone_number={phone_number}')
    else:
        phone_form = PhoneNumberForm()
    return render(request, 'booking_number.html', {'phone_form': phone_form})


def booking1(request):
    phone_number = request.GET.get('phone_number', '')  # Retrieve the phone number from query parameters

    cl = MpesaClient()
    user_profile = Profile.objects.get(user=request.user)
    # Use a Safaricom phone number that you have access to, for you to be able to view the prompt.
    phone_number = phone_number
    amount = 1
    account_reference = 'reference'
    transaction_desc = 'Description'
    callback_url = 'https://onlinebooking-674d158e4ad6.herokuapp.com/';
    response = cl.stk_push(phone_number, amount, account_reference, transaction_desc, callback_url)
    
    if response.status_code == 200:
        messages.success(request, 'Payment prompt sent to your phone')
         # Retrieve booking details from session
        booking_details = request.session.get('booking_details')
    
    # Print the booking details to debug
        print("Booking Details:", booking_details)
        payment_success = True

    else:
        messages.error(request, 'Failed to send payment prompt to your phone')

    return render(request, 'booking.html')