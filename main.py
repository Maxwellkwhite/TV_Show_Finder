from flask import Flask, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired
from sqlalchemy.orm import DeclarativeBase
from flask_sqlalchemy import SQLAlchemy
import requests
import random
import os
import smtplib


API_KEY = os.environ.get('MOVIE_API')
ORIGIN_COUNTRY = 'US'


categories_dictionary = {'Action & Adventure': 10759, 
                  'Animation': 16, 
                  'Comedy': 35, 
                  'Crime': 80, 
                  'Documentary': 99, 
                  'Drama': 18, 
                  'Family': 10751, 
                  'Kids': 10762, 
                  'Mystery': 9648, 
                  'News': 10763, 
                  'Reality': 10764, 
                  'Sci-Fi & Fantasy': 10765, 
                  'Soap': 10766, 
                  'Talk': 10767, 
                  'War & Politics': 10768, 
                  'Western': 37,}

movies_categories ={
    'Action': 28,
    'Adventure': 12,
    'Animation': 16, 
    'Comedy': 35, 
    'Crime': 80, 
    'Documentary': 99, 
    'Drama': 18, 
    'Family': 10751,
    'Fantasy': 14,
    'History':36,
    'Horror':27,
    'Music':10402,
    'Mystery': 9648,
    'Romance':10749,
    'Science Fiction':878,
    'TV Movie':10770,
    'Thriller':53,
    'War':10752,
    'Western': 37,}

app = Flask(__name__)
ckeditor = CKEditor(app)
Bootstrap5(app)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')

class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", 'sqlite:///users.db')
db = SQLAlchemy(model_class=Base)
db.init_app(app)

class Feedback(FlaskForm):
    feedback = StringField("Feedback", validators=[DataRequired()], render_kw={'class': 'form_class'})
    submit = SubmitField("Provide Feedback")

class TV_Filters(FlaskForm):
    category = SelectField(label="TV Show Category", choices=["Action & Adventure", 
                                                       "Animation", 
                                                       "Comedy",
                                                       "Crime",
                                                       "Documentary",
                                                       "Drama",
                                                       "Family",
                                                       "Kids",
                                                       "Mystery",
                                                       "News",
                                                       "Reality",
                                                       "Sci-Fi & Fantasy",
                                                       "Soap",
                                                       "Talk",
                                                       "War & Politics",
                                                       "Western"], render_kw={'class':'form_class'})
    with_type = SelectField("TV Show Type", choices=["Scripted", 
                                             "Documentary", 
                                             "Miniseries", 
                                             "Reality",  
                                             "Talk Show",
                                             "I Don't Care",], render_kw={'class':'form_class'})
    quality_of_show = SelectField("Quality of TV Show", choices=["I Don't Care", 
                                                              "Decent or Better", 
                                                              "Highly Rated"], render_kw={'class':'form_class'})
    popularity = SelectField("Popularity of TV Show", choices=["Popular", 
                                                            "Any Popularity",], render_kw={'class':'form_class'})
    submit = SubmitField("Find your show")

class Movie_Filters(FlaskForm):
    category = SelectField(label="Movie Category", choices=['Action',
                                                             'Adventure',
                                                             'Animation', 
                                                             'Comedy', 
                                                             'Crime', 
                                                             'Documentary', 
                                                             'Drama', 
                                                             'Family',
                                                             'Fantasy',
                                                             'History',
                                                             'Horror',
                                                             'Music',
                                                             'Mystery',
                                                             'Romance',
                                                             'Science Fiction',
                                                             'TV Movie',
                                                             'Thriller',
                                                             'War',
                                                             'Western',], render_kw={'class':'form_class'})
    quality_of_movie = SelectField("Quality of Movie", choices=["I Don't Care", 
                                                              "Decent or Better", 
                                                              "Highly Rated"], render_kw={'class':'form_class'})
    popularity = SelectField("Popularity of Movie", choices=["Popular", 
                                                            "Any Popularity",], render_kw={'class':'form_class'})
    submit = SubmitField("Find your Movie")

with app.app_context():
    db.create_all()

