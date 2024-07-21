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
from catboost import CatBoostClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import pickle
import os
from .forms import CustomUserCreationForm, EditProfileForm, PasswordChangingForm
from django.http import HttpResponseBadRequest

def home(request):
    return render(request, 'home.html')

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
            form.save()
            messages.success(request, 'Registration successful! Please log in.')
            return redirect('login')
        else:
            messages.error(request, 'There has been some error during registration, please try again!')
    else:
        form = CustomUserCreationForm()
    return render(request, 'login.html', {'form': form})

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

cat_model = CatBoostClassifier()
cat_model.load_model('/home/neil/Projects/ConnectAI/connectai/models/catboost_model.bin')

# Load the other required objects
with open('/home/neil/Projects/ConnectAI/connectai/models/tfidf_vectorizer.pkl', 'rb') as f:
    tfidf_vectorizer = pickle.load(f)
with open('/home/neil/Projects/ConnectAI/connectai/models/LabelEncoder.pkl', 'rb') as f:
    label_encoder = pickle.load(f)

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

def match_personality(user_text, model, tfidf_vectorizer, label_encoder, compatibility_matrix):
    # Vectorize the user_text using the tfidf_vectorizer
    user_vectorized = tfidf_vectorizer.transform([user_text])
    
    # Predict the personality type
    predicted_label = model.predict(user_vectorized)[0]
    predicted_type = label_encoder.inverse_transform([predicted_label])[0]
    
    # Find compatible personalities based on the predicted type
    compatible_personalities = compatibility_matrix.get(predicted_type, [])
    
    return predicted_type, compatible_personalities

def predict(request):
    if request.method == 'POST':
        user_text = request.POST.get('description')
        
        if not user_text:
            # Handle the case where user_text is None or empty
            return HttpResponseBadRequest("Invalid input: user_text is required")
        
        # Call match_personality function
        predicted_type, compatible_personalities = match_personality(
            user_text, cat_model, tfidf_vectorizer, label_encoder, compatibility_matrix
        )

        profile, created = Profile.objects.get_or_create(user=request.user)
        
        # Update the predicted_personality field
        profile.personality_type = predicted_type
        profile.save()

            # Fetch other users with compatible personalities
        compatible_users = Profile.objects.filter(personality_type__in=compatible_personalities).exclude(user=request.user)

        # Render the result
        return render(request, 'result.html', {
            'predicted_type': predicted_type,
            'compatible_personalities': compatible_personalities,
            'compatible_users': compatible_users
        })
    
    return render(request, 'result.html')   

