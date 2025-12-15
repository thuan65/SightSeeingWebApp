from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from flask_login import login_user, logout_user, current_user
from extensions import db, bcrypt
from models import User
from forms import RegisterForm, LoginForm

login_bp = Blueprint("login_bp", __name__, url_prefix="/auth", template_folder='templates')

# ---------------- REGISTER----------------
@login_bp.route("/register", methods=["GET", "POST"])
def register():
    # Sử dụng prefix để tránh xung đột nếu sau này gộp trang
    form = RegisterForm(prefix="register")
    
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash("Tên đăng nhập đã tồn tại!", "danger")
            form.username.errors.append("Tên đăng nhập này đã được sử dụng.")
            return render_template("register.html", form=form)
        
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username=form.username.data, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        flash("Tạo tài khoản thành công! Hãy đăng nhập.", "success")
        return redirect(url_for("login_bp.login"))
        
    return render_template("register.html", form=form)

# ---------------- LOGIN (ĐÃ SỬA HOÀN CHỈNH) ----------------
@login_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    # Khởi tạo form với prefix để tách biệt dữ liệu
    login_form = LoginForm(prefix="login")
    register_form = RegisterForm(prefix="register")

    # 1. XỬ LÝ KHI BẤM NÚT ĐĂNG NHẬP
    # login_form.submit.data == True nghĩa là nút login đã được bấm
    if login_form.submit.data and login_form.validate():
        user = User.query.filter_by(username=login_form.username.data).first()
        
        if user and bcrypt.check_password_hash(user.password, login_form.password.data):
            login_user(user)
            session['username'] = user.username
            session['user_id'] = user.id
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for("index"))
        else:
            # Chỉ thêm lỗi vào field để hiện chữ đỏ dưới input (như hình bạn muốn)
            # KHÔNG dùng flash() ở đây để tránh hiện 2 thông báo trùng lặp
            login_form.password.errors.append("Sai tài khoản hoặc mật khẩu.")

    # 2. XỬ LÝ KHI BẤM NÚT ĐĂNG KÝ
    # register_form.submit.data == True nghĩa là nút register đã được bấm
    elif register_form.submit.data and register_form.validate():
        existing_user = User.query.filter_by(username=register_form.username.data).first()
        
        if existing_user:
            # Flash thông báo lỗi lớn ở trên
            flash("Tên đăng nhập đã tồn tại!", "register_error")
            # Và thêm dòng đỏ nhỏ dưới ô input
            register_form.username.errors.append("Tên đăng nhập này đã tồn tại.")
        else:
            hashed_pw = bcrypt.generate_password_hash(register_form.password.data).decode("utf-8")
            user = User(username=register_form.username.data, password=hashed_pw)
            db.session.add(user)
            db.session.commit()
            
            flash("Đăng ký thành công! Mời bạn đăng nhập.", "success")
            # Redirect về login để reset form
            return redirect(url_for("login_bp.login"))

    # Render template
    return render_template(
        "login.html",
        login_form=login_form,
        register_form=register_form
    )

# ---------------- LOGOUT ----------------
@login_bp.route("/logout")
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    logout_user()
    flash("Bạn đã đăng xuất thành công!", "info")
    return redirect(url_for("login_bp.login"))