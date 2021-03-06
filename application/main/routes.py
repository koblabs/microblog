from flask import render_template, flash, redirect, url_for, \
    request, g, jsonify, current_app
from flask_babel import _, get_locale
from flask_login import current_user, login_user, logout_user, login_required

from datetime import datetime
from guess_language import guess_language
from werkzeug.urls import url_parse

from application import db
from application.main.forms import EditProfileForm, PostForm, \
    EmptyForm, SearchForm, MessageForm
from application.translate import translate
from application.models.user import User
from application.models.post import Post
from application.models.notification import Notification
from application.models.message import Message
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

    return render_template("search.html", title=_("Search"), posts=posts,
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
        page, current_app.config["POSTS_PER_PAGE"], False)
    next_page = url_for("main.index", page=posts.next_num) \
        if posts.has_next else None
    prev_page = url_for("main.index", page=posts.prev_num) \
        if posts.has_prev else None
    return render_template("index.html", title=_("Home"), form=form,
                            posts=posts.items, next_page=next_page,
                            prev_page=prev_page)


@bp.route("/user/<username>")
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get("page", 1, type=int)
    posts = user.posts.order_by(Post.created_on.desc()).paginate(
        page, current_app.config["POSTS_PER_PAGE"], False)
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
    return render_template("edit_profile.html", title=_("Edit Profile"),
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
            flash("You cannot unfollow yourself!")
            return redirect(url_for("main.user", username=username))
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
        page, current_app.config["POSTS_PER_PAGE"], False)
    next_page = url_for("main.explore", page=posts.next_num) \
        if posts.has_next else None
    prev_page = url_for("main.explore", page=posts.prev_num) \
        if posts.has_prev else None
    return render_template("index.html", title=_("Explore"), posts=posts.items,
                            next_page=next_page, prev_page=prev_page)


@bp.route("/user/<username>/popup")
@login_required
def user_pop(username):
    user = User.query.filter_by(username=username).first_or_404()
    print(user)
    form = EmptyForm()
    return render_template("user_popup.html", user=user, form=form)


@bp.route("/send_message/<recipient>", methods=["GET", "POST"])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        message = Message(author=current_user, recipient=user,
                            body=form.message.data)
        message.save()
        user.add_notification("unread_message_count", user.new_messages())
        db.session.commit()
        flash(_("Message sent"))
        return redirect(url_for("main.user", username=recipient))
    return render_template("send_message.html", title=_("Send Message"),
                            form=form, recipient=recipient)


@bp.route("/messages")
@login_required
def messages():
    current_user.messages_last_read = datetime.utcnow()
    current_user.add_notification("unread_message_count", 0)
    db.session.commit()
    page = request.args.get("page", 1, type=int)
    messages = current_user.messages_received.order_by(
        Message.created_on.desc()).paginate(
            page, current_app.config["MESSAGES_PER_PAGE"], False)
    next_page = url_for("main.messages", page=messages.next_num) \
        if messages.has_next else None
    prev_page = url_for("main.messages", page=messages.prev_num) \
        if messages.has_prev else None
    return render_template("messages.html", messages=messages.items,
                            next_page=next_page, prev_page=prev_page)


@bp.route("/notifications")
@login_required
def notifications():
    since = request.args.get("since", 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.created_on > since).order_by(Notification.created_on.asc())
    return jsonify([{
        "name": n.name,
        "data": n.get_data(),
        "timestamp": n.created_on
    } for n in notifications])


@bp.route("/export_posts")
@login_required
def export_posts():
    if current_user.get_task_in_progress("export_posts"):
        flash(_("An export task is currently in progress"))
    else:
        current_user.launch_task("export_posts", _("Exporting posts..."))
        db.session.commit()
    return redirect(url_for("main.user", username=current_user.username))
