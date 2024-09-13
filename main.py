from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, RadioField, SelectField, PasswordField, SelectMultipleField, BooleanField
from wtforms.validators import DataRequired
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import requests
import random
import json

API_KEY = 'eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI3MmMwNDI3MmEzMjZhZDNiNTgzODdlMGVmYTkzOTNiNiIsIm5iZiI6MTcyNTYzNzkyOS4zMDg3NzgsInN1YiI6IjY2NmIzNDcyMmRmYzNhMjI1ZTVhYjRlMCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.dt6CNZe1TspH9bG5Y-kWE51xzS3sXRwoJGHnSqhRo_4'
ORIGIN_COUNTRY = 'US'
VOTE_COUNT_MIN = 25
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

app = Flask(__name__)
ckeditor = CKEditor(app)
Bootstrap5(app)
app.config['SECRET_KEY'] = 'ABCD1234'

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

class Base(DeclarativeBase):
    pass
# db_path = os.path.abspath(os.path.join(os.path.dirname("Final_Projects/Check_List_Site/instance"), "tasks.db"))
# app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///coach_listing.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Create a form to register new users
class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Sign Me Up!")

# Create a form to login existing users
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Let Me In!")

# Create a form to login existing users
class Filters(FlaskForm):
    category = SelectField("Choose Category", choices=["Action & Adventure", 
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
                                                       "Western"])
    with_type = SelectField("Type", choices=["I Don't Care",
                                             "Documentary", 
                                             "Miniseries", 
                                             "Reality", 
                                             "Scripted", 
                                             "Talk Show"])
    quality_of_show = SelectField("Quality of Show", choices=["I Don't Care", 
                                                              "Decent or Better", 
                                                              "Incredible"])
    submit = SubmitField("Show off")



# class InProgressTaskList(db.Model):
#     __tablename__ = "in_progress_tasks"
#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#     # Create Foreign Key, "users.id" the users refers to the tablename of User.
#     user_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
#     post: Mapped[str] = mapped_column(String(250), unique=False)
#     completed: Mapped[int] = mapped_column(Integer, nullable=True)
#     color: Mapped[str] = mapped_column(String(250))
#     project: Mapped[str] = mapped_column(String(250))
#     author = relationship("User", back_populates="tasks")

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
    # tasks = relationship("InProgressTaskList", back_populates="author")

with app.app_context():
    db.create_all()


@app.route('/', methods=["GET", "POST"])
def find_show():
    form=Filters()
    if form.validate_on_submit():
        list = []
        five_shows = []
        full_details = []
        #sets the page limit at 150 to purposefully fail to get actual page total
        page_to_fail=150
        category = form.category.data
        with_type = form.with_type.data
        quality_of_show = form.quality_of_show.data
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
        elif quality_of_show == "Incredible":
            quality = 8.5
        param = {
        "include_adult":"true",
        "with_origin_country": ORIGIN_COUNTRY,
        "with_genres": categories_dictionary[category],
        "vote_average.gte": quality,
        "vote_count.gte": VOTE_COUNT_MIN,
        "page": page_to_fail,
        "with_type": type,
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
                "vote_count.gte": VOTE_COUNT_MIN,
                "page": random.randint(1, max_pages),
                "with_type": type,
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
                "vote_count.gte": VOTE_COUNT_MIN,
                "page": 1,
                "with_type": type,
                }
                headers = {
                    "Authorization": f"Bearer {API_KEY}",
                    "accept": "application/json",
                }
                response = requests.get("https://api.themoviedb.org/3/discover/tv", headers=headers, params=param)
                data = response.json()
            for x in range (data['total_results']):
                if data['total_results'] <= 19 and data['total_results'] >= 1:
                    # x = data['results'][random.randint(0,data['total_results']-1)]['name']
                    # show = data['results'][random.randint(0,data['total_results']-1)]
                    show = data['results'][x]
                    list.append(show['name'])
                    full_details.append(show)
                elif data['total_results'] == 0:
                    pass
                else:
                    # x = data['results'][random.randint(0,19)]['name']
                    show = data['results'][random.randint(0,19)]
                    list.append(show['name'])
                    full_details.append(show)
            # myset = sorted(set(list))
            for x in range(5):
                try:
                    # chosen_show = random.choice(myset)
                    # five_shows.append(chosen_show)
                    # myset.remove(chosen_show)
                    chosen_show = random.choice(full_details)
                    while chosen_show in five_shows:
                        chosen_show = random.choice(full_details)
                    five_shows.append(chosen_show)
                    full_details.remove(chosen_show)
                except IndexError: #used because some may not have 5 data points
                    pass
        return render_template('results.html', category=category, five_shows=five_shows, data=data, details=full_details)
    return render_template("index.html", form=form)

# @app.route("/results", methods =["GET", "POST"])
# def results():
#     param = {
#     "include_adult":"true",
#     "page": 1,
#     "with_origin_country": "US",
#     "with_genres": 35,
#     "vote_average.gte":7,
#     "vote_count.gte":25,
#     }
#     headers = {
#         "Authorization": f"Bearer {API_KEY}",
#         "accept": "application/json",
#     }
#     response = requests.get("https://api.themoviedb.org/3/discover/tv", headers=headers, params=param)
#     data = response.text
#     return render_template("results.html", data=data)

    
@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        # Check if user email is already present in the database.
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if user:
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        # This line will authenticate the user with Flask-Login
        login_user(new_user)
        return redirect(url_for("all_coaches"))
    return render_template("register.html", form=form, current_user=current_user)

@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        # Note, email in db is unique so will only have one result.
        user = result.scalar()
        # Email doesn't exist
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        # Password incorrect
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('all_coaches'))

    return render_template("login.html", form=form, current_user=current_user)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('all_coaches'))

if __name__ == "__main__":
    app.run(debug=True, port=5002)
