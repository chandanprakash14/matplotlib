import os
from datetime import datetime
from functools import wraps
from urllib.parse import quote

from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif", "svg"}
WHATSAPP_NUMBER = "7539967397"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-this-in-production")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'database.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


class Saree(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_filename = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)


class WhatsappEnquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    saree_id = db.Column(db.Integer, db.ForeignKey("saree.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_image(file_storage) -> str:
    filename = secure_filename(file_storage.filename)
    if not filename or not allowed_file(filename):
        return ""

    unique_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}_{filename}"
    file_storage.save(os.path.join(app.config["UPLOAD_FOLDER"], unique_name))
    return unique_name


def admin_login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "admin_id" not in session:
            flash("Please log in to access admin pages.", "warning")
            return redirect(url_for("admin_login"))
        return view_func(*args, **kwargs)

    return wrapper


def ensure_default_admin() -> None:
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")

    if not Admin.query.filter_by(username=admin_username).first():
        db.session.add(
            Admin(
                username=admin_username,
                password=generate_password_hash(admin_password),
            )
        )
        db.session.commit()


def ensure_seed_sarees() -> None:
    if Saree.query.count() > 0:
        return

    demo_sarees = [
        Saree(
            name="Kanchipuram Royal Maroon",
            price=8999,
            image_filename="demo_maroon.svg",
            description="Elegant maroon Kanchipuram silk saree with traditional zari border and rich pallu.",
        ),
        Saree(
            name="Banarasi Emerald Weave",
            price=7499,
            image_filename="demo_emerald.svg",
            description="Premium Banarasi silk saree in emerald green, woven with floral gold motifs.",
        ),
    ]
    db.session.add_all(demo_sarees)
    db.session.commit()


@app.route("/")
def home():
    sarees = Saree.query.order_by(Saree.id.desc()).all()
    return render_template("home.html", sarees=sarees)


@app.route("/saree/<int:saree_id>")
def product_details(saree_id):
    saree = Saree.query.get_or_404(saree_id)
    message = (
        "Hi, I want to buy this saree:\n"
        f"Name: {saree.name}\n"
        f"Price: ₹{saree.price:,.2f}"
    )
    whatsapp_link = f"https://wa.me/{WHATSAPP_NUMBER}?text={quote(message)}"
    return render_template("product_details.html", saree=saree, whatsapp_link=whatsapp_link)


@app.post("/saree/<int:saree_id>/track-enquiry")
def track_enquiry(saree_id):
    Saree.query.get_or_404(saree_id)
    db.session.add(WhatsappEnquiry(saree_id=saree_id))
    db.session.commit()
    return {"status": "ok"}


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password, password):
            session["admin_id"] = admin.id
            session["admin_username"] = admin.username
            flash("Logged in successfully.", "success")
            return redirect(url_for("admin_dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template("admin_login.html")


@app.route("/admin/logout")
@admin_login_required
def admin_logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("admin_login"))


@app.route("/admin/dashboard")
@admin_login_required
def admin_dashboard():
    total_sarees = Saree.query.count()
    whatsapp_enquiries = WhatsappEnquiry.query.count()
    sarees = Saree.query.order_by(Saree.id.desc()).all()
    return render_template(
        "admin_dashboard.html",
        total_sarees=total_sarees,
        whatsapp_enquiries=whatsapp_enquiries,
        sarees=sarees,
    )


@app.route("/admin/sarees/add", methods=["GET", "POST"])
@admin_login_required
def add_saree():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        price = request.form.get("price", "").strip()
        description = request.form.get("description", "").strip()
        image = request.files.get("image")

        if not all([name, price, description, image]):
            flash("All fields are required.", "warning")
            return redirect(request.url)

        image_filename = save_uploaded_image(image)
        if not image_filename:
            flash("Please upload a valid image file (png, jpg, jpeg, webp, gif, svg).", "danger")
            return redirect(request.url)

        try:
            parsed_price = float(price)
        except ValueError:
            flash("Price must be a valid number.", "danger")
            return redirect(request.url)

        db.session.add(
            Saree(
                name=name,
                price=parsed_price,
                description=description,
                image_filename=image_filename,
            )
        )
        db.session.commit()
        flash("Saree added successfully.", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("add_saree.html")


@app.route("/admin/sarees/edit/<int:saree_id>", methods=["GET", "POST"])
@admin_login_required
def edit_saree(saree_id):
    saree = Saree.query.get_or_404(saree_id)

    if request.method == "POST":
        saree.name = request.form.get("name", saree.name).strip()
        saree.description = request.form.get("description", saree.description).strip()

        try:
            saree.price = float(request.form.get("price", saree.price))
        except ValueError:
            flash("Price must be a valid number.", "danger")
            return redirect(request.url)

        image = request.files.get("image")
        if image and image.filename:
            image_filename = save_uploaded_image(image)
            if not image_filename:
                flash("Please upload a valid image file (png, jpg, jpeg, webp, gif, svg).", "danger")
                return redirect(request.url)
            saree.image_filename = image_filename

        db.session.commit()
        flash("Saree updated successfully.", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("edit_saree.html", saree=saree)


@app.post("/admin/sarees/delete/<int:saree_id>")
@admin_login_required
def delete_saree(saree_id):
    saree = Saree.query.get_or_404(saree_id)
    db.session.delete(saree)
    db.session.commit()
    flash("Saree deleted successfully.", "info")
    return redirect(url_for("admin_dashboard"))


with app.app_context():
    db.create_all()
    ensure_default_admin()
    ensure_seed_sarees()


if __name__ == "__main__":
    app.run(debug=True)
