import os
from functools import wraps
from urllib.parse import quote

from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
WHATSAPP_NUMBER = "7539967397"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "replace-me-in-production")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'database.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

db = SQLAlchemy(app)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    sarees = db.relationship(
        "Saree",
        backref="category",
        cascade="all, delete-orphan",
        lazy=True,
    )


class Saree(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(255), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)


def admin_login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "admin_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("admin_login"))
        return view_func(*args, **kwargs)

    return wrapper


def create_default_admin() -> None:
    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD", "admin123")

    if not Admin.query.filter_by(username=username).first():
        default_admin = Admin(username=username, password=generate_password_hash(password))
        db.session.add(default_admin)
        db.session.commit()


def seed_default_categories() -> None:
    if Category.query.count() > 0:
        return

    default_names = [
        "Kanchipuram Silk – Pure Zari",
        "Soft Silks",
        "Mysore Silk",
        "Paithani",
        "Bridal Collection",
    ]

    db.session.add_all([Category(name=name) for name in default_names])
    db.session.commit()


def build_whatsapp_link(saree: Saree) -> str:
    message = (
        "Hi, I want to buy this saree from Elegant Drapes Boutique:\n"
        f"Name: {saree.name}\n"
        f"Category: {saree.category.name}\n"
        f"Price: ₹{saree.price:,.0f}"
    )
    return f"https://wa.me/{WHATSAPP_NUMBER}?text={quote(message)}"


@app.route("/")
def home():
    category_id = request.args.get("category", type=int)
    categories = Category.query.order_by(Category.name).all()

    saree_query = Saree.query.order_by(Saree.id.desc())
    if category_id:
        saree_query = saree_query.filter_by(category_id=category_id)

    sarees = saree_query.all()
    selected_category = category_id
    return render_template(
        "home.html",
        sarees=sarees,
        categories=categories,
        selected_category=selected_category,
    )


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/saree/<int:saree_id>")
def product_details(saree_id):
    saree = Saree.query.get_or_404(saree_id)
    whatsapp_link = build_whatsapp_link(saree)
    return render_template("product_details.html", saree=saree, whatsapp_link=whatsapp_link)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password, password):
            session["admin_id"] = admin.id
            session["admin_username"] = admin.username
            flash("Welcome back, admin.", "success")
            return redirect(url_for("admin_dashboard"))

        flash("Invalid credentials.", "danger")

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
    total_categories = Category.query.count()
    sarees = Saree.query.order_by(Saree.id.desc()).all()
    categories = Category.query.order_by(Category.name).all()
    return render_template(
        "admin_dashboard.html",
        total_sarees=total_sarees,
        total_categories=total_categories,
        sarees=sarees,
        categories=categories,
    )


@app.route("/admin/categories/add", methods=["GET", "POST"])
@admin_login_required
def add_category():
    if request.method == "POST":
        name = request.form.get("name", "").strip()

        if not name:
            flash("Category name is required.", "warning")
            return redirect(request.url)

        if Category.query.filter_by(name=name).first():
            flash("Category already exists.", "danger")
            return redirect(request.url)

        db.session.add(Category(name=name))
        db.session.commit()
        flash("Category added successfully.", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("add_category.html")


@app.post("/admin/categories/edit/<int:category_id>")
@admin_login_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    new_name = request.form.get("name", "").strip()

    if not new_name:
        flash("Category name cannot be empty.", "warning")
        return redirect(url_for("admin_dashboard"))

    existing = Category.query.filter(Category.name == new_name, Category.id != category.id).first()
    if existing:
        flash("Another category with this name already exists.", "danger")
        return redirect(url_for("admin_dashboard"))

    category.name = new_name
    db.session.commit()
    flash("Category updated.", "success")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/categories/delete/<int:category_id>")
@admin_login_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)

    if category.sarees:
        flash("Cannot delete a category assigned to sarees.", "danger")
        return redirect(url_for("admin_dashboard"))

    db.session.delete(category)
    db.session.commit()
    flash("Category deleted.", "info")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/sarees/add", methods=["GET", "POST"])
@admin_login_required
def add_saree():
    categories = Category.query.order_by(Category.name).all()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        price_raw = request.form.get("price", "").strip()
        description = request.form.get("description", "").strip()
        category_id = request.form.get("category_id", type=int)
        image_filename = secure_filename(request.form.get("image_filename", "").strip())

        if not all([name, price_raw, description, category_id, image_filename]):
            flash("All fields are required.", "warning")
            return redirect(request.url)

        category = Category.query.get(category_id)
        if not category:
            flash("Please choose a valid category.", "danger")
            return redirect(request.url)

        try:
            price = float(price_raw)
            if price <= 0:
                raise ValueError
        except ValueError:
            flash("Price must be a positive number.", "danger")
            return redirect(request.url)

        db.session.add(
            Saree(
                name=name,
                price=price,
                description=description,
                image_filename=image_filename,
                category_id=category_id,
            )
        )
        db.session.commit()
        flash("Saree added successfully.", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("add_saree.html", categories=categories)


@app.route("/admin/sarees/edit/<int:saree_id>", methods=["GET", "POST"])
@admin_login_required
def edit_saree(saree_id):
    saree = Saree.query.get_or_404(saree_id)
    categories = Category.query.order_by(Category.name).all()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        price_raw = request.form.get("price", "").strip()
        category_id = request.form.get("category_id", type=int)
        image_filename = secure_filename(request.form.get("image_filename", "").strip())

        if not all([name, description, price_raw, category_id, image_filename]):
            flash("All fields are required.", "warning")
            return redirect(request.url)

        category = Category.query.get(category_id)
        if not category:
            flash("Please choose a valid category.", "danger")
            return redirect(request.url)

        try:
            price = float(price_raw)
            if price <= 0:
                raise ValueError
        except ValueError:
            flash("Price must be a positive number.", "danger")
            return redirect(request.url)

        saree.name = name
        saree.description = description
        saree.price = price
        saree.category_id = category_id
        saree.image_filename = image_filename

        db.session.commit()
        flash("Saree updated successfully.", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("edit_saree.html", saree=saree, categories=categories)


@app.post("/admin/sarees/delete/<int:saree_id>")
@admin_login_required
def delete_saree(saree_id):
    saree = Saree.query.get_or_404(saree_id)
    db.session.delete(saree)
    db.session.commit()
    flash("Saree deleted.", "info")
    return redirect(url_for("admin_dashboard"))


with app.app_context():
    db.create_all()
    create_default_admin()
    seed_default_categories()


if __name__ == "__main__":
    app.run(debug=True)
