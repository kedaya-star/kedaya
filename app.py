import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    return app

app = create_app()

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    banned = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(200))
    word_count = db.Column(db.String(50))
    education = db.Column(db.String(50))
    category = db.Column(db.String(50))
    remark = db.Column(db.Text)
    attachment = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text)
    image = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_first_request
def create_tables():
    db.create_all()
    if not User.query.filter_by(username='3059073936').first():
        admin = User(username='3059073936', is_admin=True)
        admin.set_password('@@521314')
        db.session.add(admin)
        db.session.commit()

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return redirect(url_for('register'))
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('注册成功, 请登录')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            flash('无效的账号或密码')
            return redirect(url_for('login'))
        if user.banned and not user.is_admin:
            return render_template('banned.html')
        login_user(user)
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        agents = User.query.filter_by(is_admin=False).all()
        return render_template('admin_dashboard.html', agents=agents)
    orders = Order.query.filter_by(user_id=current_user.id).all()
    return render_template('agent_dashboard.html', orders=orders)

@app.route('/order/new', methods=['GET', 'POST'])
@login_required
def new_order():
    if request.method == 'POST':
        title = request.form['title']
        word_count = request.form['word_count']
        education = request.form['education']
        category = request.form['category']
        remark = request.form['remark']
        file = request.files.get('attachment')
        filename = None
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        order = Order(user_id=current_user.id, title=title, word_count=word_count,
                      education=education, category=category, remark=remark,
                      attachment=filename)
        db.session.add(order)
        db.session.commit()
        flash('订单已创建')
        return redirect(url_for('dashboard'))
    return render_template('order_form.html')

@app.route('/messages/<int:agent_id>', methods=['GET', 'POST'])
@login_required
def messages(agent_id):
    if not current_user.is_admin and current_user.id != agent_id:
        return 'Unauthorized', 403
    agent = User.query.get_or_404(agent_id)
    if request.method == 'POST':
        content = request.form['content']
        file = request.files.get('image')
        filename = None
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        msg = Message(sender_id=current_user.id, receiver_id=agent.id if current_user.is_admin else 1,
                      content=content, image=filename)
        db.session.add(msg)
        db.session.commit()
    convo = Message.query.filter(
        ((Message.sender_id==current_user.id) & (Message.receiver_id==agent.id)) |
        ((Message.sender_id==agent.id) & (Message.receiver_id==current_user.id))
    ).order_by(Message.timestamp.asc()).all()
    return render_template('messages.html', agent=agent, messages=convo)

@app.route('/admin/ban/<int:user_id>')
@login_required
def ban_user(user_id):
    if not current_user.is_admin:
        return 'Unauthorized', 403
    user = User.query.get_or_404(user_id)
    user.banned = True
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
