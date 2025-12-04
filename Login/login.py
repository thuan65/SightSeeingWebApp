from flask import Blueprint, render_template, redirect, url_for, flash, session
from flask_login import login_user, logout_user, current_user
from extensions import db, bcrypt
from models import User
from forms import RegisterForm, LoginForm

login_bp = Blueprint("login_bp", __name__, url_prefix="/auth",template_folder='templates')

# ---------------- REGISTER ----------------
@login_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username=form.username.data, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        flash("Tạo tài khoản thành công! Hãy đăng nhập.", "success")
        return redirect(url_for("login_bp.login"))
    return render_template("register.html", form=form)

# ---------------- LOGIN ----------------
@login_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            session['username'] = user.username
            session['user_id'] = user.id
            return redirect(url_for("index"))
        flash("Sai tên đăng nhập hoặc mật khẩu!", "danger")

    return render_template("login.html", form=form)

# ---------------- LOGOUT ----------------
@login_bp.route("/logout")
def logout():
    session.pop('username', None)
    logout_user()
    flash("Bạn đã đăng xuất!", "info")
    return redirect(url_for("login_bp.login"))
