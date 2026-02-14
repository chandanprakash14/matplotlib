# Silk Saree E-Commerce Website (Flask)

A complete end-to-end project with two roles:
- **Customer (End User)**: browse sarees, open details, and pay with Razorpay.
- **Admin (Shop Owner)**: login securely, manage sarees (CRUD), view analytics and orders.

## Project Structure

```
silk_saree_ecommerce/
├── app.py
├── database.db (auto-created)
├── requirements.txt
├── templates/
├── static/
│   ├── css/style.css
│   └── uploads/
```

## Step-by-step Setup

1. Create virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure environment variables (recommended):
   ```bash
   export SECRET_KEY='change-this'
   export ADMIN_USERNAME='admin'
   export ADMIN_PASSWORD='admin123'
   export RAZORPAY_KEY_ID='rzp_test_xxx'
   export RAZORPAY_KEY_SECRET='xxx'
   ```
4. Run app:
   ```bash
   python app.py
   ```
5. Open in browser:
   - Storefront: `http://127.0.0.1:5000/`
   - Admin login: `http://127.0.0.1:5000/admin/login`

## Security Highlights

- Admin password stored with `generate_password_hash`.
- Login checked via `check_password_hash`.
- Admin pages protected using session + custom `@admin_login_required` decorator.
- Image uploads sanitized with `secure_filename`.

## Razorpay Flow

1. Customer clicks **Buy Now**.
2. Frontend requests backend route `/create-razorpay-order/<saree_id>`.
3. Backend creates Razorpay order and returns order data.
4. Razorpay Checkout opens in browser.
5. On payment success, frontend sends payment details to `/payment/success`.
6. Backend verifies signature and stores order in `Order` table.

## Database Tables

- `Admin(id, username, password)`
- `Saree(id, name, price, image_filename, description)`
- `Order(id, saree_name, price, razorpay_payment_id, order_date)`

