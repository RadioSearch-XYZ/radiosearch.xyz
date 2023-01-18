from flask import Flask, render_template, redirect, request, session, abort
from flask_sqlalchemy import SQLAlchemy
import uuid
from flask_login import LoginManager, login_user, current_user, login_required, UserMixin
from zenora import APIClient, User
from dhooks import Webhook, Embed
from functools import wraps
from sqlalchemy import desc
from dotenv import load_dotenv
import os
from functools import wraps
from dhooks import Webhook, Embed
from flask_session_captcha import FlaskSessionCaptcha
from flask_sessionstore import Session
import yaml

cfg = yaml.safe_load("config.yaml")

load_dotenv()

app = Flask(__name__)
client = APIClient(os.getenv("TOKEN"),
                   client_secret=os.getenv("CLIENT_SECRET"))
app = Flask(__name__)
app.config["SECRET_KEY"] = uuid.uuid4()
app.config["SQLALCHEMY_DATABASE_URI"] = cfg["db"]["addr"]
app.config['CAPTCHA_ENABLE'] = True
app.config['CAPTCHA_LENGTH'] = cfg["captcha"]["length"]
app.config['CAPTCHA_WIDTH'] = 160
app.config['CAPTCHA_HEIGHT'] = 60
app.config['CAPTCHA_SESSION_KEY'] = f'captcha_{cfg["captcha"]["type"]}'
app.config['SESSION_TYPE'] = 'sqlalchemy'
app.app_context().push()
db = SQLAlchemy(app)
Session(app)

captcha = FlaskSessionCaptcha(app)
TEAM = cfg["team"]
loginManager = LoginManager(app)

luna = Webhook(
    os.environ["LUNA"])
lina = Webhook(
    os.environ["LINA"])
lana = Webhook(
    os.environ["LANA"])


def get_discord():
    class U:
        def __init__(self, **vars):
            for k, v in vars.items():
                setattr(self, k, v)
    print(session["USER"])
    if session["USER"]:
        return U(**session["USER"])
    else:
        return U(name="Jane Doe", avatar_url="https://directemployers.org/wp-content/uploads/2018/08/avatar-JaneDoe.jpg", id=0, accent_color=None, discriminator="0000")


@loginManager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.errorhandler(401)
def unauthorized(e=None):
    return render_template("unauthorized.html", current_user=current_user, discord=get_discord())


@app.errorhandler(403)
def forbidden(e=None):
    return render_template("forbidden.html", current_user=current_user, discord=get_discord())


@app.errorhandler(404)
def notfound(e=None):
    return render_template("notFound.html", current_user=current_user, discord=get_discord())


def admin_ensure(func):

    @wraps(func)
    def predicate(*args, **kwargs):
        if current_user.id in TEAM:
            return func(*args, **kwargs)
        return abort(403)
    return predicate


class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    bio = db.Column(db.String(150))


class Radio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(512))
    image_url = db.Column(db.String(512))
    vote_count = db.Column(db.Integer, default=0, nullable=True)
    approved = db.Column(db.Integer, default=0, nullable=True)
    link = db.Column(db.String(200))
    owner = db.Column(db.Integer)
    short = db.Column(db.String(200))
    long = db.Column(db.String(10000))


@app.before_request
def before_request():
    if not "USER" in session:
        session["USER"] = {}
    return


@app.route("/")
def root():
    return render_template("index.html", current_user=current_user, radios=(Radio.query.filter_by(approved=1).all()))


@app.route("/top")
def top():
    return render_template("index.html", current_user=current_user, radios=(Radio.query.filter_by(approved=1).order_by(desc(Radio.vote_count)).all()))


@app.route("/add-radio.dhp", methods=["POST"])
@login_required
def add_station():
    station_id = request.form["stationID"]
    short = request.form["shortDsc"]
    long = request.form["long"]
    image = request.form.get("imglink")
    invite = request.form["link"]

    station = Radio(owner=session["USER"]["id"], short=short, long=long, link=invite,
                    image_url=image, name=station_id)
    db.session.add(station)
    db.session.commit()
    e = Embed(color=0x5865F2)
    e.title = "Station Submitted"
    e.add_field("Station", f'{station_id}')
    e.add_field("User", f'<@{current_user.id}>')
    e.set_image(image)
    luna.send("<@&1064583842322722968>", embed=e)
    if captcha.validate():
        return render_template("success.html", current_user=current_user, discord=get_discord(), station=station)
    return '<script>history.back()</script>'


