from flask import Flask, flash, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_cors import CORS, cross_origin
import random
import os

app = Flask(__name__)

# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///documents.db").replace("postgres://", "postgresql://")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
Bootstrap(app)
CORS(app)

## Words ADD Form
class WordForm(FlaskForm):
    word = StringField('word', validators=[DataRequired()])
    pronunciation = StringField('pronunciation')
    meaning1 = StringField('meaning1', validators=[DataRequired()])
    sentence1 = StringField('sentence1', validators=[DataRequired()])
    meaning2 = StringField('meaning2')
    sentence2 = StringField('sentence2')
    meaning3 = StringField('meaning3')
    sentence3 = StringField('sentence3')
    submit = SubmitField('Submit')


## Words TABLE Configuration
class NewWord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(20), unique=True, nullable=False)
    pronunciation = db.Column(db.String(20))
    meaning1 = db.Column(db.String(300), nullable=False)
    meaning2 = db.Column(db.String(300), nullable=False)
    meaning3 = db.Column(db.String(300), nullable=False)


class LearnedWord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(20), unique=True, nullable=False)


db.create_all()

def get_new_words():
    return db.session.query(NewWord).all()


def get_learned_words():
    return db.session.query(LearnedWord).all()


@app.route("/")
def home():
    new_words = get_new_words()
    if len(new_words) > 10:
        chose_words = []
        while len(chose_words) < 10:
            word = random.choice(new_words)
            if word not in chose_words:
                chose_words.append(word)
        return render_template("index.html", new_words=chose_words, len=len(new_words))
    return render_template("index.html", new_words=new_words, len=len(new_words))


@app.route("/add", methods=["GET", "POST"])
@cross_origin()
def add():
    form = WordForm()

    ## set the placeholder
    try:
        word = request.args['word']
    except KeyError:
        word = ""

    if form.validate_on_submit():
        new_word = NewWord(
            word=form.word.data,
            pronunciation=form.pronunciation.data,
            meaning1=f"{form.meaning1.data}@{form.sentence1.data}",
            meaning2=f"{form.meaning2.data}@{form.sentence2.data}",
            meaning3=f"{form.meaning3.data}@{form.sentence3.data}",
        )

        db.session.add(new_word)
        db.session.commit()

        return redirect("/")
    link = f"https://www.google.com.tw/search?q={word}"
    return render_template("add.html", form=form, word=word, link=link)


@app.route("/review")
def review():
    learned_words = get_learned_words()
    return render_template("review.html", learned_words=learned_words, len=len(learned_words))


@app.route("/search", methods=["GET", "POST"])
@cross_origin()
def search(word=None):
    # POST: go from form
    if request.method == "POST":
        searching_word = request.form.get('search').replace(" ", "")
        if NewWord.query.filter_by(word=searching_word).first():
            searching_word = NewWord.query.filter_by(word=searching_word).first()
            flash(f"It's already in your list.")
            return render_template("search.html", searching_word=vars(searching_word))
        elif LearnedWord.query.filter_by(word=request.form.get('search')).first():
            flash(f"You've already learned '{searching_word}'. Go review it.")
            return redirect('review')
        else:
            return redirect(url_for('add', word=searching_word))

    # GET: go from link
    searching_word = NewWord.query.filter_by(word=request.args['word']).first()
    return render_template("search.html", searching_word=vars(searching_word))


@app.route("/learn/<id>")
def is_learned(id):
    word_is_learned = NewWord.query.get(id)

    ## ADD in learned word
    learned_word = LearnedWord(word=word_is_learned.word)
    db.session.add(learned_word)
    db.session.commit()

    ## DELETE in new word
    db.session.delete(word_is_learned)
    db.session.commit()

    return redirect("/")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
