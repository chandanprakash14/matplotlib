# Elegant Drapes Boutique · Silk Saree E-Commerce (Flask)

A complete boutique storefront with:
- **Customer flow:** browse sarees, filter categories, view details, and buy via WhatsApp.
- **Admin flow:** secure login, category CRUD, saree CRUD with real image uploads, logo management, and password update.

## Project Structure

```text
silk_saree_ecommerce/
├── app.py
├── requirements.txt
├── templates/
│   ├── base.html
│   ├── home.html
│   ├── product_details.html
│   ├── about.html
│   ├── contact.html
│   ├── admin_login.html
│   ├── admin_dashboard.html
│   ├── add_saree.html
│   ├── edit_saree.html
│   ├── add_category.html
│   └── upload_logo.html
└── static/
    ├── css/style.css
    └── uploads/
        ├── sarees/
        └── logo/
```

## Setup

1. Create and activate virtualenv.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Optional env vars:
   ```bash
   export SECRET_KEY='change-this'
   export ADMIN_USERNAME='admin'
   export ADMIN_PASSWORD='admin123'
   ```
4. Run:
   ```bash
   python app.py
   ```

## A to Z Admin Panel Access

1. Open `http://127.0.0.1:5000/admin`.
2. Login with your admin credentials (from env or defaults at first run).
3. Use dashboard actions:
   - Add/Edit/Delete categories
   - Add/Edit/Delete sarees with image upload
   - Upload/replace boutique logo
4. Immediately change your password from **Change Admin Password** section in dashboard.
5. Logout from navbar when done.

## WhatsApp Buy Flow

From product detail page, **Buy Now on WhatsApp** opens:
- Number: `7539967397`
- Pre-filled message with saree Name, Category, and Price.

## Security Notes

- Password hashing via Werkzeug.
- Session-protected admin routes.
- Secure image upload handling with `secure_filename`.
- Allowed file-type validation for uploads.
