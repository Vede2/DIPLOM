"""
Фермерский интернет-магазин "Натуральный продукт"
Единый файл для деплоя на Render.com
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

# Инициализация приложения
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация расширений
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ============ МОДЕЛИ БАЗЫ ДАННЫХ ============

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    orders = db.relationship('Order', backref='user', lazy=True)
    cart_items = db.relationship('CartItem', backref='user', lazy=True)

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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    cart_items = db.relationship('CartItem', backref='product', lazy=True)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer, default=1)

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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ============ ФУНКЦИИ ИНИЦИАЛИЗАЦИИ ДАННЫХ ============

def init_categories():
    """Инициализация категорий если их нет"""
    if Category.query.first() is None:
        categories = [
            Category(name='Овощи', description='Свежие фермерские овощи'),
            Category(name='Фрукты', description='Сезонные фрукты с фермы'),
            Category(name='Молочные продукты', description='Натуральные молочные продукты'),
            Category(name='Мясо', description='Фермерское мясо'),
            Category(name='Яйца', description='Домашние яйца'),
            Category(name='Мёд', description='Натуральный мёд'),
            Category(name='Зелень', description='Свежая зелень'),
            Category(name='Выпечка', description='Домашняя выпечка'),
            Category(name='Соленья', description='Домашние соленья и заготовки'),
            Category(name='Растительное масло', description='Нерафинированные масла'),
        ]
        for category in categories:
            db.session.add(category)
        db.session.commit()

def init_products():
    """Инициализация товаров если их нет"""
    if Product.query.first() is None:
        products = [
            # Овощи (category_id=1)
            Product(name='Картофель фермерский', description='Экологически чистый картофель выращенный без химических удобрений. Идеально подходит для жарки, варки и запекания.', 
                   price=45, stock=100, image='potato.jpg', category_id=1, is_organic=True, weight='1 кг'),
            Product(name='Морковь свежая', description='Сочная морковь с собственной грядки. Богата каротином и витаминами.', 
                   price=55, stock=80, image='carrot.jpg', category_id=1, is_organic=True, weight='1 кг'),
            Product(name='Помидоры черри', description='Сладкие помидоры черри, выращенные в теплице. Идеальны для салатов и закусок.', 
                   price=120, stock=50, image='cherry_tomatoes.jpg', category_id=1, is_organic=False, weight='500 г'),
            Product(name='Огурцы свежие', description='Хрустящие огурчики прямо с грядки. Без горечи и химикатов.', 
                   price=80, stock=60, image='cucumbers.jpg', category_id=1, is_organic=True, weight='1 кг'),
            Product(name='Тыква мускатная', description='Сладкая мускатная тыква для супов и запекания. Отличный источник витаминов.', 
                   price=90, stock=30, image='pumpkin.jpg', category_id=1, is_organic=True, weight='шт'),
            Product(name='Капуста белокочанная', description='Сочная белокочанная капуста. Идеальна для салатов и квашения.', 
                   price=40, stock=70, image='cabbage.jpg', category_id=1, is_organic=True, weight='1 кг'),
            
            # Фрукты (category_id=2)
            Product(name='Яблоки сезонные', description='Хрустящие яблоки из собственного сада. Разные сорта в зависимости от сезона.', 
                   price=70, stock=120, image='apples.jpg', category_id=2, is_organic=True, weight='1 кг'),
            Product(name='Груши садовые', description='Ароматные груши, собранные вручную. Сочные и сладкие.', 
                   price=95, stock=40, image='pears.jpg', category_id=2, is_organic=True, weight='1 кг'),
            Product(name='Вишня свежая', description='Кисло-сладкая вишня для вареников и компотов. Собрана вручную.', 
                   price=150, stock=25, image='cherry.jpg', category_id=2, is_organic=True, weight='500 г'),
            Product(name='Малина лесная', description='Ароматная лесная малина, собранная в экологически чистом районе. Настоящий деликатес.', 
                   price=200, stock=15, image='raspberries.jpg', category_id=2, is_organic=True, weight='250 г'),
            Product(name='Сливы домашние', description='Спелые сливы из собственного сада. Идеальны для варенья и компотов.', 
                   price=110, stock=35, image='plums.jpg', category_id=2, is_organic=True, weight='1 кг'),
            
            # Молочные продукты (category_id=3)
            Product(name='Молоко цельное', description='Натуральное коровье молоко от свободно пасущихся коров. Жирность 3.5-4%.', 
                   price=60, stock=50, image='milk.jpg', category_id=3, is_organic=True, weight='1 л'),
            Product(name='Творог домашний', description='Нежный домашний творог из цельного молока. Отличный источник белка и кальция.', 
                   price=120, stock=30, image='cottage_cheese.jpg', category_id=3, is_organic=True, weight='500 г'),
            Product(name='Сметана деревенская', description='Густая домашняя сметана 20% жирности. Идеальна для борща и выпечки.', 
                   price=85, stock=40, image='sour_cream.jpg', category_id=3, is_organic=True, weight='250 г'),
            Product(name='Масло сливочное', description='Натуральное сливочное масло ручного взбивания 82.5% жирности.', 
                   price=180, stock=20, image='butter.jpg', category_id=3, is_organic=True, weight='200 г'),
            Product(name='Йогурт домашний', description='Натуральный йогурт без добавок и консервантов. Живые бактерии.', 
                   price=90, stock=25, image='yogurt.jpg', category_id=3, is_organic=True, weight='300 мл'),
            
            # Мясо (category_id=4)
            Product(name='Курица фермерская', description='Курица выращенная на свободном выгуле. Нежное диетическое мясо.', 
                   price=280, stock=25, image='chicken.jpg', category_id=4, is_organic=True, weight='1.5-2 кг'),
            Product(name='Говядина фермерская', description='Мраморная говядина от бычков травяного откорма. Выдержка 21 день.', 
                   price=450, stock=15, image='beef.jpg', category_id=4, is_organic=True, weight='1 кг'),
            Product(name='Свинина домашняя', description='Свинина от поросят выращенных на натуральных кормах без антибиотиков.', 
                   price=320, stock=20, image='pork.jpg', category_id=4, is_organic=True, weight='1 кг'),
            
            # Яйца (category_id=5)
            Product(name='Яйца куриные', description='Яйца от кур несушек свободного выгула. Яркий желток, прочная скорлупа.', 
                   price=90, stock=200, image='eggs.jpg', category_id=5, is_organic=True, weight='10 шт'),
            Product(name='Яйца перепелиные', description='Диетические перепелиные яйца. Богаты витаминами и микроэлементами.', 
                   price=120, stock=150, image='quail_eggs.jpg', category_id=5, is_organic=True, weight='18 шт'),
            
            # Мёд (category_id=6)
            Product(name='Мёд цветочный', description='Натуральный цветочный мёд с собственной пасеки. Собран в экологически чистом районе.', 
                   price=250, stock=30, image='flower_honey.jpg', category_id=6, is_organic=True, weight='500 г'),
            Product(name='Мёд гречишный', description='Ароматный гречишный мёд с характерным вкусом. Богат железом.', 
                   price=280, stock=20, image='buckwheat_honey.jpg', category_id=6, is_organic=True, weight='500 г'),
            
            # Зелень (category_id=7)
            Product(name='Укроп свежий', description='Ароматный свежий укроп. Выращен без химикатов.', 
                   price=30, stock=100, image='dill.jpg', category_id=7, is_organic=True, weight='пучок'),
            Product(name='Петрушка свежая', description='Свежая зелень петрушки. Отличное дополнение к любому блюду.', 
                   price=25, stock=100, image='parsley.jpg', category_id=7, is_organic=True, weight='пучок'),
            Product(name='Зеленый лук', description='Свежий зеленый лук с грядки. Сочный и ароматный.', 
                   price=35, stock=80, image='green_onion.jpg', category_id=7, is_organic=True, weight='пучок'),
            
            # Выпечка (category_id=8)
            Product(name='Хлеб домашний', description='Хлеб на закваске из цельнозерновой муки. Без дрожжей и улучшителей.', 
                   price=60, stock=40, image='bread.jpg', category_id=8, is_organic=True, weight='буханка'),
            Product(name='Пирожки с капустой', description='Домашние пирожки из дрожжевого теста с капустной начинкой.', 
                   price=45, stock=50, image='pirozhki.jpg', category_id=8, is_organic=False, weight='шт'),
            
            # Соленья (category_id=9)
            Product(name='Огурцы соленые', description='Хрустящие соленые огурчики по бабушкиному рецепту. Без уксуса.', 
                   price=180, stock=40, image='pickles.jpg', category_id=9, is_organic=True, weight='1 л'),
            Product(name='Квашеная капуста', description='Квашеная капуста с клюквой. Натуральная ферментация.', 
                   price=130, stock=35, image='sauerkraut.jpg', category_id=9, is_organic=True, weight='1 л'),
            
            # Растительное масло (category_id=10)
            Product(name='Подсолнечное масло', description='Нерафинированное подсолнечное масло холодного отжима. Сохраняет все витамины.', 
                   price=150, stock=30, image='sunflower_oil.jpg', category_id=10, is_organic=True, weight='500 мл'),
        ]
        
        for product in products:
            db.session.add(product)
        db.session.commit()

def init_users():
    """Создание тестовых пользователей если их нет"""
    if User.query.first() is None:
        admin = User(
            username='admin',
            email='admin@farmshop.ru',
            password_hash=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin)
        
        user = User(
            username='user',
            email='user@farmshop.ru',
            password_hash=generate_password_hash('user123')
        )
        db.session.add(user)
        
        db.session.commit()

# ============ HTML ШАБЛОНЫ ============

BASE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Фермерский магазин "Натуральный продукт"{% endblock %}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f8f9fa;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }
        
        /* Навигация */
        .navbar {
            background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
            color: white;
            padding: 1rem 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
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
            font-size: 1.5rem;
            font-weight: bold;
            color: white;
            text-decoration: none;
        }
        
        .nav-links {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .nav-links a {
            color: white;
            text-decoration: none;
            transition: opacity 0.3s;
            font-weight: 500;
        }
        
        .nav-links a:hover {
            opacity: 0.8;
        }
        
        .cart-link {
            position: relative;
        }
        
        .cart-count {
            background: #ff6b6b;
            color: white;
            border-radius: 50%;
            padding: 2px 6px;
            font-size: 12px;
            position: absolute;
            top: -8px;
            right: -8px;
        }
        
        .mobile-menu-btn {
            display: none;
            background: none;
            border: none;
            color: white;
            font-size: 24px;
            cursor: pointer;
        }
        
        /* Алерты */
        .alert {
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
            animation: slideIn 0.3s ease-out;
        }
        
        @keyframes slideIn {
            from { transform: translateY(-20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        
        .alert-success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .alert-error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        /* Hero секция */
        .hero {
            background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
            color: white;
            padding: 80px 20px;
            text-align: center;
            border-radius: 10px;
            margin: 20px 0;
        }
        
        .hero h1 {
            font-size: 3rem;
            margin-bottom: 1rem;
            font-weight: 700;
        }
        
        .hero p {
            font-size: 1.2rem;
            margin-bottom: 2rem;
        }
        
        /* Кнопки */
        .btn {
            display: inline-block;
            padding: 12px 24px;
            background-color: #6c757d;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            border: none;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 16px;
        }
        
        .btn-primary {
            background-color: #FF9800;
        }
        
        .btn-primary:hover {
            background-color: #F57C00;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        
        .btn-success {
            background-color: #4CAF50;
        }
        
        .btn-success:hover {
            background-color: #45a049;
        }
        
        .btn-sm {
            padding: 8px 16px;
            font-size: 14px;
        }
        
        /* Сетка товаров */
        .products-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 30px;
            margin: 30px 0;
        }
        
        .product-card {
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
            transition: transform 0.3s, box-shadow 0.3s;
        }
        
        .product-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        }
        
        .product-card img {
            width: 100%;
            height: 250px;
            object-fit: cover;
        }
        
        .product-info {
            padding: 20px;
        }
        
        .product-info h3 {
            margin-bottom: 10px;
            color: #333;
            font-size: 1.2rem;
        }
        
        .product-description {
            color: #666;
            margin-bottom: 15px;
            font-size: 14px;
            height: 40px;
            overflow: hidden;
        }
        
        .product-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .product-price {
            font-size: 1.5rem;
            font-weight: bold;
            color: #4CAF50;
        }
        
        .product-weight {
            color: #666;
            font-size: 14px;
        }
        
        .product-badges {
            margin-bottom: 15px;
        }
        
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: 500;
        }
        
        .badge.organic {
            background-color: #4CAF50;
            color: white;
        }
        
        .product-actions {
            display: flex;
            gap: 10px;
        }
        
        /* Категории */
        .categories-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        
        .category-card {
            background: white;
            padding: 30px;
            border-radius: 10px;
            text-align: center;
            text-decoration: none;
            color: #333;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        
        .category-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        }
        
        .category-card h3 {
            color: #4CAF50;
            margin-bottom: 10px;
        }
        
        /* Преимущества */
        .advantages-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 30px;
            margin: 30px 0;
        }
        
        .advantage-card {
            text-align: center;
            padding: 30px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .advantage-card h3 {
            margin-bottom: 15px;
            color: #4CAF50;
        }
        
        /* Фильтры */
        .filters {
            display: flex;
            gap: 15px;
            margin: 20px 0;
            flex-wrap: wrap;
        }
        
        .filter-btn {
            padding: 8px 20px;
            background: white;
            border: 2px solid #4CAF50;
            color: #4CAF50;
            border-radius: 25px;
            text-decoration: none;
            transition: all 0.3s;
        }
        
        .filter-btn:hover,
        .filter-btn.active {
            background: #4CAF50;
            color: white;
        }
        
        /* Футер */
        .footer {
            background: #333;
            color: white;
            padding: 50px 0 20px;
            margin-top: 50px;
        }
        
        .footer-content {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }
        
        .footer-section h3 {
            margin-bottom: 20px;
            color: #4CAF50;
        }
        
        .footer-bottom {
            text-align: center;
            padding-top: 20px;
            border-top: 1px solid #555;
        }
        
        /* Страница товара */
        .product-detail {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 50px;
            margin: 40px 0;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .product-image-large {
            width: 100%;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .product-detail-info h1 {
            font-size: 2rem;
            margin-bottom: 20px;
            color: #333;
        }
        
        .product-detail-price {
            font-size: 2rem;
            color: #4CAF50;
            font-weight: bold;
            margin: 20px 0;
        }
        
        .quantity-control {
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 20px 0;
        }
        
        .quantity-control input {
            width: 80px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            text-align: center;
        }
        
        /* Корзина */
        .cart-items {
            margin: 30px 0;
        }
        
        .cart-item {
            display: flex;
            align-items: center;
            gap: 20px;
            padding: 20px;
            background: white;
            border-radius: 10px;
            margin-bottom: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .cart-item img {
            width: 100px;
            height: 100px;
            object-fit: cover;
            border-radius: 5px;
        }
        
        .cart-item-info {
            flex: 1;
        }
        
        .cart-total {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-top: 30px;
        }
        
        .cart-total h2 {
            margin-bottom: 20px;
            color: #333;
        }
        
        .total-price {
            font-size: 2rem;
            color: #4CAF50;
            font-weight: bold;
        }
        
        /* Формы */
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
        }
        
        .form-group input,
        .form-group textarea,
        .form-group select {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        .form-group input:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: #4CAF50;
        }
        
        .auth-form {
            max-width: 400px;
            margin: 50px auto;
            padding: 30px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .search-bar {
            margin: 20px 0;
        }
        
        .search-bar input {
            width: 300px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        
        section {
            margin: 40px 0;
        }
        
        h2 {
            margin: 30px 0 20px;
            color: #333;
            position: relative;
            padding-bottom: 10px;
        }
        
        h2:after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 50px;
            height: 3px;
            background: #4CAF50;
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
                background: #4CAF50;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            
            .nav-links.active {
                display: flex;
            }
            
            .mobile-menu-btn {
                display: block;
            }
            
            .product-detail {
                grid-template-columns: 1fr;
            }
            
            .hero h1 {
                font-size: 2rem;
            }
            
            .cart-item {
                flex-direction: column;
                text-align: center;
            }
            
            .products-grid {
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            }
        }
        
        @media (max-width: 480px) {
            .container {
                padding: 0 15px;
            }
            
            .hero {
                padding: 40px 15px;
            }
            
            .hero h1 {
                font-size: 1.8rem;
            }
            
            .products-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="container">
            <a href="/" class="logo">🌾 Натуральный продукт</a>
            <div class="nav-links" id="navLinks">
                <a href="/catalog">Каталог</a>
                <a href="/about">О нас</a>
                <a href="/cart" class="cart-link">
                     Корзина
                    {% if current_user.is_authenticated %}
                        <span class="cart-count">{{ current_user.cart_items|length }}</span>
                    {% endif %}
                </a>
                {% if current_user.is_authenticated %}
                    <a href="/orders">Заказы</a>
                    <a href="/logout">Выйти</a>
                    <span class="user-name">👤 {{ current_user.username }}</span>
                {% else %}
                    <a href="/login">Войти</a>
                    <a href="/register">Регистрация</a>
                {% endif %}
            </div>
            <button class="mobile-menu-btn" onclick="toggleMenu()">☰</button>
        </div>
    </nav>

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

    <footer class="footer">
        <div class="container">
            <div class="footer-content">
                <div class="footer-section">
                    <h3>О нас</h3>
                    <p>Мы - семейная ферма, которая выращивает натуральные продукты с любовью и заботой о вашем здоровье.</p>
                </div>
                <div class="footer-section">
                    <h3>Контакты</h3>
                    <p> +7 (999) 123-45-67</p>
                    <p> info@farmshop.ru</p>
                    <p> Красноярск, д. Фермерская</p>
                </div>
                <div class="footer-section">
                    <h3>Мы в соцсетях</h3>
                    <p>Telegram: @farmshop</p>
                    <p>WhatsApp: +79991234567</p>
                    <p>VK: vk.com/farmshop</p>
                </div>
            </div>
            <div class="footer-bottom">
                <p>&copy; 2024 Фермерский магазин "Натуральный продукт". Все права защищены.</p>
            </div>
        </div>
    </footer>

    <script>
        function toggleMenu() {
            const navLinks = document.getElementById('navLinks');
            navLinks.classList.toggle('active');
        }
        
        // Автоматическое скрытие алертов
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

INDEX_TEMPLATE = '''
{% extends "base.html" %}

{% block content %}
<div class="hero">
    <h1>Натуральные продукты с любовью</h1>
    <p>От фермы до вашего стола — свежесть, качество и традиции</p>
    <a href="/catalog" class="btn btn-primary">Перейти в каталог</a>
</div>

<section class="featured-products">
    <h2>Популярные товары</h2>
    <div class="products-grid">
        {% for product in products %}
            <div class="product-card">
                <img src="{{ url_for('static', filename='images/products/' + product.image) }}" 
                     alt="{{ product.name }}" 
                     onerror="this.src='{{ url_for('static', filename='images/products/default.jpg') }}'">
                <div class="product-info">
                    <h3>{{ product.name }}</h3>
                    <p class="product-description">{{ product.description[:100] }}...</p>
                    <div class="product-meta">
                        <span class="product-price">{{ "%.0f"|format(product.price) }} ₽</span>
                        <span class="product-weight">{{ product.weight }}</span>
                    </div>
                    <div class="product-badges">
                        {% if product.is_organic %}
                            <span class="badge organic">Органик</span>
                        {% endif %}
                    </div>
                    <div class="product-actions">
                        <a href="/product/{{ product.id }}" class="btn btn-sm">Подробнее</a>
                        <form action="/add_to_cart/{{ product.id }}" method="POST" style="display: inline;">
                            <button type="submit" class="btn btn-primary btn-sm">В корзину</button>
                        </form>
                    </div>
                </div>
            </div>
        {% endfor %}
    </div>
</section>

<section class="categories-section">
    <h2>Категории товаров</h2>
    <div class="categories-grid">
        {% for category in categories %}
            <a href="/catalog/{{ category.id }}" class="category-card">
                <h3>{{ category.name }}</h3>
                <p>{{ category.description }}</p>
            </a>
        {% endfor %}
    </div>
</section>

<section class="advantages">
    <h2>Почему выбирают нас</h2>
    <div class="advantages-grid">
        <div class="advantage-card">
            <h3> Натурально</h3>
            <p>Вся продукция выращена без химических удобрений и пестицидов</p>
        </div>
        <div class="advantage-card">
            <h3> Свежая доставка</h3>
            <p>Доставляем продукты в день сбора урожая</p>
        </div>
        <div class="advantage-card">
            <h3>‍ Семейная ферма</h3>
            <p>Трех поколений опыт выращивания качественных продуктов</p>
        </div>
        <div class="advantage-card">
            <h3> Контроль качества</h3>
            <p>Каждая партия проходит строгий контроль качества</p>
        </div>
    </div>
</section>
{% endblock %}
'''

CATALOG_TEMPLATE = '''
{% extends "base.html" %}

{% block title %}Каталог товаров{% endblock %}

{% block content %}
<h1>Каталог товаров</h1>

<div class="search-bar">
    <form action="/search" method="GET">
        <input type="text" name="q" placeholder="Поиск товаров..." value="{{ search_query or '' }}">
        <button type="submit" class="btn">🔍 Поиск</button>
    </form>
</div>

<div class="filters">
    <a href="/catalog" class="filter-btn {% if not current_category %}active{% endif %}">Все товары</a>
    {% for category in categories %}
        <a href="/catalog/{{ category.id }}" 
           class="filter-btn {% if current_category and current_category.id == category.id %}active{% endif %}">
            {{ category.name }}
        </a>
    {% endfor %}
</div>

{% if products %}
    <div class="products-grid">
        {% for product in products %}
            <div class="product-card">
                <img src="{{ url_for('static', filename='images/products/' + product.image) }}" 
                     alt="{{ product.name }}"
                     onerror="this.src='{{ url_for('static', filename='images/products/default.jpg') }}'">
                <div class="product-info">
                    <h3>{{ product.name }}</h3>
                    <p class="product-description">{{ product.description[:100] }}...</p>
                    <div class="product-meta">
                        <span class="product-price">{{ "%.0f"|format(product.price) }} ₽</span>
                        <span class="product-weight">{{ product.weight }}</span>
                    </div>
                    <div class="product-badges">
                        {% if product.is_organic %}
                            <span class="badge organic">Органик</span>
                        {% endif %}
                    </div>
                    <div class="product-actions">
                        <a href="/product/{{ product.id }}" class="btn btn-sm">Подробнее</a>
                        <form action="/add_to_cart/{{ product.id }}" method="POST" style="display: inline;">
                            <button type="submit" class="btn btn-primary btn-sm">В корзину</button>
                        </form>
                    </div>
                </div>
            </div>
        {% endfor %}
    </div>
{% else %}
    <p style="text-align: center; padding: 50px;">Товары не найдены</p>
{% endif %}
{% endblock %}
'''

PRODUCT_TEMPLATE = '''
{% extends "base.html" %}

{% block title %}{{ product.name }}{% endblock %}

{% block content %}
<div class="product-detail">
    <div>
        <img src="{{ url_for('static', filename='images/products/' + product.image) }}" 
             alt="{{ product.name }}"
             class="product-image-large"
             onerror="this.src='{{ url_for('static', filename='images/products/default.jpg') }}'">
    </div>
    <div class="product-detail-info">
        <h1>{{ product.name }}</h1>
        {% if product.is_organic %}
            <span class="badge organic">Органик</span>
        {% endif %}
        <p>{{ product.description }}</p>
        <div class="product-detail-price">{{ "%.0f"|format(product.price) }} ₽</div>
        <p><strong>Вес/Объем:</strong> {{ product.weight }}</p>
        <p><strong>В наличии:</strong> {{ product.stock }} шт.</p>
        
        <form action="/add_to_cart/{{ product.id }}" method="POST">
            <div class="quantity-control">
                <label>Количество:</label>
                <input type="number" name="quantity" value="1" min="1" max="{{ product.stock }}">
            </div>
            <button type="submit" class="btn btn-primary">Добавить в корзину</button>
        </form>
        
        <div style="margin-top: 20px;">
            <a href="/catalog/{{ product.category_id }}" class="btn">← Назад к категории</a>
        </div>
    </div>
</div>
{% endblock %}
'''

ABOUT_TEMPLATE = '''
{% extends "base.html" %}

{% block title %}О нас{% endblock %}

{% block content %}
<div class="hero" style="padding: 60px 20px;">
    <h1>О нашей ферме</h1>
    <p>История семьи, традиции и любовь к земле</p>
</div>

<div style="background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
    <h2>Наша история</h2>
    <p>Наша семейная ферма была основана в 1995 году. Три поколения нашей семьи трудятся над тем, чтобы на вашем столе были только самые свежие и натуральные продукты.</p>
    <p>Мы используем традиционные методы земледелия без применения химических удобрений и пестицидов. Все наши животные выращиваются на свободном выгуле и получают только натуральные корма.</p>
    
    <h2>Наши принципы</h2>
    <ul style="list-style: none; padding: 0;">
        <li style="margin: 10px 0;">🌱 Экологически чистое производство</li>
        <li style="margin: 10px 0;">🐄 Гуманное отношение к животным</li>
        <li style="margin: 10px 0;">🚚 Свежесть каждого продукта</li>
        <li style="margin: 10px 0;">💚 Забота о здоровье покупателей</li>
    </ul>
</div>
{% endblock %}
'''

CART_TEMPLATE = '''
{% extends "base.html" %}

{% block title %}Корзина{% endblock %}

{% block content %}
<h1>Корзина</h1>

{% if cart_items %}
    <div class="cart-items">
        {% for item in cart_items %}
            <div class="cart-item">
                {% if item.product %}
                    <img src="{{ url_for('static', filename='images/products/' + item.product.image) }}" 
                         alt="{{ item.product.name }}"
                         onerror="this.src='{{ url_for('static', filename='images/products/default.jpg') }}'">
                    <div class="cart-item-info">
                        <h3>{{ item.product.name }}</h3>
                        <p>Цена: {{ "%.0f"|format(item.product.price) }} ₽</p>
                        <p>Сумма: {{ "%.0f"|format(item.product.price * item.quantity) }} ₽</p>
                    </div>
                {% else %}
                    <div class="cart-item-info">
                        <h3>Товар не найден</h3>
                    </div>
                {% endif %}
                {% if item.product %}
                    <form action="/update_cart/{{ item.product.id }}" method="POST">
                        <input type="number" name="quantity" value="{{ item.quantity }}" min="1" class="quantity-input" data-product-id="{{ item.product.id }}">
                        <button type="submit" class="btn btn-sm">Обновить</button>
                    </form>
                    <a href="/update_cart/{{ item.product.id }}?quantity=0" class="btn btn-sm" style="background: #dc3545;">Удалить</a>
                {% endif %}
            </div>
        {% endfor %}
    </div>
    
    <div class="cart-total">
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
            <form action="/checkout" method="POST" style="margin-top: 20px;">
                <button type="submit" class="btn btn-success">Оформить заказ</button>
            </form>
        {% else %}
            <p style="margin-top: 20px;">Для оформления заказа необходимо <a href="/login">войти</a> или <a href="/register">зарегистрироваться</a></p>
        {% endif %}
    </div>
{% else %}
    <p style="text-align: center; padding: 50px;">Корзина пуста</p>
    <div style="text-align: center;">
        <a href="/catalog" class="btn btn-primary">Перейти в каталог</a>
    </div>
{% endif %}
{% endblock %}
'''

LOGIN_TEMPLATE = '''
{% extends "base.html" %}

{% block title %}Вход{% endblock %}

{% block content %}
<div class="auth-form">
    <h2>Вход в личный кабинет</h2>
    <form method="POST">
        <div class="form-group">
            <label>Имя пользователя:</label>
            <input type="text" name="username" required>
        </div>
        <div class="form-group">
            <label>Пароль:</label>
            <input type="password" name="password" required>
        </div>
        <button type="submit" class="btn btn-primary">Войти</button>
    </form>
    <p style="margin-top: 20px; text-align: center;">
        Нет аккаунта? <a href="/register">Зарегистрироваться</a>
    </p>
</div>
{% endblock %}
'''

REGISTER_TEMPLATE = '''
{% extends "base.html" %}

{% block title %}Регистрация{% endblock %}

{% block content %}
<div class="auth-form">
    <h2>Регистрация</h2>
    <form method="POST">
        <div class="form-group">
            <label>Имя пользователя:</label>
            <input type="text" name="username" required>
        </div>
        <div class="form-group">
            <label>Email:</label>
            <input type="email" name="email" required>
        </div>
        <div class="form-group">
            <label>Пароль:</label>
            <input type="password" name="password" required>
        </div>
        <button type="submit" class="btn btn-primary">Зарегистрироваться</button>
    </form>
    <p style="margin-top: 20px; text-align: center;">
        Уже есть аккаунт? <a href="/login">Войти</a>
    </p>
</div>
{% endblock %}
'''

ORDERS_TEMPLATE = '''
{% extends "base.html" %}

{% block title %}Мои заказы{% endblock %}

{% block content %}
<h1>Мои заказы</h1>

{% if orders %}
    {% for order in orders %}
        <div style="background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h3>Заказ №{{ order.id }}</h3>
            <p>Дата: {{ order.created_at.strftime('%d.%m.%Y %H:%M') }}</p>
            <p>Статус: {{ order.status }}</p>
            <p>Сумма: {{ "%.0f"|format(order.total_amount) }} ₽</p>
            <h4>Товары:</h4>
            <ul>
                {% for item in order.items %}
                    <li>{{ item.product.name }} x {{ item.quantity }} = {{ "%.0f"|format(item.price * item.quantity) }} ₽</li>
                {% endfor %}
            </ul>
        </div>
    {% endfor %}
{% else %}
    <p style="text-align: center; padding: 50px;">У вас пока нет заказов</p>
    <div style="text-align: center;">
        <a href="/catalog" class="btn btn-primary">Перейти в каталог</a>
    </div>
{% endif %}
{% endblock %}
'''

# Регистрируем шаблоны
app.jinja_env.globals['BASE_TEMPLATE'] = BASE_TEMPLATE

# ============ МАРШРУТЫ ============

@app.route('/')
def index():
    products = Product.query.order_by(Product.created_at.desc()).limit(8).all()
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

@app.route('/about')
def about():
    return render_template_string(ABOUT_TEMPLATE)

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
                    cart_items.append({
                        'product': product,
                        'quantity': item['quantity']
                    })
    return render_template_string(CART_TEMPLATE, cart_items=cart_items)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    quantity = int(request.form.get('quantity', 1))
    
    if current_user.is_authenticated:
        cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        if cart_item:
            cart_item.quantity += quantity
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
                item['quantity'] += quantity
                found = True
                break
        
        if not found:
            cart.append({'product_id': product_id, 'quantity': quantity})
        
        session['cart'] = cart
    
    flash('Товар добавлен в корзину!', 'success')
    return redirect(request.referrer or url_for('catalog'))

@app.route('/update_cart/<int:product_id>', methods=['POST', 'GET'])
def update_cart(product_id):
    if request.method == 'GET':
        quantity = int(request.args.get('quantity', 0))
    else:
        quantity = int(request.form.get('quantity', 1))
    
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
                if item['product_id'] == product_id and quantity > 0:
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
        
        if User.query.filter_by(email=email).first():
            flash('Пользователь с таким email уже существует', 'error')
            return redirect(url_for('register'))
        
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('Регистрация успешна! Теперь вы можете войти.', 'success')
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
            
            # Перенос корзины из сессии в базу данных
            if 'cart' in session:
                for item in session['cart']:
                    cart_item = CartItem.query.filter_by(
                        user_id=user.id, 
                        product_id=item['product_id']
                    ).first()
                    
                    if cart_item:
                        cart_item.quantity += item['quantity']
                    else:
                        cart_item = CartItem(
                            user_id=user.id,
                            product_id=item['product_id'],
                            quantity=item['quantity']
                        )
                        db.session.add(cart_item)
                
                db.session.commit()
                session.pop('cart')
            
            flash('Вы успешно вошли!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'success')
    return redirect(url_for('index'))

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if query:
        products = Product.query.filter(
            Product.name.contains(query) | Product.description.contains(query)
        ).all()
    else:
        products = []
    
    categories = Category.query.all()
    return render_template_string(CATALOG_TEMPLATE, products=products, categories=categories, search_query=query)

# Вспомогательная функция для рендеринга шаблонов из строк
def render_template_string(template_string, **context):
    from flask import render_template_string as flask_render_template_string
    import re
    
    # Если шаблон расширяет базовый
    if '{% extends "base.html" %}' in template_string:
        # Удаляем extends
        template_string = template_string.replace('{% extends "base.html" %}', '')
        
        # Извлекаем содержимое блоков
        blocks = {}
        block_pattern = r'{% block (\w+) %}(.*?){% endblock %}'
        matches = re.findall(block_pattern, template_string, re.DOTALL)
        
        for block_name, block_content in matches:
            blocks[block_name] = block_content.strip()
        
        # Берем базовый шаблон и заменяем в нем блоки
        result_template = BASE_TEMPLATE
        
        # Заменяем каждый блок в базовом шаблоне
        for block_name, block_content in blocks.items():
            # Ищем блок в базовом шаблоне и заменяем его
            base_block_pattern = r'{% block ' + block_name + r' %}(.*?){% endblock %}'
            result_template = re.sub(base_block_pattern, block_content, result_template, flags=re.DOTALL)
        
        return flask_render_template_string(result_template, **context)
    else:
        # Если нет расширения, просто рендерим как есть
        return flask_render_template_string(template_string, **context)

# Создание необходимых директорий
def create_directories():
    directories = ['static', 'static/images', 'static/images/products']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    # Создаем default изображение если его нет
    default_image_path = 'static/images/products/default.jpg'
    if not os.path.exists(default_image_path):
        # Создаем простое SVG изображение как заглушку
        with open(default_image_path.replace('.jpg', '.svg'), 'w') as f:
            f.write('''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400">
                <rect width="400" height="400" fill="#f0f0f0"/>
                <text x="200" y="200" text-anchor="middle" fill="#999" font-size="20">Нет изображения</text>
            </svg>''')

# Инициализация приложения
def init_app():
    with app.app_context():
        # Создаем таблицы если их нет
        db.create_all()
        
        # Создаем директории
        create_directories()
        
        # Инициализируем данные если БД пустая
        init_categories()
        init_products()
        init_users()

# Запуск приложения
if __name__ == '__main__':
    init_app()
    app.run(debug=True, host='127.0.0.1', port=8080)
else:
    # Для production (gunicorn)
    init_app()