@app.route('/', methods=["GET", "POST"])
def find_show():
    form=TV_Filters()
    if form.validate_on_submit():
        list = []
        five_shows = []
        full_details = []
        seasons = []
        episodes = []
        show_id = []
        homepage = []
        #sets the page limit at 150 to purposefully fail to get actual page total
        page_to_fail=150
        category = form.category.data
        with_type = form.with_type.data
        quality_of_show = form.quality_of_show.data
        popularity = form.popularity.data
        #create blank type to fille the actual value into it
        type = ""
        if with_type == "Documentary":
            type = 0
        elif with_type == "Miniseries":
            type = 2
        elif with_type == "Reality":
            type = 3
        elif with_type == "Scripted":
            type = 4
        elif with_type == "Talk Show":
            type = 5
        elif with_type == "I Don't Care":
            type = ''
        # choices=["I Don't Care", "At least Decent", "Incredible"]
        quality = 0
        if quality_of_show == "I Don't Care":
            quality = 0
        elif quality_of_show == "Decent or Better":
            quality = 5
        elif quality_of_show == "Highly Rated":
            quality = 7.5
        popularity_value = 0
        if popularity == "Popular":
            popularity_value = 750
        elif popularity == "Any Popularity":
            popularity_value = 25
        param = {
        "include_adult":"true",
        "with_origin_country": ORIGIN_COUNTRY,
        "with_genres": categories_dictionary[category],
        "vote_average.gte": quality,
        "page": page_to_fail,
        "with_type": type,
        "vote_count.gte":popularity_value,
        }
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "accept": "application/json",
        }
        response = requests.get("https://api.themoviedb.org/3/discover/tv", headers=headers, params=param)
        data = response.json()
        #if the results don't produce a value, rerun the API using new API values
        if data['results'] == []:
            try:
                max_pages=data['total_pages']-1
                param = {
                "include_adult":"true",
                "with_origin_country": ORIGIN_COUNTRY,
                "with_genres": categories_dictionary[category],
                "vote_average.gte": quality,
                "page": random.randint(1, max_pages),
                "with_type": type,
                "vote_count.gte":popularity_value,
                }
                headers = {
                    "Authorization": f"Bearer {API_KEY}",
                    "accept": "application/json",
                }
                response = requests.get("https://api.themoviedb.org/3/discover/tv", headers=headers, params=param)
                data = response.json()
            except ValueError:
                x=data['total_pages']
                param = {
                "include_adult":"true",
                "with_origin_country": ORIGIN_COUNTRY,
                "with_genres": categories_dictionary[category],
                "vote_average.gte": quality,
                "page": 1,
                "with_type": type,
                "vote_count.gte":popularity_value,
                }
                headers = {
                    "Authorization": f"Bearer {API_KEY}",
                    "accept": "application/json",
                }
                response = requests.get("https://api.themoviedb.org/3/discover/tv", headers=headers, params=param)
                data = response.json()
            for x in range (data['total_results']):
                if data['total_results'] <= 19 and data['total_results'] >= 1:
                    show = data['results'][x]
                    list.append(show['name'])
                    full_details.append(show)
                elif data['total_results'] == 0:
                    pass
                else:
                    show = data['results'][random.randint(0,19)]
                    list.append(show['name'])
                    full_details.append(show)
            for x in range(5):
                try:
                    chosen_show = random.choice(full_details)
                    while chosen_show in five_shows:
                        chosen_show = random.choice(full_details)
                    five_shows.append(chosen_show)
                    full_details.remove(chosen_show)
                except IndexError: #used because some may not have 5 data points
                    pass
        for show in five_shows:
            response = requests.get(f"https://api.themoviedb.org/3/tv/{show['id']}?language=en-US", headers=headers, params=param)
            data = response.json()
            show_season = data['number_of_seasons']
            seasons.append(show_season)
            show_episodes = data['number_of_episodes']
            episodes.append(show_episodes)
            homepage_link = data['homepage']
            homepage.append(homepage_link)
        return render_template('tv_results.html', 
                               category=category, 
                               five_shows=five_shows, 
                               data=data, 
                               details=full_details,
                               genres=form.category.data,
                               quality=quality_of_show,
                               type=with_type,
                               seasons=seasons,
                               episodes=episodes,
                               homepage=homepage)
    return render_template("tv_index.html", form=form)

