import json
from django.shortcuts import render, redirect
from django.views import View
from django.db.models import Q
from django.core.mail import send_mail
from .models import RideModel, Booking, Profile
from django.db.models import F
from datetime import datetime
from django.contrib import messages
import math
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.sites.shortcuts import get_current_site
from express import settings
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from .tokens import generate_token
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode


class Index(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'expressapp/index.html')


class About(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'expressapp/about.html')

class PickRide(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'expressapp/pickRide.html')

class Rides(View):
    def get(self, request, *args, **kwargs):
        rides=RideModel.objects.all()
        # if date and time of trip is less than todays date and time then we are not showing in all rides 
        for ride in rides:
            if ride.date_of_trip < datetime.now().date() and ride.time_of_trip < datetime.now().time():
                rides=rides.exclude(id = ride.id)

        # these blocks are for pagination 
        page= request.GET.get('page')
        rides, prev, nxt = pagination(page, rides)

        context={'rides': rides, 'prev':prev, 'nxt':nxt}
        return render(request, 'expressapp/allRides.html')
    
    def post(self, request, *args, **kwargs):
        leave = request.POST.get('leave')
        arrive = request.POST.get('arrive')
        date = request.POST.get('date')
        # number_of_passengers so that we can pass it through url to use it on ride.html
        number = request.POST.get('number')
        lookup = (Q(source__icontains=leave) &
                    Q(destination__icontains=arrive))
        if leave != None and arrive != None and date != None and number != None:
            rides = RideModel.objects.filter(Q(lookup))

            #if rides does not exist
            if not rides:
                return render(request, 'expressapp/rides.html', {'error': 'No rides available'})

            # if vacant_seats is less than the user demand then we are not showing that particular ride and if date and time of trip is less than todays date and time
            for ride in rides:
                if ride.vacant_seats < int(number) or (ride.date_of_trip < datetime.now().date() and ride.time_of_trip < datetime.now().time()):
                    rides=rides.exclude(id = ride.id)
            
            # these blocks are for pagination 
            page= request.GET.get('page')
            rides, prev, nxt = pagination(page, rides)

            context={'rides': rides,'number':number, 'prev':prev, 'nxt':nxt}

            return render(request, "expressapp/rides.html", context)

class RideCards(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'expressapp/rideCards.html')
    
    def post(self, request, pk):
        ride = RideModel.objects.get(id=pk)
        # getting number_of_passenger through url get method
        number=request.GET.get('number')
        number=number if number else 1
        print(number)
        ride.vacant_seats = F('vacant_seats') - number
        ride.save()
        
        # This model is saving ride information
        bookings=Booking(post=ride, riders_id=request.user.id, seats_booked=number)
        bookings.save()

        return render(request, 'expressapp/success.html')

def pagination(page, rides):
    # PAGINATION LOGIC STARTS
    # designing pagination logic
    no_of_posts=2
    # page= request.GET.get('page') # fetching value from url

    # By default, request.GET.get('page') returns string and if there is no page then return None
    # so if there is no page, make page = 1 otherwise convert ot integer
    if page is None:
        page = 1
    else:
        page = int(page)

    
    # counting all blogs in the databases to perform pagination logic
    length = len(rides)
    # here we are using python slicing function
    # below line just used to show how many blogs can be rendered on blog page and from where to where (ie, if page = 1, then blogs from index 0 to 2 will be displayed)
    rides = rides[(page-1)*no_of_posts: page*no_of_posts]

    # if page is greater than 1 then prev will be decremented by page-1 else make it None
    if page > 1:
        prev=page-1
    else:
        prev=None

    # Similarly, if page is less than ceiling value of required number of pages then nxt will be incremented by page+1 else make it None
    if page<math.ceil(length/no_of_posts):
        nxt=page+1
    else:
        nxt=None

    return rides, prev, nxt
    
    # PAGINATION LOGIC ENDS

class PubRide(View):
    def get(self, request, *args, **kwargs):
        return render(request, "expressapp/PubRide.html")
    
    def post(self, request, *args, **kwargs):
        #user=request.user
        source = request.POST['source']
        destination = request.POST['destination']
        vacant_seats = request.POST['vacant_seats']
        date_of_trip = request.POST['date_of_trip']
        time_of_trip = request.POST['time_of_trip']
        price = request.POST['price']
        car_name = request.POST.get('car_name')
        car_id = request.POST.get('car_id')
        details = request.POST.get('details')

        post1 = RideModel(
            source=source, destination=destination, vacant_seats=vacant_seats, date_of_trip=date_of_trip, time_of_trip=time_of_trip, price=price, car_name=car_name, car_id=car_id, details=details)

        post1.save()

        print(post1)

        messages.success(request, "Sua corrida foi postada com sucesso!")
        return render(request, "expressapp/PubRide.html")
    
