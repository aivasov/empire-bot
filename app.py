from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
import traceback
from functools import wraps

app = Flask(__name__)

# Загружаем секретный ключ из .env
app.secret_key = os.getenv('SECRET_KEY', 'fallback-secret-key')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

DATA_DIR = os.path.join(os.getcwd(), "data")
DATA_PATH = os.path.join(DATA_DIR, "questions.json")

# Создаем папку если её нет
try:
    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"Data directory: {DATA_DIR}")
    print(f"Data file: {DATA_PATH}")
except Exception as e:
    print(f"Error creating directory: {e}")

def login_required(f):
    """Декоратор для проверки авторизации"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def load_questions():
    """Загрузка данных из JSON файла"""
    try:
        if os.path.exists(DATA_PATH):
            with open(DATA_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"Loaded data: {len(data.get('blocks', []))} blocks, {len(data.get('bonus_blocks', []))} bonus blocks")
                return data
        else:
            print("Data file doesn't exist, creating empty structure")
            return {"blocks": [], "bonus_blocks": []}
    except Exception as e:
        print(f"Error loading data: {e}")
        return {"blocks": [], "bonus_blocks": []}

def save_questions(data):
    """Сохранение данных в JSON файл"""
    try:
        print(f"Attempting to save to: {DATA_PATH}")
        print(f"Data to save: {len(data.get('blocks', []))} blocks, {len(data.get('bonus_blocks', []))} bonus blocks")
                
        # Проверяем что папка существует
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR, exist_ok=True)
            print(f"Created directory: {DATA_DIR}")
                
        # Сохраняем данные
        with open(DATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
                
        print("Data saved successfully")
        return True
            
    except Exception as e:
        print(f"Error saving data: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа в админку"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('login.html', error='Неверный пароль')
    
    # Если уже авторизован, перенаправляем в админку
    if session.get('admin_logged_in'):
        return redirect(url_for('admin'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Выход из админки"""
    session.pop('admin_logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def admin():
    return render_template('admin.html')

@app.route('/api/questions', methods=['GET'])
@login_required
def get_questions():
    """API для получения всех вопросов"""
    try:
        data = load_questions()
        return jsonify(data)
    except Exception as e:
        print(f"Error in get_questions: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/questions', methods=['POST'])
@login_required
def save_questions_api():
    """API для сохранения вопросов"""
    try:
        print("Received POST request to save questions")
                
        data = request.get_json()
        if not data:
            print("No data received")
            return jsonify({"error": "Нет данных"}), 400
                
        print(f"Received data keys: {list(data.keys())}")
                
        # Валидация структуры
        if "blocks" not in data:
            data["blocks"] = []
        if "bonus_blocks" not in data:
            data["bonus_blocks"] = []
                
        if save_questions(data):
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Ошибка записи файла"}), 500
                
    except Exception as e:
        print(f"Error in save_questions_api: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask app...")
    app.run(debug=True, host='0.0.0.0', port=5000)
