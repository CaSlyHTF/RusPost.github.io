from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'd2730abce64ea65a58474cf00ade4a4e'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rus_post.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'  # Папка для загрузки медиа
db = SQLAlchemy(app)


# Модель пользователя
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    avatar = db.Column(db.String(200), nullable=True)  # Поле для аватара
    description = db.Column(db.String(280), nullable=True)  # Описание пользователя
    posts = db.relationship('Post', backref='user', lazy='dynamic')
    comments = db.relationship('Comment', backref='user', lazy='dynamic')


# Модель поста
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    media_file = db.Column(db.String(200), nullable=True)  # Для медиа
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship('Comment', backref='post', lazy='dynamic')


# Модель комментария
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


@app.before_request
def create_tables():
    db.create_all()  # Создает таблицы, если их нет


@app.route('/')
def index():
    return redirect(url_for('home'))


@app.route('/home')
def home():
    posts = Post.query.all()
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    return render_template('home.html', posts=posts, user=user)


@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Если пользователь не авторизован, отправить на страницу логина

    if request.method == 'POST':
        content = request.form.get('content')
        media_file = request.files.get('media')

        post = Post(content=content, user_id=session['user_id'])

        if media_file:
            filename = media_file.filename
            media_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            post.media_file = filename

        db.session.add(post)
        db.session.commit()
        flash('Пост успешно создан!')
        return redirect(url_for('home'))

    user = User.query.get(session['user_id'])  # Получаем информацию о пользователе
    return render_template('create_post.html', user=user)  # Передаем пользователя в шаблон


@app.route('/search_posts/<query>')
def search_posts(query):
    posts = Post.query.filter(Post.content.like(f'%{query}%')).all()
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    return render_template('search_results.html', posts=posts, user=user)


@app.route('/search_user/<username>')
def search_user(username):
    user = User.query.filter_by(username=username).first()
    return render_template('user_profile.html', user=user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id  # Сохраняем ID пользователя в сессии
            flash('Вы успешно вошли в аккаунт.')
            return redirect(url_for('home'))  # Переход на главную страницу после успеха
        else:
            flash('Неверные учетные данные!')
    return render_template('login.html')



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует.')
        else:
            new_user = User(username=username, password_hash=generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()
            flash('Пользователь успешно зарегистрирован.')
            return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Вы вышли из аккаунта.')
    return redirect(url_for('home'))


@app.route('/add_comment/', methods=['POST'])
def add_comment():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    content = request.form.get('content')
    post_id = request.form.get('post_id')

    if content and post_id:
        comment = Comment(content=content, post_id=post_id, user_id=session['user_id'])
        db.session.add(comment)
        db.session.commit()
        flash("Комментарий успешно добавлен.")

    return redirect(url_for('home'))


@app.route('/comments/<int:post_id>')
def get_comments(post_id):
    comments = Comment.query.filter_by(post_id=post_id).all()
    comments_data = [{"content": comment.content, "username": comment.user.username} for comment in comments]
    return jsonify(comments_data)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return os.path.join(app.config['UPLOAD_FOLDER'], filename)


@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)


@app.route('/subscriptions')
def subscriptions():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    return render_template('subscriptions.html', user=user)


@app.route('/settings', methods=['GET', 'POST'])
def account_settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        user.username = request.form.get('username')
        user.description = request.form.get('description')
        avatar_file = request.files.get('avatar')

        if avatar_file:
            filename = avatar_file.filename
            avatar_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            user.avatar = filename

        db.session.commit()
        flash('Настройки успешно обновлены.')

    return render_template('settings.html', user=user)


if __name__ == '__main__':
    app.run(debug=True)
