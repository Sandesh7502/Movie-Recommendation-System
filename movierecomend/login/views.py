import pickle
import numpy as np
import pandas as pd
from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
import requests
from django.http import JsonResponse

@login_required(login_url='login')
def HomePage(request):
    return render(request, 'home.html')


def SignupPage(request):
    if request.method == 'POST':
        uname = request.POST.get('username')
        email = request.POST.get('email')
        pass1 = request.POST.get('password1')
        pass2 = request.POST.get('password2')

        if pass1 != pass2:
            return HttpResponse("Your password and confirm password are not the same!")
        else:
            my_user = User.objects.create_user(uname, email, pass1)
            my_user.save()
            return redirect('login')

    return render(request, 'signup.html')


def LoginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        pass1 = request.POST.get('pass')
        user = authenticate(request, username=username, password=pass1)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return HttpResponse("Username or Password is incorrect!!!")

    return render(request, 'login.html')


def LogoutPage(request):
    logout(request)
    return redirect('login')





def recommend_ui(request):
    username = request.session.get('username')
    return render(request, 'recommend.html', {'username': username})
  


 
def Home(request):
    return render(request, 'home.html')


def fetch_poster(movie_id):
    url = "https://api.themoviedb.org/3/movie/{}?api_key=8265bd1679663a7ea12ac168da84d2e8&language=en-US".format(movie_id)
    data = requests.get(url)
    data = data.json()
    poster_path = data['poster_path']
    full_path = "https://image.tmdb.org/t/p/w500/" + poster_path
    return full_path

def get_movie_titles_view(request):
    input = request.GET.get('input', '')
    
    # Load movie data from pickle file
    with open('login/movies.pkl', 'rb') as file:
        movies = pickle.load(file)
    
    # Filter movie titles based on input
    filtered_titles = movies[movies['title'].str.contains(input, case=False)]['title'].values.tolist()
    
    return JsonResponse(filtered_titles, safe=False)

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def recommend_movies(request):
    if request.method == 'POST':
        username = request.session.get('username')
        searched_movie_title = request.POST['movie_title']

        with open('login/movies.pkl', 'rb') as file:
            movies = pickle.load(file)
        with open('login/reducedfeature_vectors.pkl', 'rb') as file:
            reducedfeature_vectors = pickle.load(file)

        if searched_movie_title not in movies['title'].values:
            return HttpResponse("Sorry, we could not find the movie you are looking for!")

        movie_id = movies[movies['title'] == searched_movie_title].index[0]

        k = 5  # Number of nearest neighbors


        similarities = []
        for i, vector in enumerate(reducedfeature_vectors):
            if i != movie_id:
                sim = cosine_similarity(reducedfeature_vectors[movie_id], vector)
                similarities.append((i, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)
        neighbors = similarities[:k]

        recommended_movies = []
        for neighbor in neighbors:
            movie_info = movies.iloc[neighbor[0]]
            poster_url = fetch_poster(movie_info['id'])
            recommended_movies.append({
                'Title': movie_info['title'],
                'cosinesimilarity_score': neighbor[1],
                'Genres': movie_info['genres'],
                'Cast': movie_info['cast'],
                'Poster': poster_url
            })

        return render(request, 'recommend.html', {'username': username, 'searched_movie_title': searched_movie_title, 'recommended_movies': recommended_movies})

    else:  # Handle the initial GET request
      username = request.session.get('username')
    return render(request, 'recommend.html', {'username': username})

