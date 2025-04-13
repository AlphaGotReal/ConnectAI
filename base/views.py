from django.shortcuts import render
from .models import Room
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib import auth
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render
from .models import Room
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib import auth
from django.contrib.auth.forms import UserCreationForm
from .models import Profile
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from random import randint
# from catboost import CatBoostClassifier
# from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import pickle
import os
from .forms import CustomUserCreationForm, EditProfileForm, PasswordChangingForm
from django.http import HttpResponseBadRequest

def home(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    personality_type = profile.personality_type

    compatible_personalities = compatibility_matrix.get(profile.personality_type, [])

    compatible_users = Profile.objects.filter(personality_type__in=compatible_personalities).exclude(user=request.user)

    return render(request, 'home.html', {
        'predicted_type': personality_type,
        'compatible_personalities': compatible_personalities,
        'compatible_users': compatible_users
    })

def landing(request):
    return render(request, 'landing.html')

def room(request):
    rooms = Room.objects.all()
    context = {'rooms': rooms} 
    return render(request, 'room.html', context)

def login(request):
    page = 'login'
    context = {'page' : page}

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, 'User does not exist')
            return redirect('login')  # Redirect to login page with error message

        user = authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)
            messages.success(request, 'You have successfully logged in.')
            return redirect('home')  # Redirect to home page after successful login
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html', context)

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, '✅ Registration successful! Please log in.')
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"❌ {field.capitalize()}: {error}")
            messages.error(request, '⚠️ There were errors in your registration form. Please correct them and try again.')
    else:
        form = CustomUserCreationForm()

    return render(request, 'login.html', {'form': form, 'page': 'register'})

@login_required
def profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    return render(request, 'profile.html', {'profile': profile})

@login_required
def edit_profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = EditProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = EditProfileForm(instance=profile)
    return render(request, 'editProfile.html', {'form': form})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangingForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important to update session with new password hash
            messages.success(request, 'Password changed successfully.')
            return redirect('profile')  # Redirect to profile page after password change
    else:
        form = PasswordChangingForm(request.user)
    return render(request, 'change_password.html', {'form': form})

def logout(request):
    auth.logout(request)
    messages.success(request, 'You have successfully logged out.')
    return redirect('login')  # Redirect to home page after logout

def connect(request):
    # Check if the user is authenticated
    if request.user.is_authenticated:
        # Try to get the user's profile
        profile, created = Profile.objects.get_or_create(user=request.user)
        if profile.personality_type:
            # Fetch compatible personalities
            compatible_personalities = compatibility_matrix.get(profile.personality_type, [])
            # Fetch other users with compatible personalities
            compatible_users = Profile.objects.filter(personality_type__in=compatible_personalities).exclude(user=request.user)
            # Render the connect page with compatible users
            return render(request, 'connect.html', {'compatible_users': compatible_users})
        else:
            # Redirect to personality test page if personality_type is not set
            return redirect('personality_test')
    else:
        # Handle the case where the user is not authenticated
        return redirect('login')
    
def personality_test(request):
    return render(request, 'personality_test.html', {}) 

compatibility_matrix = {
    'INTJ': ['ENTP', 'INTP', 'ENTJ', 'INFJ'],
    'INTP': ['ENTJ', 'INTJ', 'ENTP', 'INFP'],
    'ENTJ': ['INTP', 'ENTP', 'INTJ', 'INFJ'],
    'ENTP': ['INTJ', 'ENTJ', 'INTP', 'ENFP'],
    'INFJ': ['ENFP', 'INFP', 'INTP', 'ENTP'],
    'INFP': ['ENFJ', 'INFJ', 'ENFP', 'INTJ'],
    'ENFJ': ['INFJ', 'ENFP', 'INTJ', 'ENTP'],
    'ENFP': ['INFP', 'ENFJ', 'INTJ', 'ENTP'],
    'ISTJ': ['ESTP', 'ISFJ', 'ESFJ', 'ISTP'],
    'ISFJ': ['ESFJ', 'ISTJ', 'ESTJ', 'ISFP'],
    'ESTJ': ['ISTJ', 'ESTP', 'ESFJ', 'ENTJ'],
    'ESFJ': ['ISFJ', 'ESFP', 'ESTJ', 'ENFJ'],
    'ISTP': ['ESTP', 'ISFP', 'INTP', 'ISTJ'],
    'ISFP': ['ESFP', 'ISTP', 'INFP', 'ISFJ'],
    'ESTP': ['ISTP', 'ESTJ', 'ENTP', 'ESFP'],
    'ESFP': ['ISFP', 'ESTP', 'ENFP', 'ESFJ']
}

def personality_quiz(answers):
    global E, I, S, N, T, F, J, P
    """Determines personality type based on quiz answers"""
    
    # Initialize scores
    E, I = 0, 0
    S, N = 0, 0
    T, F = 0, 0
    J, P = 0, 0

    # Mapping questions to personality dimensions
    questions = [
        ('E', 'I'), ('E', 'I'), ('E', 'I'),
        ('J', 'P'), ('S', 'N'), ('S', 'N'),
        ('T', 'F'), ('T', 'F'), ('J', 'P'),
        ('J', 'P')
    ]
        
    # Assign scores based on user answers
    for index, answer in enumerate(answers):
        if answer == 'a':
            globals()[questions[index][0]] += 1
        elif answer == 'b':
            globals()[questions[index][1]] += 1
        else:
            globals()[questions[index][0]] += randint(0, 1)

    # Determine personality type
    personality_type = f"{'E' if E > I else 'I'}{'S' if S > N else 'N'}{'T' if T > F else 'F'}{'J' if J > P else 'P'}"
    
    return personality_type

def predict(request):
    if request.method == 'POST':
        # Extract answers from the form input (questions q1 to q10)
        answers = [request.POST.get(f'q{i}') for i in range(1, 11)]

        # Determine the personality type based on the answers
        predicted_type = personality_quiz(answers)

        # Get compatible personality types from the compatibility matrix
        compatible_personalities = compatibility_matrix.get(predicted_type, [])

        # Update the user's profile with the predicted personality type
        profile, created = Profile.objects.get_or_create(user=request.user)
        profile.personality_type = predicted_type
        profile.save()

        # Find users with compatible personality types, excluding the current user
        compatible_users = Profile.objects.filter(personality_type__in=compatible_personalities).exclude(user=request.user)

        # Render the result page with the predicted type, compatible personalities, and compatible users
        return render(request, 'result.html', {
            'predicted_type': predicted_type,
            'compatible_personalities': compatible_personalities,
            'compatible_users': compatible_users
        })

    # Handle GET request or return empty form
    return render(request, 'result.html')

def chat_room(request, room_name):
    return render(request, 'chat_room.html', {'room_name': room_name})