class Register(View):
    def get(self, request, *args, **kwargs):
        return render(request, "expressapp/register.html")
    
    def post(self, request, *args, **kwargs):
        username = request.POST['username']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']
        contact_no = request.POST['contact_no']

        if User.objects.filter(username=username):
            messages.error(
                request, "Usuário já existente! Por favor, tente outro nome de usuário.")
            return render(request, "expressapp/register.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email já registrado!")
            return render(request, "expressapp/register.html")

        if len(username) > 20:
            messages.error(request, "Usuário deve ter menos de 20 caracteres!")
            return render(request, "expressapp/register.html")

        if pass1 != pass2:
            messages.error(request, "Senhas não são a mesma!")
            return render(request, "expressapp/register.html")

        if not username.isalnum():
            messages.error(request, "Usuário não pode conter apenas números!")
            return render(request, "expressapp/register.html")

        myuser = User.objects.create_user(username, email, pass1)
        myuser.first_name = first_name
        myuser.last_name = last_name
        myuser.is_active = True
        myuser.save()

        # Also saving the details in Profile database
        profile= Profile(user=username, first_name=first_name, last_name=last_name, email=email, contact_no=contact_no)
        profile.save()

        messages.success(request, "Sua conta foi criada com sucesso. Por favor confirme seu email clicando no link de confirmação que lhe enviamos.")

        # Welcome Email
        subject = "Bem-vindo(a) ao Express!!!"
        message = "Olá " + myuser.first_name + "!! \n" + \
            "Bem-vindo(a) à plataforma Express! \nAgradecemos pela visita e registro no nosso site.\n Nós lhe enviamos um email de confirmação, por favor confirme seu email. \n\nViaje com a gente, vá de Express! \n Stéfany Coura Coimbra"
        from_email = settings.EMAIL_HOST_USER
        to_list = [myuser.email]
        send_mail(subject, message, from_email, to_list, fail_silently=True)

        # Email Address Confirmation Email
        current_site = get_current_site(request)
        email_subject = "Confirme seu email na nossa plataforma Express!"
        message2 = render_to_string('expressapp/email_confirmation.html', {

            'name': myuser.first_name,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(myuser.pk)),
            'token': generate_token.make_token(myuser),
        })
        email = EmailMessage(
            email_subject,
            message2,
            settings.EMAIL_HOST_USER,
            [myuser.email],
        )
        email.fail_silently = True
        # email.send()

        messages.success(request, "Você foi registrado com sucesso no site")
        return render(request, "expressapp/logIn.html")

def logIn(request):
    if request.method == "POST":
        username = request.POST['username']
        pass1 = request.POST['pass1']
        user = authenticate(request, username=username, password=pass1)

        if user is not None:
            login(request, user)
            messages.success(request, "Você está logado")
            return render(request, "expressapp/index.html", {'username': username})

        else:
            messages.error(request, "Credenciais erradas ou inexistentes")
            return render(request, "expressapp/logIn.html")
    return render(request, "expressapp/logIn.html")


class LogOut(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        messages.success(request, "Você logou com sucesso!")
        return render(request, "expressapp/index.html")

def activate(request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            myuser = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            myuser = None

        if myuser is not None and generate_token.check_token(myuser, token):
            myuser.is_active = True
            # user.profile.signup_confirmation = True
            myuser.save()
            login(request, myuser)
            messages.success(request, "Sua conta foi ativada!")
            # context = {'uidb64': uidb64, 'token': token}
            return render(request, "expressapp/logIn.html")
        else:
            return render(request, 'expressapp/activation_failed.html')

def profile(request, username):
    try:
        profile = Profile.objects.get(user=username)
        context = {'profile': profile}
        return render(request, "expressapp/profile.html", context)
    except Profile.DoesNotExist:
        # Handle the case where the profile does not exist
        # For example, you can redirect to a 404 page
        profile = User.objects.get(username=username)
        context = {'profile': profile}
        return render(request, "expressapp/profile.html", context)

def booking(request, pk):
    if request.user.is_authenticated:
        bookings=Booking.objects.filter(riders_id=pk)

        context={'bookings':bookings}
        return render(request, "expressapp/yourBookings.html", context)

def yourRides(request, pk):
    rides = RideModel.objects.filter(user=pk)
    context={"rides":rides}
    return render(request, "expressapp/yourRides.html", context)

def riderInfo(request, id):
    context={}
    bookings=[]
    user=[]
    allrides = Booking.objects.all()
    for ride in allrides:
        print(ride.post.id)
        if ride.post.id == id:
            bookings.append(ride.riders_id)
    
    riders_profile=User.objects.filter(id__in = bookings)

    context={'riders_profile':riders_profile}
    return render(request, "expressapp/riderInfo.html", context)

def editProfile(request):
    if request.method=='POST':
        user=request.POST.get('user')
        first_name=request.POST.get('first_name')
        last_name=request.POST.get('last_name')
        contact_no=request.POST.get('phone')
        email=request.POST.get('email')

        # if profile is already saved then update the profile otherwise save it
        if Profile.objects.filter(user=user).exists():
            profile=Profile.objects.get(user=user)
            profile.contact_no=contact_no
            profile.save()
            messages.success(request, "Seu perfil foi atualizado com sucesso!")
        else:
            profile= Profile(user=user, first_name=first_name, last_name=last_name,email=email, contact_no=contact_no)
            profile.save()
            messages.success(request, "Seu perfil foi salvo com sucesso!")
        return redirect('/')
    return render(request, "expressapp/editProfile.html")
