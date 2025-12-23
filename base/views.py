from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .models import Room, Topic, Message, User
from .forms import RoomForm, UserForm, MyUserCreationForm


# Create your views here.
def loginPage(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email').lower() #To get username from request based on the field name in form(username) 
        password = request.POST.get('password') #To get password from request based on the field name in form(password) 
    
        try:
            user = User.objects.get(email=email) #To get user from databases inbuilt user table based on the email 
        except:
            messages.error(request, 'User does not exist') # To add eroor messages to the list which are stored for a single session only

        user = authenticate(request, email=email, password=password) # Matches the credintials and returns an object if valid user else returns none
        if user is not None:
            login(request,user) #Logins user and adds the session of user to the database and browser
            return redirect('home') # return to home page by calling name of the url route
        else:
            messages.error(request, 'Login Failed') # To add eroor messages to the list which are stored for a single session only

    context={'page':'login'}
    return render(request, 'base/login_register.html',context)


def logoutUser(request):
    logout(request) # inbuilt method to logout user; this deletes the session of the user
    return redirect('home')


def registerUser(request):
    form = MyUserCreationForm()

    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False) # gets the form rsponse from user
            user.username = user.username.lower()
            user.save() # Save the user object instance
            login(request, user) # logs user
            return redirect('home')
        else:
            messages.error(request, 'An Eroor in regis')

    context = {'page':'register', 'form':form}
    return render(request, 'base/login_register.html',context)


def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''

    rooms =Room.objects.filter( Q(topic__name__icontains=q) | Q(name__icontains=q) | Q(description__icontains=q) )
    topics = Topic.objects.all()[0:5]
    room_count = rooms.count()
    activities = Message.objects.all().order_by('-updated').filter( Q(room__topic__name__icontains=q) )

    context = {'rooms' : rooms , 'topics':topics, 'room_count':room_count, 'activities':activities}
    return render(request, 'base/home.html', context)


def room(request , pk):    
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all().order_by('-created')  #related name of message model is message_set by default

    if request.method == 'POST':
        message = Message.objects.create(
            user = request.user,
            room = room,
            body = request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room', pk = room.id)

    context = {'room' : room, 'room_messages':room_messages}
    return render(request, 'base/room.html',context)


def userProfile(request, pk):
    q = request.GET.get('q') if request.GET.get('q') != None else ''


    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    topics = Topic.objects.all()
    activities =  user.message_set.all().order_by('-updated')
    # Message.objects.all().order_by('-updated').filter( Q(room__topic__name__icontains=q) and Q(user=user) )

    context = {'user': user, 'rooms':rooms, 'topics': topics, 'activities':activities}
    return render(request, 'base/profile.html', context)


@login_required(login_url='login')
def createRoom(request):
    form = RoomForm()

    if request.method == 'POST':
        form = RoomForm(request.POST)

        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)

        Room.objects.create(
            host = request.user,
            topic = topic,
            name = request.POST.get('name'),
            description = request.POST.get('description')
        )

        return redirect('home')           
        
    topics = Topic.objects.all()

    context = {'form':form, 'topics':topics}
    return render(request, 'base/room_form.html', context )


@login_required(login_url='login') #only executes view if the user is logged in
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)

    if request.user != room.host:
        return HttpResponse('You are not allowed here!!')

    if request.method == 'POST':

        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)

        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()

        return redirect('home')

    topics = Topic.objects.all()

    context = {'form':form, 'topics':topics, 'room':room, 'page': "update"}
    return render(request, 'base/room_form.html',context)


@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)

    if request.user != room.host:
        return HttpResponse('You are not allowed here!!')

    if request.method == 'POST':
        room.delete()
        return redirect('home')

    context = {'obj': room}
    return render(request, 'base/delete.html',context)


@login_required(login_url='login')
def deleteMessage(request,pk):
    message = Message.objects.get(id=pk)

    if request.user != message.user:
        return HttpResponse('You are not allowed delete!!')

    if request.method == 'POST':
        message.delete()
        return redirect('room', pk = message.room.id)

    context = {'obj': message}
    return render(request, 'base/delete.html',context)

@login_required(login_url='login')
def updateUser(request):

    user = request.user
    form = UserForm(instance= user )

    if request.method == "POST":
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile',pk=user.id )

    context = {'form':form}
    return render(request, 'base/update-user.html', context)

def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)
    context = {'topics': topics }
    return render(request, 'base/topics.html', context)

def activitiesPage(request):
    activities = Message.objects.all()
    context = {'activities': activities }
    return render(request, 'base/activity.html', context)