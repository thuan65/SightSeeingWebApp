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
    login_form = LoginForm()
    register_form = RegisterForm()

    if login_form.submit.data and login_form.validate_on_submit():
        user = User.query.filter_by(username=login_form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, login_form.password.data):
            login_user(user)
            return redirect(url_for("index"))
        flash("Sai tài khoản hoặc mật khẩu", "danger")

    if register_form.submit.data and register_form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(register_form.password.data).decode("utf-8")
        user = User(username=register_form.username.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash("Đăng ký thành công!", "success")

    return render_template(
        "login.html",
        login_form=login_form,
        register_form=register_form
    )

# ---------------- LOGOUT ----------------
@login_bp.route("/logout")
def logout():
    session.pop('username', None)
    logout_user()
    flash("Bạn đã đăng xuất!", "info")
    return redirect(url_for("login_bp.login"))
