import os
from datetime import datetime
from functools import wraps

import razorpay
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-change-this-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'database.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class Saree(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_filename = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    saree_name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Float, nullable=False)
    razorpay_payment_id = db.Column(db.String(120), unique=True, nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)


def init_default_admin() -> None:
    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD", "admin123")

    admin = Admin.query.filter_by(username=username).first()
    if not admin:
        admin = Admin(username=username, password=generate_password_hash(password))
        db.session.add(admin)
        db.session.commit()




def seed_demo_sarees() -> None:
    if Saree.query.count() > 0:
        return

    demo_items = [
        Saree(
            name="Kanchipuram Royal Maroon",
            price=8999.0,
            image_filename="demo_maroon.svg",
            description="Pure zari Kanchipuram silk saree with rich pallu and traditional motifs.",
        ),
        Saree(
            name="Banarasi Emerald Weave",
            price=7499.0,
            image_filename="demo_emerald.svg",
            description="Handwoven Banarasi silk saree in emerald green with intricate golden work.",
        ),
    ]
    db.session.add_all(demo_items)
    db.session.commit()

def admin_login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("admin_id"):
            flash("Please login to continue.", "warning")
            return redirect(url_for("admin_login"))
        return view_func(*args, **kwargs)

    return wrapper


def get_razorpay_client():
    key_id = os.getenv("RAZORPAY_KEY_ID", "")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET", "")
    if not key_id or not key_secret:
        return None
    return razorpay.Client(auth=(key_id, key_secret))


@app.route("/")
def home():
    sarees = Saree.query.order_by(Saree.id.desc()).all()
    return render_template("home.html", sarees=sarees)


@app.route("/saree/<int:saree_id>")
def saree_details(saree_id):
    saree = Saree.query.get_or_404(saree_id)
    return render_template("saree_details.html", saree=saree, razorpay_key=os.getenv("RAZORPAY_KEY_ID", ""))


@app.post("/create-razorpay-order/<int:saree_id>")
def create_razorpay_order(saree_id):
    saree = Saree.query.get_or_404(saree_id)
    client = get_razorpay_client()
    if not client:
        return jsonify({"error": "Razorpay keys are not configured on server."}), 500

    order_payload = {
        "amount": int(saree.price * 100),
        "currency": "INR",
        "payment_capture": "1",
        "notes": {"saree_id": str(saree.id), "saree_name": saree.name},
    }
    razorpay_order = client.order.create(order_payload)
    return jsonify(
        {
            "order_id": razorpay_order["id"],
            "amount": order_payload["amount"],
            "name": saree.name,
            "price": saree.price,
            "key": os.getenv("RAZORPAY_KEY_ID", ""),
        }
    )


@app.post("/payment/success")
def payment_success():
    payload = request.get_json(silent=True) or request.form

    razorpay_order_id = payload.get("razorpay_order_id")
    razorpay_payment_id = payload.get("razorpay_payment_id")
    razorpay_signature = payload.get("razorpay_signature")
    saree_name = payload.get("saree_name")
    price = payload.get("price")

    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature, saree_name, price]):
        return jsonify({"status": "error", "message": "Invalid payment data."}), 400

    client = get_razorpay_client()
    if not client:
        return jsonify({"status": "error", "message": "Razorpay is not configured."}), 500

    try:
        client.utility.verify_payment_signature(
            {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            }
        )

        existing_payment = Order.query.filter_by(razorpay_payment_id=razorpay_payment_id).first()
        if existing_payment:
            return jsonify({"status": "ok", "message": "Payment already recorded."})

        order = Order(
            saree_name=saree_name,
            price=float(price),
            razorpay_payment_id=razorpay_payment_id,
        )
        db.session.add(order)
        db.session.commit()
        return jsonify({"status": "ok", "message": "Payment verified and order placed."})

    except razorpay.errors.SignatureVerificationError:
        return jsonify({"status": "error", "message": "Payment signature verification failed."}), 400


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password, password):
            session["admin_id"] = admin.id
            session["admin_username"] = admin.username
            flash("Welcome back!", "success")
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
    total_orders = Order.query.count()
    total_revenue = db.session.query(db.func.sum(Order.price)).scalar() or 0
    recent_orders = Order.query.order_by(Order.order_date.desc()).limit(5).all()

    return render_template(
        "admin_dashboard.html",
        total_sarees=total_sarees,
        total_orders=total_orders,
        total_revenue=total_revenue,
        recent_orders=recent_orders,
    )


@app.route("/admin/sarees")
@admin_login_required
def manage_sarees():
    sarees = Saree.query.order_by(Saree.id.desc()).all()
    return render_template("manage_sarees.html", sarees=sarees)


def save_uploaded_image(file_storage):
    filename = secure_filename(file_storage.filename)
    if not filename:
        return ""

    unique_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}_{filename}"
    path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
    file_storage.save(path)
    return unique_name


@app.route("/admin/sarees/add", methods=["GET", "POST"])
@admin_login_required
def add_saree():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        price = request.form.get("price", "").strip()
        description = request.form.get("description", "").strip()
        image = request.files.get("image")

        if not name or not price or not description or not image:
            flash("Please fill all fields and upload an image.", "warning")
            return redirect(request.url)

        image_filename = save_uploaded_image(image)
        saree = Saree(name=name, price=float(price), description=description, image_filename=image_filename)
        db.session.add(saree)
        db.session.commit()
        flash("Saree added successfully.", "success")
        return redirect(url_for("manage_sarees"))

    return render_template("saree_form.html", page_title="Add Saree", saree=None)


@app.route("/admin/sarees/edit/<int:saree_id>", methods=["GET", "POST"])
@admin_login_required
def edit_saree(saree_id):
    saree = Saree.query.get_or_404(saree_id)

    if request.method == "POST":
        saree.name = request.form.get("name", saree.name).strip()
        saree.price = float(request.form.get("price", saree.price))
        saree.description = request.form.get("description", saree.description).strip()

        image = request.files.get("image")
        if image and image.filename:
            saree.image_filename = save_uploaded_image(image)

        db.session.commit()
        flash("Saree updated successfully.", "success")
        return redirect(url_for("manage_sarees"))

    return render_template("saree_form.html", page_title="Edit Saree", saree=saree)


@app.post("/admin/sarees/delete/<int:saree_id>")
@admin_login_required
def delete_saree(saree_id):
    saree = Saree.query.get_or_404(saree_id)
    db.session.delete(saree)
    db.session.commit()
    flash("Saree deleted.", "info")
    return redirect(url_for("manage_sarees"))


@app.route("/admin/orders")
@admin_login_required
def admin_orders():
    orders = Order.query.order_by(Order.order_date.desc()).all()
    return render_template("admin_orders.html", orders=orders)


with app.app_context():
    db.create_all()
    init_default_admin()
    seed_demo_sarees()


if __name__ == "__main__":
    app.run(debug=True)