@app.route('/movie', methods=["GET", "POST"])
def find_movie():
    form=Movie_Filters()
    if form.validate_on_submit():
        list = []
        five_movies = []
        full_details = []
        seasons = []
        episodes = []
        show_id = []
        homepage = []
        budget_list = []
        runtime_list = []
        #sets the page limit at 501 to purposefully fail to get actual page total
        page_to_fail=500
        category = form.category.data
        quality_of_movie = form.quality_of_movie.data
        popularity = form.popularity.data
        #create blank type to fille the actual value into it
        # choices=["I Don't Care", "At least Decent", "Incredible"]
        quality = 0
        if quality_of_movie == "I Don't Care":
            quality = 0
        elif quality_of_movie == "Decent or Better":
            quality = 5
        elif quality_of_movie == "Highly Rated":
            quality = 7.5
        popularity_value = 0
        if popularity == "Popular":
            popularity_value = 1000
        else:
            popularity_value = 25
        param = {
        "include_adult":"true",
        "with_origin_country": ORIGIN_COUNTRY,
        "with_genres": movies_categories[category],
        "vote_average.gte": quality,
        "page": random.randint(1, page_to_fail),
        "vote_count.gte":popularity_value,
        }
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "accept": "application/json",
        }
        response = requests.get("https://api.themoviedb.org/3/discover/movie", headers=headers, params=param)
        movie_data = response.json()
        #if the results don't produce a value, rerun the API using new API values
        if movie_data['results'] == []:
            try:
                max_pages=movie_data['total_pages']-1
                param = {
                "include_adult":"true",
                "with_origin_country": ORIGIN_COUNTRY,
                "with_genres": movies_categories[category],
                "vote_average.gte": quality,
                "page": random.randint(1, max_pages),
                "with_type": type,
                "vote_count.gte":popularity_value,
                }
                headers = {
                    "Authorization": f"Bearer {API_KEY}",
                    "accept": "application/json",
                }
                response = requests.get("https://api.themoviedb.org/3/discover/movie", headers=headers, params=param)
                movie_data = response.json()
            except ValueError:
                x=movie_data['total_pages']
                param = {
                "include_adult":"true",
                "with_origin_country": ORIGIN_COUNTRY,
                "with_genres": movies_categories[category],
                "vote_average.gte": quality,
                "page": 1,
                "with_type": type,
                "vote_count.gte":popularity_value,
                }
                headers = {
                    "Authorization": f"Bearer {API_KEY}",
                    "accept": "application/json",
                }
                response = requests.get("https://api.themoviedb.org/3/discover/movie", headers=headers, params=param)
                movie_data = response.json()
            for x in range (movie_data['total_results']):
                if movie_data['total_results'] <= 19 and movie_data['total_results'] >= 1:
                    show = movie_data['results'][x]
                    list.append(show['title'])
                    full_details.append(show)
                elif movie_data['total_results'] == 0:
                    pass
                else:
                    show = movie_data['results'][random.randint(0,19)]
                    list.append(show['title'])
                    full_details.append(show)
            for x in range(5):
                try:
                    chosen_movie = random.choice(full_details)
                    while chosen_movie in five_movies:
                        chosen_movie = random.choice(full_details)
                    five_movies.append(chosen_movie)
                    full_details.remove(chosen_movie)
                except IndexError: #used because some may not have 5 data points
                    pass
        for show in five_movies:
            response = requests.get(f"https://api.themoviedb.org/3/movie/{show['id']}?language=en-US", headers=headers, params=param)
            movie_data = response.json()
            homepage_link = movie_data['homepage']
            homepage.append(homepage_link)
            budget = movie_data['budget']
            budget_list.append(budget)
            runtime = movie_data['runtime']
            runtime_list.append(runtime)
        return render_template('movie_results.html', 
                               category=category, 
                               five_movies=five_movies, 
                               data=movie_data, 
                               details=full_details,
                               genres=form.category.data,
                               quality=quality_of_movie,
                               seasons=seasons,
                               episodes=episodes,
                               homepage=homepage,
                               budget=budget_list,
                               runtime=runtime_list)
    return render_template("movie_index.html", form=form)

@app.route('/retry', methods=["GET", "POST"])
def retry():
    return redirect(url_for('find_show'))

@app.route('/search-movie', methods=["GET", "POST"])
def movie_redirect():
    return redirect(url_for('find_movie'))

@app.route('/privacy-policy', methods=['POST', 'GET'])
def privacy_policy():
    return render_template("privacy_policy.html")

@app.route('/terms-and-conditions', methods=['POST', 'GET'])
def terms_and_conditions():
    return render_template("terms_and_conditions.html")

@app.route('/feedback', methods=['POST', 'GET'])
def feedback():
    form=Feedback()
    if form.validate_on_submit():
        feedback = form.feedback.data
        my_email = os.environ.get('FROM_EMAIL')
        password = os.environ.get('EMAIL_PASS')
        connection = smtplib.SMTP("smtp.gmail.com", 587)
        connection.starttls()
        connection.login(user=my_email, password=password)
        connection.sendmail(from_addr=my_email, 
                            to_addrs=os.environ.get('TO_EMAIL'), 
                            msg=f"Subject:Feedback from Binge Buddy!\n\nFeedback: {feedback}",
                            )
        connection.close()
        flash('Feedback received! Thank you for taking the time to help.')
    return render_template("feedback.html", form=form)

if __name__ == "__main__":
    app.run(debug=False, port=5002)