@app.route("/admin/station/<id>/approve")
@login_required
@admin_ensure
def station_approve(id):
    station: Radio = Radio.query.get(id)
    station.approved = 1
    db.session.commit()
    e = Embed()
    e.title = "Station Approved"
    e.add_field("Station", f'**[{station.name}](https://example.com)**')
    e.add_field("Owner", f'<@{station.owner}>')
    e.add_field("Moderator", f'<@{get_discord().id}>')
    lana.send(embed=e)
    return render_template("redirecting.html", current_user=current_user, discord=get_discord(), cstr="Station Approved! Redirecting...", to="/panel")


@app.route("/admin/<id>/decline", methods=["post"])
@login_required
@admin_ensure
def station_decline(id):
    station = Radio.query.get(id)
    db.session.delete(station)
    db.session.commit()
    e = Embed()
    e.title = "Station Declined"
    print("Station added")
    e.add_field("Station", f'**{station.name}**')
    e.add_field("Owner", f'<@{station.owner}>')
    e.add_field("Moderator", f'<@{get_discord().id}>')
    e.add_field("Reason", request.form["reason"])
    lana.send(f'<@{station.owner}>', embed=e)
    return render_template("redirecting.html", current_user=current_user, discord=get_discord(), cstr="Station Declined! Redirecting...", to="/panel")


@app.route("/admin/<int:id>")
@admin_ensure
def adminview(id):
    return render_template("staffradio.html", current_user=current_user, discord=get_discord(), radio=Radio.query.filter_by(id=id, approved=0).first())


@app.route("/view/<int:id>")
def view(id):
    return render_template("radio.html", current_user=current_user, discord=get_discord(), radio=Radio.query.filter_by(id=id, approved=1).first())


@app.route("/admin/<int:id>/decision")
@admin_ensure
def admindec(id):
    return render_template("decision.html", current_user=current_user, discord=get_discord(), station=Radio.query.filter_by(id=id, approved=0).first())


@app.route("/panel")
@admin_ensure
def adminpanel():
    return render_template("panel.html", current_user=current_user, discord=get_discord(), stations=Radio.query.filter_by(approved=0).all())


@app.route("/external_link")
def extlink():
    url = request.args.get("url")

    return render_template("redirecting.html", cstr=f'Redirecting you to external page "{url}"...', current_user=current_user, discord=get_discord(), to=url)


@app.route("/auth/login")
def login():
    return redirect(os.getenv("OAUTH_URL"))


@app.route("/submit")
@login_required
def submit():
    return render_template("addradio.html", current_user=current_user)


@app.route("/auth/callback")
def callback():
    code = request.args.get("code")
    resp = client.oauth.get_access_token(code, os.getenv("REDIRECT_URI"))
    bearer_client = APIClient(resp.access_token, bearer=True)
    currentUser = bearer_client.users.get_current_user()
    if User.query.filter_by(id=currentUser.id).first():
        u = User.query.filter_by(id=currentUser.id).first()
        login_user(u)
    else:
        u = User(id=currentUser.id, bio="Hey there!")
        db.session.add(u)
        db.session.commit()
        login_user(u)
    session["USER"] = {
        "name": currentUser.username,
        "id": currentUser.id,
        "avatar_url": currentUser.avatar_url,
        "accent_color": currentUser.accent_color,
        "discriminator": currentUser.discriminator,
    }
    lina.send(
        f"{currentUser.username} has logged in")
    return render_template("redirecting.html", current_user=current_user, discord=get_discord(), cstr="You are being logged in...", to="/")


if __name__ == "__main__":
    app.run(cfg["host"]["addr"], cfg["host"]["port"])
