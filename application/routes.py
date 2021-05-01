from datetime import datetime

from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

from application import app, db
from application.models import User, Post
from application.forms import LoginForm, RegistrationForm, EditProfileForm, FollowUnfollowForm, PostForm


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@app.route("/", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        post.save()
        flash("Your post is now live!")
        return redirect(url_for("index"))
    page = request.args.get("page", 1, type=int)
    posts = current_user.following_posts().paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_page = url_for("index", page=posts.next_num) \
        if posts.has_next else None
    prev_page = url_for("index", page=posts.prev_num) \
        if posts.has_prev else None
    return render_template("index.html", title="Home", form=form,
                            posts=posts.items, next_page=next_page,
                            prev_page=prev_page)


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        user.save()
        flash("You are now a registered user!")
        return redirect(url_for("login"))
    return render_template("register.html", title="Register", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.verify_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("login"))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("index")
        return redirect(next_page)
    return render_template("login.html", title="Sign in", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/user/<username>")
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()    
    page = request.args.get("page", 1, type=int)
    posts = user.posts.order_by(Post.created_on.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_page = url_for("user", username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_page = url_for("user", username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    form = FollowUnfollowForm()
    return render_template("user.html", user=user, form=form,
                            posts=posts.items, next_page=next_page,
                            prev_page=prev_page)


@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash("Your changes have been saved!")
        return redirect(url_for("edit_profile"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@app.route("/follow/<username>", methods=["POST"])
@login_required
def follow(username):
    form = FollowUnfollowForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash("User {username} not found")
            return redirect(url_for("index"))
        if user == current_user:
            flash("You cannot follow yourself!")
            return redirect(url_for("user", username=username))
        current_user.follow(user)
        db.session.commit()
        flash("You are now following {username}")
        return redirect(url_for("user", username=username))
    else:
        return redirect(url_for("index"))


@app.route("/unfollow/<username>", methods=["POST"])
@login_required
def unfollow(username):
    form = FollowUnfollowForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash("User {username} not found.")
            return redirect(url_for("index"))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash("You unfollowed {username}.")
        return redirect(url_for("user", username=username))
    else:
        return redirect(url_for("index"))


@app.route('/explore')
@login_required
def explore():
    page = request.args.get("page", 1, type=int)
    posts = Post.query.order_by(Post.created_on.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_page = url_for("explore", page=posts.next_num) \
        if posts.has_next else None
    prev_page = url_for("explore", page=posts.prev_num) \
        if posts.has_prev else None
    return render_template("index.html", title='Explore', posts=posts.items,
                            next_page=next_page, prev_page=prev_page)
