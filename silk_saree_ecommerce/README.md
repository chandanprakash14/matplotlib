# Elegant Drapes Boutique · Silk Saree E-Commerce (Flask)

A complete end-to-end boutique storefront with two roles:
- **Customer**: browse, filter by category, view details, and buy through WhatsApp.
- **Admin**: secure login, dashboard stats, category CRUD, and saree CRUD.

## Project Structure

```
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
│   └── add_category.html
└── static/
    ├── css/style.css
    └── uploads/   # keep empty, add image files manually
```

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Optional environment variables:
   ```bash
   export SECRET_KEY='change-this'
   export ADMIN_USERNAME='admin'
   export ADMIN_PASSWORD='admin123'
   ```
4. Run the app:
   ```bash
   python app.py
   ```
5. Open:
   - Storefront: `http://127.0.0.1:5000/`
   - Admin: `http://127.0.0.1:5000/admin/login`

## WhatsApp Buy Flow

The **Buy Now on WhatsApp** button opens:

- Number: `7539967397`
- Pre-filled message with:
  - Saree Name
  - Category
  - Price

## Database Models

- `Admin(id, username, password)`
- `Category(id, name)`
- `Saree(id, name, price, description, image_filename, category_id)`

## Security

- Password hashing with Werkzeug.
- Session-protected admin routes.
- Filename sanitization using `secure_filename` for image filename input.
