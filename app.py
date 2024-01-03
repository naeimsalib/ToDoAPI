from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'This_Is_My_Very_Strong_Secret_Key'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
migrate = Migrate(app, db)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  # New field for admin status

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(80), nullable=False)
    due_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    priority = db.Column(db.String(10), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'))
    tag = db.relationship('Tag', backref=db.backref('tasks', lazy=True))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_completed = db.Column(db.Boolean, default=False)  # New field for completion status


    def to_dict(self):
        return {
            "id": self.id,
            "task": self.task,
            "due_date": self.due_date.isoformat(),
            "priority": self.priority,
            "tag": self.tag.name if self.tag else None,
            "is_completed": self.is_completed  # Include completion status
        }

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    is_admin = data.get('is_admin', False)  # Defaults to False if not provided

    if username is None or password is None:
        return jsonify({"message": "Missing username or password"}), 400

    if User.query.filter_by(username=username).first() is not None:
        return jsonify({"message": "Username already exists"}), 400

    user = User(username=username, is_admin=is_admin)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data.get('username')).first()

    if user is None or not user.check_password(data.get('password')):
        return jsonify({"message": "Invalid username or password"}), 401

    login_user(user)
    return jsonify({"message": "Logged in successfully"})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"})

@app.route('/tasks', methods=['POST'])
@login_required
def create_task():
    data = request.json
    task_description = data['task']
    due_date_str = data.get('due_date', datetime.utcnow().isoformat())
    priority = data.get('priority', 'Low')
    tag_id = data.get('tag_id')

    # Parse the due_date string into a datetime object
    try:
        due_date = datetime.fromisoformat(due_date_str)
    except ValueError:
        return jsonify({"message": "Invalid due date format"}), 400

    if Task.query.filter_by(task=task_description, user_id=current_user.id).first():
        return jsonify({"message": "This task is already in the list"}), 409

    new_task = Task(task=task_description, due_date=due_date, priority=priority, tag_id=tag_id, user_id=current_user.id)
    db.session.add(new_task)
    db.session.commit()
    return jsonify(new_task.to_dict()), 201

@app.route('/tasks', methods=['GET'])
@login_required
def get_all_tasks():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    if not tasks:
        return jsonify({"message": "No tasks found"}), 404
    return jsonify([task.to_dict() for task in tasks])

@app.route('/tasks/completed', methods=['GET'])
@login_required
def get_completed_tasks():
    completed_tasks = Task.query.filter_by(user_id=current_user.id, is_completed=True).all()
    return jsonify([task.to_dict() for task in completed_tasks])

@app.route('/tasks/search', methods=['GET'])
@login_required
def search_task():
    search_keyword = request.args.get('keyword', '')
    matching_tasks = Task.query.filter(Task.task.ilike(f'%{search_keyword}%'), Task.user_id == current_user.id).all()
    if matching_tasks:
        return jsonify([task.to_dict() for task in matching_tasks])
    return jsonify({"message": "No tasks found with the provided keyword"}), 404

@app.route('/tasks/<int:task_id>', methods=['GET'])
@login_required
def get_task(task_id):
    task = Task.query.get(task_id)
    if task and task.user_id == current_user.id:
        return jsonify(task.to_dict())
    return jsonify({"message": "Task not found"}), 404

@app.route('/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    task = Task.query.get(task_id)
    if task and task.user_id == current_user.id:
        data = request.json

        # Parse the due_date string into a datetime object
        due_date_str = data.get('due_date', task.due_date.isoformat())
        try:
            task.due_date = datetime.fromisoformat(due_date_str)
        except ValueError:
            return jsonify({"message": "Invalid due date format"}), 400

        task.task = data.get('task', task.task)
        task.priority = data.get('priority', task.priority)
        task.tag_id = data.get('tag_id', task.tag_id)
        
        db.session.commit()
        return jsonify(task.to_dict())
    return jsonify({"message": "Task not found"}), 404


@app.route('/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    task = Task.query.get(task_id)
    if task and task.user_id == current_user.id:
        db.session.delete(task)
        db.session.commit()
        return jsonify({"message": "Task deleted"})
    else:
        return jsonify({"message": "Task not found"}), 404


@app.route('/tasks/complete', methods=['POST'])
@login_required
def complete_task():
    data = request.json
    task_id = data.get('id')
    task_name = data.get('task')

    task = None
    if task_id:
        task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    elif task_name:
        task = Task.query.filter_by(task=task_name, user_id=current_user.id).first()

    if task:
        task.is_completed = True
        db.session.commit()
        return jsonify(task.to_dict()), 200  # Return updated task data
    else:
        return jsonify({"message": "Task not found"}), 404

@app.route('/users', methods=['GET'])
@login_required
def list_users():
    if not current_user.is_admin:
        return jsonify({"message": "Access denied"}), 403

    users = User.query.all()
    users_data = [{"id": user.id, "username": user.username, "is_admin": user.is_admin} for user in users]
    return jsonify(users_data)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
