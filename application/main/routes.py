from flask import render_template, flash, redirect, url_for, \
    request, g, jsonify, current_app
from flask_babel import _, get_locale
from flask_login import current_user, login_user, logout_user, login_required

from datetime import datetime
from guess_language import guess_language
from werkzeug.urls import url_parse

from application import db
from application.main.forms import EditProfileForm, PostForm, \
    EmptyForm, SearchForm
from application.translate import translate
from application.models import User, Post
from application.main import bp


@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()
    g.locale = str(get_locale())


@bp.route("/search")
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for("main.explore"))
    page = request.args.get("page", 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page, 
                                current_app.config["POSTS_PER_PAGE"])
    next_page = url_for("main.search", q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config["POSTS_PER_PAGE"] else None

    prev_page = url_for("main.seatch", q=g.search_form.q.data, page=page -1) \
        if page > 1 else None

    return render_template("search.html", title=_l("Search"), posts=posts,
                            next_page=next_page, prev_page=prev_page)


@bp.route("/translate", methods=["POST", "GET"])
@login_required
def translate_text():
    text = translate(request.form["text"],
                        request.form["src_language"],
                        request.form["dest_language"])
    return jsonify({"text": text})


@bp.route("/", methods=["GET", "POST"])
@bp.route("/index", methods=["GET", "POST"])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        language = guess_language(form.post.data)
        if language == "UNKNOWN" or len(language) > 5:
            language = ""
        post = Post(body=form.post.data, author=current_user,
                    language=language)
        post.save()
        flash("Your post is now live!")
        return redirect(url_for("main.index"))
    page = request.args.get("page", 1, type=int)
    posts = current_user.following_posts().paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_page = url_for("main.index", page=posts.next_num) \
        if posts.has_next else None
    prev_page = url_for("main.index", page=posts.prev_num) \
        if posts.has_prev else None
    return render_template("index.html", title="Home", form=form,
                            posts=posts.items, next_page=next_page,
                            prev_page=prev_page)


@bp.route("/user/<username>")
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get("page", 1, type=int)
    posts = user.posts.order_by(Post.created_on.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_page = url_for("main.user", username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_page = url_for("main.user", username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    form = EmptyForm()
    return render_template("user.html", user=user, form=form,
                            posts=posts.items, next_page=next_page,
                            prev_page=prev_page)


@bp.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash("Your changes have been saved!")
        return redirect(url_for("main.edit_profile"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@bp.route("/follow/<username>", methods=["POST"])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(f"User {username} not found")
            return redirect(url_for("main.index"))
        if user == current_user:
            flash("You cannot follow yourself!")
            return redirect(url_for("main.user", username=username))
        current_user.follow(user)
        db.session.commit()
        flash(f"You are now following {username}")
        return redirect(url_for("main.user", username=username))
    else:
        return redirect(url_for("main.index"))


@bp.route("/unfollow/<username>", methods=["POST"])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash("User {username} not found.")
            return redirect(url_for("main.index"))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('main.user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(f"You unfollowed {username}.")
        return redirect(url_for("main.user", username=username))
    else:
        return redirect(url_for("main.index"))


@bp.route("/explore")
@login_required
def explore():
    page = request.args.get("page", 1, type=int)
    posts = Post.query.order_by(Post.created_on.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_page = url_for("main.explore", page=posts.next_num) \
        if posts.has_next else None
    prev_page = url_for("main.explore", page=posts.prev_num) \
        if posts.has_prev else None
    return render_template("index.html", title=_('Explore'), posts=posts.items,
                            next_page=next_page, prev_page=prev_page)


@bp.route("/user/<username>/popup")
@login_required
def user_pop(username):
    user = User.query.filter_by(username=username).first_or_404()
    print(user)
    form = EmptyForm()
    return render_template("user_popup.html", user=user, form=form)