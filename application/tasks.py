import time, json, sys

from flask import render_template

from rq import get_current_job

from application import create_app, db
from application.models.task import Task
from application.models.user import User
from application.models.post import Post
from application.email import send_mail


app = create_app()
app.app_context().push()


def _set_task_progress(progress):
    job = get_current_job()
    if job:
        job.meta["progress"] = progress
        job.save_meta()
        task = Task.query.get(job.get_id())
        task.user.add_notification("task_progress",{
                                    "task_id": job.get_id(),
                                    "progress": progress})
        if progress >= 100:
            task.complete = True
        db.session.commit()


def export_posts(user_id):
    try:
        # read user posts from database
        user = User.query.get(user_id)
        _set_task_progress(0)
        data = []
        i = 0
        total_posts = user.posts.count()
        for post in user.posts.order_by(Post.created_on.asc()):
            data.append({'body': post.body,
                         'timestamp': post.created_on.isoformat() + 'Z'})
            time.sleep(5)
            i += 1
            _set_task_progress(100 * i // total_posts)

        # send email with data to user
        send_mail("[Microblog] Your blog posts",
                sender=app.config["ADMINS"][0], recipients=[user.email],
                body=render_template("email/export_posts.txt", user=user),
                html=render_template("email/export_posts.html",
                                          user=user),
                attachments=[("posts.json", "application/json",
                              json.dumps({"posts": data}, indent=4))],
                sync=True)
    except:
        app.logger.error("Unhandled exception", exc_info=sys.exc_info())
    finally:
        _set_task_progress(100)


def export(seconds):
    job = get_current_job()
    print("Starting task")
    for i in range(seconds):
        job.meta["progress"] = 100.0 * i / seconds
        job.save_meta()
        print(i)
        time.sleep(1)
    job.meta["progress"] = 100
    job.save_meta()
    print("Task completed")
