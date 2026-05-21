"""
Фермерский интернет-магазин "Натуральный продукт"
Обновленный дизайн - зеленый + оранжевый
"""
import os
import sys
import re

try:
    from flask import Flask, render_template_string, request, redirect, url_for, flash, session
    from flask_sqlalchemy import SQLAlchemy
    from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
    from werkzeug.security import generate_password_hash, check_password_hash
    from datetime import datetime
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "flask-sqlalchemy", "flask-login", "werkzeug"])
    print("Пакеты установлены! Перезапустите скрипт.")
    sys.exit(1)

# Инициализация приложения
app = Flask(__name__)
app.config['SECRET_KEY'] = 'farm-shop-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация базы данных
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Создаем папки для изображений
os.makedirs('static/images/products', exist_ok=True)
os.makedirs('static/images/icons', exist_ok=True)

# ============ МОДЕЛИ ============

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    cart_items = db.relationship('CartItem', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    products = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    image = db.Column(db.String(200), default='default.jpg')
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    is_organic = db.Column(db.Boolean, default=False)
    weight = db.Column(db.String(20))

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer, default=1)
    product = db.relationship('Product', backref='cart_items')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    total_amount = db.Column(db.Float)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)
    product = db.relationship('Product')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ============ БАЗОВЫЙ HTML ШАБЛОН ============

BASE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Натуральный продукт</title>
    <link href="https://fonts.googleapis.com/css2?family=Rubik:wght@300;400;500;600;700&family=Comfortaa:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        html, body {
            height: 100%;
        }
        
        body {
            font-family: 'Rubik', sans-serif;
            line-height: 1.5;
            color: #000;
            background-color: #faf8f5;
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }
        
        h1, h2, h3, h4 {
            font-family: 'Comfortaa', cursive;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }
        
        .main-content-wrapper {
            flex: 1;
        }
        
        /* Навигация */
        .navbar {
            background: #2d5a27;
            padding: 0.8rem 0;
            position: sticky;
            top: 0;
            z-index: 1000;
        }
        
        .navbar .container {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            font-family: 'Comfortaa', cursive;
            font-size: 1.4rem;
            font-weight: 700;
            color: #ff8f00;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .logo img {
            width: 32px;
            height: 32px;
            object-fit: contain;
        }
        
        .nav-links {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .nav-links a {
            color: white;
            text-decoration: none;
            font-size: 24px;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            width: 44px;
            height: 44px;
            border-radius: 10px;
        }
        
        .nav-links a:hover {
            color: #ff8f00;
            background: rgba(255, 255, 255, 0.1);
            transform: scale(1.1);
        }
        
        .nav-links a img {
            width: 28px;
            height: 28px;
            object-fit: contain;
        }
        
        .mobile-menu-btn {
            display: none;
            background: none;
            border: none;
            color: white;
            font-size: 28px;
            cursor: pointer;
        }
        
        /* Hero секция */
        .hero {
            background: linear-gradient(135deg, #2d5a27 0%, #4a7c3f 100%);
            padding: 60px 20px;
            margin: 0 0 30px 0;
            border-radius: 0 0 30px 30px;
            display: flex;
            align-items: center;
            gap: 40px;
        }
        
        .hero-text {
            flex: 1;
        }
        
        .hero-text h1 {
            font-size: 2.5rem;
            margin-bottom: 1rem;
            color: #ff8f00;
            font-weight: 700;
        }
        
        .hero-text p {
            font-size: 1.1rem;
            margin-bottom: 2rem;
            color: #c8e6c9;
        }
        
        .hero-image {
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .hero-image img {
            max-width: 100%;
            height: auto;
            border-radius: 20px;
            max-height: 350px;
            object-fit: cover;
        }
        
        /* Кнопки */
        .btn {
            display: inline-block;
            padding: 12px 24px;
            border-radius: 25px;
            border: none;
            cursor: pointer;
            transition: all 0.3s;
            font-family: 'Rubik', sans-serif;
            font-weight: 500;
            text-decoration: none;
            font-size: 16px;
        }
        
        .btn-primary {
            background: #ff8f00;
            color: white;
        }
        
        .btn-primary:hover {
            background: #f57c00;
            transform: translateY(-1px);
        }
        
        .btn-green {
            background: #2d5a27;
            color: white;
        }
        
        .btn-green:hover {
            background: #1b3d17;
        }
        
        .btn-sm {
            padding: 8px 16px;
            font-size: 14px;
        }
        
        .btn-outline {
            background: transparent;
            border: 2px solid #000;
            color: #000;
        }
        
        .btn-outline:hover {
            background: #000;
            color: white;
        }
        
        /* Сетка товаров */
        .products-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
            gap: 25px;
            margin: 25px 0;
        }
        
        .product-card {
            background: white;
            border-radius: 20px;
            overflow: hidden;
            transition: transform 0.3s;
            display: flex;
            flex-direction: column;
        }
        
        .product-card:hover {
            transform: translateY(-3px);
        }
        
        .product-card img {
            width: 100%;
            height: 200px;
            object-fit: cover;
        }
        
        .product-info {
            padding: 20px;
            display: flex;
            flex-direction: column;
            flex: 1;
        }
        
        .product-info h3 {
            margin-bottom: 8px;
            color: #000;
            font-size: 1.1rem;
        }
        
        .product-description {
            color: #333;
            margin-bottom: 12px;
            font-size: 13px;
            height: 36px;
            overflow: hidden;
            font-family: 'Rubik', sans-serif;
        }
        
        .product-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .product-price {
            font-size: 1.4rem;
            font-weight: 700;
            color: #ff8f00;
            font-family: 'Rubik', sans-serif;
        }
        
        .product-weight {
            color: #333;
            font-size: 13px;
        }
        
        .product-badges {
            margin-bottom: 12px;
        }
        
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 11px;
            font-weight: 600;
        }
        
        .badge.organic {
            background: #c8e6c9;
            color: #2d5a27;
        }
        
        .product-actions {
            display: flex;
            gap: 10px;
            margin-top: auto;
            padding-top: 10px;
        }
        
        /* Фильтры слева */
        .catalog-layout {
            display: flex;
            gap: 30px;
            margin: 30px 0;
        }
        
        .sidebar {
            width: 220px;
            flex-shrink: 0;
        }
        
        .sidebar h3 {
            color: #000;
            margin-bottom: 15px;
            font-size: 1.1rem;
        }
        
        .filter-list {
            list-style: none;
        }
        
        .filter-list li {
            margin-bottom: 8px;
        }
        
        .filter-btn {
            display: block;
            padding: 10px 15px;
            color: #000;
            text-decoration: none;
            border-radius: 20px;
            transition: all 0.3s;
            font-size: 14px;
            border: 1px solid transparent;
        }
        
        .filter-btn:hover {
            background: white;
            border-color: #2d5a27;
        }
        
        .filter-btn.active {
            background: #2d5a27;
            color: white;
        }
        
        .main-content {
            flex: 1;
        }
        
        /* Поиск */
        .search-bar {
            margin-bottom: 20px;
        }
        
        .search-bar input {
            width: 100%;
            padding: 12px 20px;
            border: 2px solid #c8e6c9;
            border-radius: 25px;
            font-size: 14px;
            background: white;
            font-family: 'Rubik', sans-serif;
        }
        
        .search-bar input:focus {
            outline: none;
            border-color: #2d5a27;
        }
        
        /* Корзина */
        .cart-page {
            display: flex;
            gap: 30px;
            align-items: flex-start;
        }
        
        .cart-items {
            flex: 1;
        }
        
        .cart-item {
            display: flex;
            align-items: center;
            gap: 20px;
            padding: 15px 20px;
            background: white;
            border-radius: 15px;
            margin-bottom: 12px;
        }
        
        .cart-item img {
            width: 80px;
            height: 80px;
            object-fit: cover;
            border-radius: 10px;
        }
        
        .cart-item-info {
            flex: 1;
        }
        
        .cart-item-info h3 {
            color: #000;
            font-size: 1rem;
            margin-bottom: 5px;
        }
        
        .cart-summary {
            width: 300px;
            background: white;
            padding: 25px;
            border-radius: 20px;
            position: sticky;
            top: 80px;
        }
        
        .cart-summary h2 {
            color: #000;
            margin-bottom: 20px;
            font-size: 1.3rem;
        }
        
        .total-price {
            font-size: 2rem;
            font-weight: 700;
            color: #ff8f00;
            margin-bottom: 20px;
            font-family: 'Rubik', sans-serif;
        }
        
        .quantity-input {
            width: 70px;
            padding: 8px;
            border: 2px solid #c8e6c9;
            border-radius: 15px;
            text-align: center;
            font-family: 'Rubik', sans-serif;
        }
        
        /* Заказы */
        .orders-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin: 30px 0;
        }
        
        .order-card {
            background: white;
            padding: 25px;
            border-radius: 20px;
            aspect-ratio: 1;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        
        .order-card h3 {
            color: #000;
            font-size: 1.1rem;
            margin-bottom: 10px;
        }
        
        .order-date {
            color: #333;
            font-size: 13px;
            margin-bottom: 8px;
        }
        
        .order-status {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 15px;
            font-size: 13px;
            font-weight: 600;
            margin: 8px 0;
        }
        
        .status-pending {
            background: #fff3e0;
            color: #e65100;
        }
        
        .status-processing {
            background: #e3f2fd;
            color: #1565c0;
        }
        
        .status-delivered {
            background: #c8e6c9;
            color: #2d5a27;
        }
        
        .status-cancelled {
            background: #ffcdd2;
            color: #c62828;
        }
        
        .order-total {
            font-size: 1.4rem;
            font-weight: 700;
            color: #ff8f00;
            margin: 8px 0;
        }
        
        .order-items {
            font-size: 12px;
            color: #333;
            line-height: 1.6;
        }
        
        .order-id {
            color: #333;
            font-size: 13px;
        }
        
        /* Формы */
        .auth-form {
            max-width: 400px;
            margin: 50px auto;
            padding: 30px;
            background: white;
            border-radius: 20px;
        }
        
        .auth-form h2 {
            color: #000;
            margin-bottom: 25px;
            text-align: center;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #000;
            font-weight: 500;
        }
        
        .form-group input {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #c8e6c9;
            border-radius: 20px;
            font-size: 15px;
            font-family: 'Rubik', sans-serif;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #2d5a27;
        }
        
        /* Уведомления */
        .alert {
            padding: 15px 20px;
            margin: 15px 0;
            border-radius: 15px;
            font-size: 14px;
        }
        
        .alert-success {
            background: #c8e6c9;
            color: #2d5a27;
        }
        
        .alert-error {
            background: #ffccbc;
            color: #bf360c;
        }
        
        /* Заголовки секций */
        .section-title {
            color: #000 !important;
            font-size: 1.8rem;
            margin-bottom: 25px;
        }
        
        /* Футер */
        .footer {
            background: #2d5a27;
            padding: 40px 0 20px;
            margin-top: auto;
            color: #c8e6c9;
        }
        
        .footer-content {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }
        
        .footer-section h3 {
            color: #ff8f00;
            margin-bottom: 15px;
            font-size: 1rem;
        }
        
        .footer-bottom {
            text-align: center;
            padding-top: 20px;
            border-top: 1px solid #4a7c3f;
            font-size: 13px;
        }
        
        /* Текст на страницах */
        .page-text {
            color: #000;
        }
        
        .page-text-light {
            color: #333;
        }
        
        /* Мобильная адаптация */
        @media (max-width: 768px) {
            .nav-links {
                display: none;
                flex-direction: column;
                position: absolute;
                top: 60px;
                left: 0;
                right: 0;
                background: #2d5a27;
                padding: 20px;
            }
            
            .nav-links.active {
                display: flex;
            }
            
            .mobile-menu-btn {
                display: block;
            }
            
            .hero {
                flex-direction: column;
            }
            
            .hero-image {
                order: -1;
            }
            
            .catalog-layout {
                flex-direction: column;
            }
            
            .sidebar {
                width: 100%;
            }
            
            .cart-page {
                flex-direction: column;
            }
            
            .cart-summary {
                width: 100%;
                position: static;
            }
            
            .orders-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        
        @media (max-width: 480px) {
            .orders-grid {
                grid-template-columns: 1fr;
            }
            
            .products-grid {
                grid-template-columns: 1fr;
            }
            
            .hero-text h1 {
                font-size: 1.8rem;
            }
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="container">
            <a href="/" class="logo">
                <img src="{{ url_for('static', filename='images/icons/logo.png') }}" alt="Logo" onerror="this.style.display='none'">
                Фермерский
            </a>
            <div class="nav-links" id="navLinks">
                <a href="/catalog">
                    <img src="{{ url_for('static', filename='images/icons/catalog.png') }}" alt="Каталог" onerror="this.outerHTML='📦'">
                </a>
                <a href="/cart" class="cart-link">
                    <img src="{{ url_for('static', filename='images/icons/cart.png') }}" alt="Корзина" onerror="this.outerHTML='🛒'">
                </a>
                {% if current_user.is_authenticated %}
                    <a href="/orders">
                        <img src="{{ url_for('static', filename='images/icons/orders.png') }}" alt="Заказы" onerror="this.outerHTML='📋'">
                    </a>
                    <a href="/logout">
                        <img src="{{ url_for('static', filename='images/icons/logout.png') }}" alt="Выйти" onerror="this.outerHTML='🚪'">
                    </a>
                {% else %}
                    <a href="/login">
                        <img src="{{ url_for('static', filename='images/icons/login.png') }}" alt="Войти" onerror="this.outerHTML='🔑'">
                    </a>
                {% endif %}
            </div>
            <button class="mobile-menu-btn" onclick="toggleMenu()">☰</button>
        </div>
    </nav>

    <div class="main-content-wrapper">
        <div class="container">
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}

            {% block content %}{% endblock %}
        </div>
    </div>

    <footer class="footer">
        <div class="container">
            <div class="footer-content">
                <div class="footer-section">
                    <h3>Контакты</h3>
                    <p>📞 +7 (999) 123-45-67</p>
                    <p>📧 info@farmshop.ru</p>
                </div>
                <div class="footer-section">
                    <h3>Мы в соцсетях</h3>
                    <p>Telegram: @farmshop</p>
                    <p>WhatsApp: +79991234567</p>
                </div>
            </div>
            <div class="footer-bottom">
                <p>&copy; 2024 Фермерский магазин "Натуральный продукт"</p>
            </div>
        </div>
    </footer>

    <script>
        function toggleMenu() {
            const navLinks = document.getElementById('navLinks');
            navLinks.classList.toggle('active');
        }
        
        setTimeout(() => {
            const alerts = document.querySelectorAll('.alert');
            alerts.forEach(alert => {
                alert.style.transition = 'opacity 0.5s';
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 500);
            });
        }, 3000);
    </script>
</body>
</html>
'''

# ============ ШАБЛОНЫ СТРАНИЦ ============

INDEX_TEMPLATE = '''
{% extends "base.html" %}
{% block content %}
<div class="hero">
    <div class="hero-text">
        <h1>Свежие продукты с фермы</h1>
        <p>Натуральные продукты прямо к вашему столу</p>
        <a href="/catalog" class="btn btn-primary">Смотреть каталог</a>
    </div>
    <div class="hero-image">
        <img src="{{ url_for('static', filename='images/hero.png') }}" alt="Фермерские продукты" onerror="this.parentElement.innerHTML='<div style=\\'width: 100%; height: 300px; background: rgba(255,255,255,0.2); border-radius: 20px; display: flex; align-items: center; justify-content: center; font-size: 80px;\\'>🧺</div>'">
    </div>
</div>

<div style="margin: 40px 0;">
    <h2 class="section-title">Популярные товары</h2>
    <div class="products-grid">
        {% for product in products %}
            <div class="product-card">
                <img src="{{ url_for('static', filename='images/products/' + product.image) }}" 
                     alt="{{ product.name }}"
                     onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                <div style="height: 200px; background: #e8e4df; display: none; align-items: center; justify-content: center; font-size: 64px;">
                    🧺
                </div>
                <div class="product-info">
                    <h3>{{ product.name }}</h3>
                    <p class="product-description">{{ product.description[:80] }}...</p>
                    <div class="product-meta">
                        <span class="product-price">{{ "%.0f"|format(product.price) }} ₽</span>
                        <span class="product-weight">{{ product.weight }}</span>
                    </div>
                    <div class="product-badges">
                        {% if product.is_organic %}
                            <span class="badge organic">органик</span>
                        {% endif %}
                    </div>
                    <div class="product-actions">
                        <a href="/product/{{ product.id }}" class="btn btn-outline btn-sm">Подробнее</a>
                        <a href="/add_to_cart/{{ product.id }}" class="btn btn-primary btn-sm">В корзину</a>
                    </div>
                </div>
            </div>
        {% endfor %}
    </div>
</div>
{% endblock %}
'''

CATALOG_TEMPLATE = '''
{% extends "base.html" %}
{% block content %}
<h1 class="section-title" style="margin: 25px 0;">Каталог товаров</h1>

<div class="search-bar">
    <input type="text" id="searchInput" placeholder="🔍 Поиск товаров..." value="{{ search_query or '' }}" onkeyup="searchProducts()">
</div>

<div class="catalog-layout">
    <div class="sidebar">
        <h3>Категории</h3>
        <ul class="filter-list">
            <li><a href="/catalog" class="filter-btn {% if not current_category %}active{% endif %}">Все товары</a></li>
            {% for category in categories %}
                <li><a href="/catalog/{{ category.id }}" class="filter-btn {% if current_category and current_category.id == category.id %}active{% endif %}">{{ category.name }}</a></li>
            {% endfor %}
        </ul>
    </div>
    
    <div class="main-content">
        {% if products %}
            <div class="products-grid" id="productsGrid">
                {% for product in products %}
                    <div class="product-card" data-name="{{ product.name.lower() }}">
                        <img src="{{ url_for('static', filename='images/products/' + product.image) }}" 
                             alt="{{ product.name }}"
                             onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                        <div style="height: 200px; background: #e8e4df; display: none; align-items: center; justify-content: center; font-size: 64px;">
                            🧺
                        </div>
                        <div class="product-info">
                            <h3>{{ product.name }}</h3>
                            <p class="product-description">{{ product.description[:80] }}...</p>
                            <div class="product-meta">
                                <span class="product-price">{{ "%.0f"|format(product.price) }} ₽</span>
                                <span class="product-weight">{{ product.weight }}</span>
                            </div>
                            <div class="product-badges">
                                {% if product.is_organic %}
                                    <span class="badge organic">органик</span>
                                {% endif %}
                            </div>
                            <div class="product-actions">
                                <a href="/product/{{ product.id }}" class="btn btn-outline btn-sm">Подробнее</a>
                                <a href="/add_to_cart/{{ product.id }}" class="btn btn-primary btn-sm">В корзину</a>
                            </div>
                        </div>
                    </div>
                {% endfor %}
            </div>
        {% else %}
            <p class="page-text" style="text-align: center; padding: 50px;">Товары не найдены</p>
        {% endif %}
    </div>
</div>

<script>
function searchProducts() {
    const query = document.getElementById('searchInput').value.toLowerCase();
    const products = document.querySelectorAll('.product-card');
    products.forEach(product => {
        const name = product.getAttribute('data-name');
        if (name.includes(query)) {
            product.style.display = '';
        } else {
            product.style.display = 'none';
        }
    });
}
</script>
{% endblock %}
'''

PRODUCT_TEMPLATE = '''
{% extends "base.html" %}
{% block content %}
<div style="display: flex; gap: 30px; margin: 30px 0; background: white; padding: 30px; border-radius: 20px; flex-wrap: wrap;">
    <div style="flex: 1; min-width: 300px;">
        <img src="{{ url_for('static', filename='images/products/' + product.image) }}" 
             alt="{{ product.name }}"
             style="width: 100%; height: 400px; object-fit: cover; border-radius: 15px;"
             onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
        <div style="width: 100%; height: 400px; background: #e8e4df; display: none; align-items: center; justify-content: center; font-size: 100px; border-radius: 15px;">
            🧺
        </div>
    </div>
    <div style="flex: 1; min-width: 300px;" class="page-text">
        <h1 style="color: #000; font-size: 1.8rem;">{{ product.name }}</h1>
        {% if product.is_organic %}
            <span class="badge organic" style="margin: 10px 0; display: inline-block;">органик</span>
        {% endif %}
        <p style="margin: 15px 0; color: #333; font-family: 'Rubik', sans-serif;">{{ product.description }}</p>
        <p style="font-size: 2rem; font-weight: 700; color: #ff8f00; margin: 20px 0;">{{ "%.0f"|format(product.price) }} ₽</p>
        <p style="color: #000;"><strong>Вес/Объем:</strong> {{ product.weight }}</p>
        <p style="color: #000;"><strong>В наличии:</strong> {{ product.stock }} шт.</p>
        
        <form action="/add_to_cart/{{ product.id }}" method="GET" style="margin-top: 20px;">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
                <label style="color: #000;">Количество:</label>
                <input type="number" name="quantity" value="1" min="1" max="10" class="quantity-input">
            </div>
            <button type="submit" class="btn btn-primary">Добавить в корзину</button>
        </form>
        
        <a href="/catalog/{{ product.category_id }}" class="btn btn-outline" style="margin-top: 10px;">← Назад</a>
    </div>
</div>
{% endblock %}
'''

CART_TEMPLATE = '''
{% extends "base.html" %}
{% block content %}
<h1 class="section-title" style="margin: 25px 0;">Корзина</h1>

{% if cart_items %}
    <div class="cart-page">
        <div class="cart-items">
            {% for item in cart_items %}
                <div class="cart-item">
                    {% if item.product %}
                        <img src="{{ url_for('static', filename='images/products/' + item.product.image) }}" 
                             alt="{{ item.product.name }}"
                             onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                        <div style="width: 80px; height: 80px; background: #e8e4df; display: none; align-items: center; justify-content: center; font-size: 40px; border-radius: 10px;">
                            🧺
                        </div>
                        <div class="cart-item-info">
                            <h3>{{ item.product.name }}</h3>
                            <p style="color: #333;">Цена: {{ "%.0f"|format(item.product.price) }} ₽</p>
                            <p style="color: #333;">Сумма: {{ "%.0f"|format(item.product.price * item.quantity) }} ₽</p>
                        </div>
                        <form action="/update_cart/{{ item.product.id }}" method="GET" style="display: flex; align-items: center; gap: 10px;">
                            <input type="number" name="quantity" value="{{ item.quantity }}" min="1" max="10" class="quantity-input">
                            <button type="submit" class="btn btn-green btn-sm">Обновить</button>
                        </form>
                        <a href="/update_cart/{{ item.product.id }}?quantity=0" class="btn btn-sm" style="background: #ff8f00; color: white;">Удалить</a>
                    {% endif %}
                </div>
            {% endfor %}
        </div>
        
        <div class="cart-summary">
            <h2>Итого:</h2>
            <div class="total-price">
                {% set total = namespace(value=0) %}
                {% for item in cart_items %}
                    {% if item.product %}
                        {% set total.value = total.value + (item.product.price * item.quantity) %}
                    {% endif %}
                {% endfor %}
                {{ "%.0f"|format(total.value) }} ₽
            </div>
            
            {% if current_user.is_authenticated %}
                <form action="/checkout" method="POST">
                    <button type="submit" class="btn btn-primary" style="width: 100%;">Оформить заказ</button>
                </form>
            {% else %}
                <p style="color: #333; margin: 15px 0; font-size: 14px;">Для оформления заказа необходимо <a href="/login" style="color: #ff8f00;">войти</a></p>
            {% endif %}
        </div>
    </div>
{% else %}
    <p class="page-text" style="text-align: center; padding: 50px;">Корзина пуста</p>
    <div style="text-align: center;">
        <a href="/catalog" class="btn btn-primary">Перейти в каталог</a>
    </div>
{% endif %}
{% endblock %}
'''

LOGIN_TEMPLATE = '''
{% extends "base.html" %}
{% block content %}
<div class="auth-form">
    <h2>Вход</h2>
    <form method="POST">
        <div class="form-group">
            <label>Имя пользователя</label>
            <input type="text" name="username" required>
        </div>
        <div class="form-group">
            <label>Пароль</label>
            <input type="password" name="password" required>
        </div>
        <button type="submit" class="btn btn-primary" style="width: 100%;">Войти</button>
    </form>
    <p style="margin-top: 20px; text-align: center; color: #333;">
        Нет аккаунта? <a href="/register" style="color: #ff8f00;">Зарегистрироваться</a>
    </p>
</div>
{% endblock %}
'''

REGISTER_TEMPLATE = '''
{% extends "base.html" %}
{% block content %}
<div class="auth-form">
    <h2>Регистрация</h2>
    <form method="POST">
        <div class="form-group">
            <label>Имя пользователя</label>
            <input type="text" name="username" required>
        </div>
        <div class="form-group">
            <label>Email</label>
            <input type="email" name="email" required>
        </div>
        <div class="form-group">
            <label>Пароль</label>
            <input type="password" name="password" required>
        </div>
        <button type="submit" class="btn btn-primary" style="width: 100%;">Зарегистрироваться</button>
    </form>
    <p style="margin-top: 20px; text-align: center; color: #333;">
        Уже есть аккаунт? <a href="/login" style="color: #ff8f00;">Войти</a>
    </p>
</div>
{% endblock %}
'''

ORDERS_TEMPLATE = '''
{% extends "base.html" %}
{% block content %}
<h1 class="section-title" style="margin: 25px 0;">Мои заказы</h1>

{% if orders %}
    <div class="orders-grid">
        {% for order in orders %}
            <div class="order-card">
                <div>
                    <h3>Заказ №{{ order.id }}</h3>
                    <p class="order-date">{{ order.created_at.strftime('%d.%m.%Y') }}</p>
                    <p class="order-id">ID: {{ order.id }}</p>
                </div>
                <div>
                    {% if order.status == 'pending' %}
                        <span class="order-status status-pending">В обработке</span>
                    {% elif order.status == 'processing' %}
                        <span class="order-status status-processing">Готовится</span>
                    {% elif order.status == 'delivered' %}
                        <span class="order-status status-delivered">Доставлен</span>
                    {% elif order.status == 'cancelled' %}
                        <span class="order-status status-cancelled">Отменен</span>
                    {% else %}
                        <span class="order-status status-pending">{{ order.status }}</span>
                    {% endif %}
                </div>
                <div class="order-total">{{ "%.0f"|format(order.total_amount) }} ₽</div>
                <div class="order-items">
                    {% for item in order.items %}
                        • {{ item.product.name }} ×{{ item.quantity }}<br>
                    {% endfor %}
                </div>
            </div>
        {% endfor %}
    </div>
{% else %}
    <p class="page-text" style="text-align: center; padding: 50px;">У вас пока нет заказов</p>
{% endif %}
{% endblock %}
'''

# ============ ФУНКЦИИ ============

def render_template_string(template_string, **context):
    if '{% extends "base.html" %}' in template_string:
        template_string = template_string.replace('{% extends "base.html" %}', '')
        
        # Удаляем блок title если есть
        template_string = re.sub(r'{% block title %}.*?{% endblock %}', '', template_string, flags=re.DOTALL)
        
        # Вставляем содержимое в базовый шаблон
        result = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', template_string)
        
        return render_template_string(result, **context)
    else:
        from flask import render_template_string as flask_render_template_string
        return flask_render_template_string(template_string, **context)

# ============ МАРШРУТЫ ============

@app.route('/')
def index():
    products = Product.query.limit(8).all()
    categories = Category.query.all()
    return render_template_string(INDEX_TEMPLATE, products=products, categories=categories)

@app.route('/catalog')
@app.route('/catalog/<int:category_id>')
def catalog(category_id=None):
    categories = Category.query.all()
    if category_id:
        products = Product.query.filter_by(category_id=category_id).all()
        current_category = Category.query.get(category_id)
    else:
        products = Product.query.all()
        current_category = None
    return render_template_string(CATALOG_TEMPLATE, products=products, categories=categories, current_category=current_category)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template_string(PRODUCT_TEMPLATE, product=product)

@app.route('/cart')
def cart():
    cart_items = []
    if current_user.is_authenticated:
        cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    else:
        if 'cart' in session:
            for item in session['cart']:
                product = Product.query.get(item['product_id'])
                if product:
                    cart_items.append({'product': product, 'quantity': item['quantity']})
    return render_template_string(CART_TEMPLATE, cart_items=cart_items)

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    quantity = int(request.args.get('quantity', 1))
    
    if quantity > 10:
        quantity = 10
        flash('Максимальное количество - 10 штук', 'error')
    
    if current_user.is_authenticated:
        cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        if cart_item:
            cart_item.quantity = min(cart_item.quantity + quantity, 10)
        else:
            cart_item = CartItem(user_id=current_user.id, product_id=product_id, quantity=quantity)
            db.session.add(cart_item)
        db.session.commit()
    else:
        if 'cart' not in session:
            session['cart'] = []
        
        cart = session['cart']
        found = False
        for item in cart:
            if item['product_id'] == product_id:
                item['quantity'] = min(item['quantity'] + quantity, 10)
                found = True
                break
        
        if not found:
            cart.append({'product_id': product_id, 'quantity': quantity})
        
        session['cart'] = cart
    
    flash('Товар добавлен в корзину!', 'success')
    return redirect(url_for('catalog'))

@app.route('/update_cart/<int:product_id>')
def update_cart(product_id):
    quantity = int(request.args.get('quantity', 1))
    
    if quantity > 10:
        quantity = 10
    
    if current_user.is_authenticated:
        cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        if cart_item:
            if quantity > 0:
                cart_item.quantity = quantity
            else:
                db.session.delete(cart_item)
            db.session.commit()
    else:
        if 'cart' in session:
            cart = session['cart']
            cart = [item for item in cart if not (item['product_id'] == product_id and quantity == 0)]
            for item in cart:
                if item['product_id'] == product_id:
                    item['quantity'] = quantity
            session['cart'] = cart
    
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Корзина пуста!', 'error')
        return redirect(url_for('cart'))
    
    total = sum(item.product.price * item.quantity for item in cart_items)
    order = Order(user_id=current_user.id, total_amount=total)
    db.session.add(order)
    
    for cart_item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            price=cart_item.product.price
        )
        db.session.add(order_item)
        db.session.delete(cart_item)
    
    db.session.commit()
    flash('Заказ успешно оформлен!', 'success')
    return redirect(url_for('orders'))

@app.route('/orders')
@login_required
def orders():
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template_string(ORDERS_TEMPLATE, orders=user_orders)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует', 'error')
            return redirect(url_for('register'))
        
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('Регистрация успешна!', 'success')
        return redirect(url_for('login'))
    
    return render_template_string(REGISTER_TEMPLATE)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            
            if 'cart' in session:
                for item in session['cart']:
                    cart_item = CartItem.query.filter_by(user_id=user.id, product_id=item['product_id']).first()
                    if cart_item:
                        cart_item.quantity = min(cart_item.quantity + item['quantity'], 10)
                    else:
                        cart_item = CartItem(user_id=user.id, product_id=item['product_id'], quantity=item['quantity'])
                        db.session.add(cart_item)
                db.session.commit()
                session.pop('cart')
            
            flash('Вы успешно вошли!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# ============ ИНИЦИАЛИЗАЦИЯ ДАННЫХ ============

def init_data():
    with app.app_context():
        db.create_all()
        
        if Category.query.first() is None:
            categories = [
                Category(name='Овощи', description='Свежие овощи'),
                Category(name='Фрукты', description='Сезонные фрукты'),
                Category(name='Молочные продукты', description='Натуральное молоко'),
                Category(name='Мясо', description='Фермерское мясо'),
                Category(name='Яйца', description='Домашние яйца'),
                Category(name='Мёд', description='Натуральный мёд'),
                Category(name='Зелень', description='Свежая зелень'),
                Category(name='Выпечка', description='Домашняя выпечка'),
                Category(name='Соленья', description='Домашние заготовки'),
                Category(name='Масло', description='Нерафинированные масла'),
            ]
            for cat in categories:
                db.session.add(cat)
            db.session.commit()
        
        if Product.query.first() is None:
            products = [
                Product(name='Картофель', description='Экологически чистый картофель выращенный без химических удобрений', price=45, stock=100, category_id=1, is_organic=True, weight='1 кг', image='potato.jpg'),
                Product(name='Морковь', description='Сочная морковь с собственной грядки', price=55, stock=80, category_id=1, is_organic=True, weight='1 кг', image='carrot.jpg'),
                Product(name='Помидоры черри', description='Сладкие помидоры черри, выращенные в теплице', price=120, stock=50, category_id=1, is_organic=False, weight='500 г', image='cherry_tomatoes.jpg'),
                Product(name='Огурцы', description='Хрустящие огурчики прямо с грядки', price=80, stock=60, category_id=1, is_organic=True, weight='1 кг', image='cucumbers.jpg'),
                Product(name='Тыква', description='Сладкая мускатная тыква для супов и запекания', price=90, stock=30, category_id=1, is_organic=True, weight='шт', image='pumpkin.jpg'),
                Product(name='Капуста', description='Сочная белокочанная капуста', price=40, stock=70, category_id=1, is_organic=True, weight='1 кг', image='cabbage.jpg'),
                Product(name='Яблоки', description='Хрустящие яблоки из собственного сада', price=70, stock=120, category_id=2, is_organic=True, weight='1 кг', image='apples.jpg'),
                Product(name='Груши', description='Ароматные груши, собранные вручную', price=95, stock=40, category_id=2, is_organic=True, weight='1 кг', image='pears.jpg'),
                Product(name='Вишня', description='Кисло-сладкая вишня для вареников и компотов', price=150, stock=25, category_id=2, is_organic=True, weight='500 г', image='cherry.jpg'),
                Product(name='Малина', description='Ароматная лесная малина', price=200, stock=15, category_id=2, is_organic=True, weight='250 г', image='raspberries.jpg'),
                Product(name='Сливы', description='Спелые сливы из собственного сада', price=110, stock=35, category_id=2, is_organic=True, weight='1 кг', image='plums.jpg'),
                Product(name='Молоко', description='Натуральное коровье молоко от свободно пасущихся коров', price=60, stock=50, category_id=3, is_organic=True, weight='1 л', image='milk.jpg'),
                Product(name='Творог', description='Нежный домашний творог из цельного молока', price=120, stock=30, category_id=3, is_organic=True, weight='500 г', image='cottage_cheese.jpg'),
                Product(name='Сметана', description='Густая домашняя сметана', price=85, stock=40, category_id=3, is_organic=True, weight='250 г', image='sour_cream.jpg'),
                Product(name='Масло сливочное', description='Натуральное сливочное масло ручного взбивания', price=180, stock=20, category_id=3, is_organic=True, weight='200 г', image='butter.jpg'),
                Product(name='Курица', description='Курица выращенная на свободном выгуле', price=280, stock=25, category_id=4, is_organic=True, weight='шт', image='chicken.jpg'),
                Product(name='Говядина', description='Мраморная говядина от бычков травяного откорма', price=450, stock=15, category_id=4, is_organic=True, weight='1 кг', image='beef.jpg'),
                Product(name='Свинина', description='Свинина от поросят выращенных на натуральных кормах', price=320, stock=20, category_id=4, is_organic=True, weight='1 кг', image='pork.jpg'),
                Product(name='Яйца куриные', description='Яйца от кур несушек свободного выгула', price=90, stock=200, category_id=5, is_organic=True, weight='10 шт', image='eggs.jpg'),
                Product(name='Яйца перепелиные', description='Диетические перепелиные яйца', price=120, stock=150, category_id=5, is_organic=True, weight='18 шт', image='quail_eggs.jpg'),
                Product(name='Мёд цветочный', description='Натуральный цветочный мёд с собственной пасеки', price=250, stock=30, category_id=6, is_organic=True, weight='500 г', image='flower_honey.jpg'),
                Product(name='Мёд гречишный', description='Ароматный гречишный мёд', price=280, stock=20, category_id=6, is_organic=True, weight='500 г', image='buckwheat_honey.jpg'),
                Product(name='Укроп', description='Ароматный свежий укроп', price=30, stock=100, category_id=7, is_organic=True, weight='пучок', image='dill.jpg'),
                Product(name='Петрушка', description='Свежая зелень петрушки', price=25, stock=100, category_id=7, is_organic=True, weight='пучок', image='parsley.jpg'),
                Product(name='Зеленый лук', description='Свежий зеленый лук с грядки', price=35, stock=80, category_id=7, is_organic=True, weight='пучок', image='green_onion.jpg'),
                Product(name='Хлеб домашний', description='Хлеб на закваске из цельнозерновой муки', price=60, stock=40, category_id=8, is_organic=True, weight='буханка', image='bread.jpg'),
                Product(name='Пирожки с капустой', description='Домашние пирожки из дрожжевого теста', price=45, stock=50, category_id=8, is_organic=False, weight='шт', image='pirozhki.jpg'),
                Product(name='Огурцы соленые', description='Хрустящие соленые огурчики по бабушкиному рецепту', price=180, stock=40, category_id=9, is_organic=True, weight='1 л', image='pickles.jpg'),
                Product(name='Квашеная капуста', description='Квашеная капуста с клюквой', price=130, stock=35, category_id=9, is_organic=True, weight='1 л', image='sauerkraut.jpg'),
                Product(name='Подсолнечное масло', description='Нерафинированное подсолнечное масло холодного отжима', price=150, stock=30, category_id=10, is_organic=True, weight='500 мл', image='sunflower_oil.jpg'),
            ]
            for product in products:
                db.session.add(product)
            db.session.commit()
        
        if User.query.first() is None:
            admin = User(username='admin', email='admin@farm.ru', password_hash=generate_password_hash('admin123'))
            user = User(username='user', email='user@farm.ru', password_hash=generate_password_hash('user123'))
            db.session.add(admin)
            db.session.add(user)
            db.session.commit()

# ============ ЗАПУСК ============

if __name__ == '__main__':
    init_data()
    print("=" * 50)
    print("🌾 Фермерский магазин запущен!")
    print("Откройте: http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=True, host='127.0.0.1', port=5000)
