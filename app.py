# -*- coding: utf-8 -*-
import os
import sys
import sqlite3
import uuid
from datetime import timedelta, datetime
from flask import Flask, request, redirect, url_for, send_file, session, render_template_string, jsonify
from functools import wraps
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ===== КОДИРОВКА =====
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
        sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)
    except:
        pass

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or 'temp_key_123'
app.permanent_session_lifetime = timedelta(minutes=10)

USERNAME_MIN_LENGTH = 6
PASSWORD_MIN_LENGTH = 6
PASSWORD_REQUIRE_UPPERCASE = True

def is_valid_username(username):
    return len(username) >= USERNAME_MIN_LENGTH

def is_valid_password(password):
    if len(password) < PASSWORD_MIN_LENGTH:
        return False
    if PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
        return False
    return True

def is_valid_email(email):
    return '@' in email and '.' in email

STYLES = '''
<style>
    :root {
        --primary: #8fceb0;
        --primary-dark: #6bb894;
        --secondary: #e0f0e9;
        --success: #74c69d;
        --danger: #f7a8a8;
        --danger-dark: #ee8b8b;
        --bg-gradient: linear-gradient(135deg, #d8f3e4 0%, #b8e3cf 100%);
    }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        background: var(--bg-gradient);
        min-height: 100vh;
        padding: 20px;
        position: relative;
        overflow-x: hidden;
        font-size: 16px;
        line-height: 1.5;
        color: #333;
        transition: background 0.3s ease;
    }
    .bubble { position: fixed; border-radius: 50%; background: radial-gradient(circle at 30% 30%, rgba(255,255,255,0.85), rgba(255,255,255,0.15)); box-shadow: inset 0 0 10px rgba(255,255,255,0.8), 0 0 20px rgba(255,255,255,0.4); opacity: 0.55; animation: floatBubble linear infinite; pointer-events: none; z-index: -1; }
    @keyframes floatBubble {
        0% { transform: translateY(100vh) scale(0.4); opacity: 0; }
        10% { opacity: 0.7; }
        90% { opacity: 0.5; }
        100% { transform: translateY(-20vh) scale(1.1); opacity: 0; }
    }
    .bubble:nth-child(1) { width: 80px; height: 80px; left: 5%; animation-duration: 16s; animation-delay: 0s; }
    .bubble:nth-child(2) { width: 120px; height: 120px; left: 20%; animation-duration: 22s; animation-delay: 3s; }
    .bubble:nth-child(3) { width: 60px; height: 60px; left: 35%; animation-duration: 12s; animation-delay: 6s; }
    .bubble:nth-child(4) { width: 150px; height: 150px; left: 50%; animation-duration: 27s; animation-delay: 1s; }
    .bubble:nth-child(5) { width: 90px; height: 90px; left: 65%; animation-duration: 18s; animation-delay: 4s; }
    .bubble:nth-child(6) { width: 110px; height: 110px; left: 80%; animation-duration: 24s; animation-delay: 7s; }
    .bubble:nth-child(7) { width: 70px; height: 70px; left: 90%; animation-duration: 14s; animation-delay: 2s; }
    .bubble:nth-child(8) { width: 100px; height: 100px; left: 45%; animation-duration: 17s; animation-delay: 5s; }
    .container {
        max-width: 1200px; margin: 0 auto; background: rgba(255,255,255,0.95); backdrop-filter: blur(8px);
        border-radius: 12px; padding: 25px 30px; box-shadow: 0 10px 25px rgba(0,0,0,0.08);
        position: relative; z-index: 1; animation: fadeIn 0.4s ease-out;
    }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    .header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 15px; border-bottom: 1px solid rgba(143,206,176,0.5); margin-bottom: 20px; position: relative; }
    .header h1 { color: #2d5a48; font-size: 1.8em; font-weight: 600; }
    .header .user-info { display: flex; align-items: center; gap: 15px; }
    .role-badge { background: var(--primary); color: white; padding: 6px 16px; border-radius: 20px; font-size: 0.9em; font-weight: 500; }
    .avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        overflow: hidden;
        border: 2px solid var(--primary);
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: var(--primary);
        color: white;
        font-weight: bold;
        font-size: 1.2em;
        position: relative;
    }
    .avatar img {
        width: 100%;
        height: 100%;
        object-fit: contain;
        display: block;
        position: absolute;
        top: 50%;
        left: 50%;
        transform-origin: center center;
    }
    .settings-gear { position: relative; cursor: pointer; font-size: 1.5em; background: none; border: none; color: #4a7a6b; transition: transform 0.3s ease; }
    .settings-gear:hover { transform: rotate(90deg); }
    .settings-menu { display: none; position: absolute; right: 0; top: 40px; background: white; border-radius: 8px; box-shadow: 0 8px 20px rgba(0,0,0,0.12); min-width: 180px; z-index: 1000; padding: 8px 0; animation: slideDown 0.2s ease-out; border: 1px solid #eee; }
    .settings-menu.show { display: block; }
    @keyframes slideDown { from { opacity: 0; transform: translateY(-5px); } to { opacity: 1; transform: translateY(0); } }
    .settings-menu a { display: block; padding: 10px 20px; color: #333; text-decoration: none; transition: background 0.2s; }
    .settings-menu a:hover { background: #f5faf8; }
    .btn { display: inline-block; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: 500; transition: all 0.2s; border: none; cursor: pointer; font-size: 0.95em; box-shadow: 0 2px 6px rgba(0,0,0,0.05); color: white; }
    .btn-primary { background: var(--primary); color: white; }
    .btn-primary:hover { background: var(--primary-dark); transform: translateY(-2px); box-shadow: 0 6px 16px rgba(143,206,176,0.4); }
    .btn-secondary { background: var(--secondary); color: #2d5a48; }
    .btn-secondary:hover { background: #cde5db; }
    .btn-success { background: var(--success); color: white; }
    .btn-danger { background: var(--danger); color: white; }
    .btn-danger:hover { background: var(--danger-dark); }
    .btn-sm { padding: 6px 12px; font-size: 0.85em; }
    .form-box { max-width: 500px; margin: 0 auto; }
    .form-group { margin-bottom: 20px; position: relative; }
    .form-group label { display: block; margin-bottom: 5px; font-weight: 500; color: #2d5a48; }
    .form-group input[type="text"], .form-group input[type="password"], .form-group input[type="file"], .form-group input[type="email"] {
        width: 100%; padding: 12px 15px; border: 1px solid #cde5db; border-radius: 8px; font-size: 1em; transition: border-color 0.2s, box-shadow 0.2s; background: #fafffd;
    }
    .form-group input:focus { outline: none; border-color: var(--primary); box-shadow: 0 0 0 3px rgba(143,206,176,0.25); }
    .toggle-password { position: absolute; right: 12px; top: 38px; cursor: pointer; user-select: none; font-size: 1.2em; color: #777; transition: color 0.2s; }
    .toggle-password:hover { color: #333; }
    .admin-dashboard { display: flex; gap: 25px; flex-wrap: wrap; }
    .panel { flex: 1; min-width: 280px; background: rgba(255,255,255,0.85); border-radius: 12px; padding: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.04); border: 1px solid rgba(143,206,176,0.3); transition: transform 0.2s; }
    .panel:hover { transform: translateY(-3px); }
    .panel-title { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; font-size: 1.2em; font-weight: 600; color: #2d5a48; }
    .file-list { display: flex; flex-direction: column; gap: 10px; max-height: 500px; overflow-y: auto; padding-right: 5px; }
    .file-item { display: flex; justify-content: space-between; align-items: center; padding: 12px 15px; background: white; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.04); transition: transform 0.15s, box-shadow 0.15s; border-left: 3px solid var(--primary); animation: slideIn 0.3s ease-out both; animation-delay: calc(var(--i, 0) * 0.03s); }
    .file-item:hover { transform: translateX(4px); box-shadow: 0 4px 10px rgba(0,0,0,0.08); }
    @keyframes slideIn { from { opacity: 0; transform: translateX(-10px); } to { opacity: 1; transform: translateX(0); } }
    .file-info { flex: 1; min-width: 0; }
    .file-name { font-weight: 500; color: #2d5a48; word-break: break-word; }
    .file-meta { font-size: 0.85em; color: #6b8b7d; }
    .file-actions { display: flex; gap: 8px; margin-left: 10px; }
    .user-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
    .user-table th, .user-table td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #e0f0e9; }
    .user-table th { background: #f0f8f4; font-weight: 600; color: #2d5a48; }
    .user-table tr:hover td { background: #fafdff; }
    .error-box, .success-box { text-align: center; padding: 40px 20px; }
    .error-box h2, .success-box h2 { margin-bottom: 15px; }
    .error-box h2 { color: #d9534f; }
    .success-box h2 { color: var(--success); }
    .error-box .btn, .success-box .btn { margin-top: 15px; }
    .theme-selector { display: flex; flex-direction: column; gap: 10px; }
    .theme-option { display: flex; align-items: center; gap: 10px; padding: 10px 15px; border: 2px solid #ccc; border-radius: 8px; cursor: pointer; transition: border-color 0.2s, background 0.2s; background: white; }
    .theme-option:hover { border-color: #999; background: #f5f5f5; }
    .theme-option.selected { border-color: var(--primary); background: rgba(143,206,176,0.1); }
    .theme-option input[type="radio"] { margin-right: 5px; }
    .theme-preview { width: 30px; height: 30px; border-radius: 50%; display: inline-block; border: 1px solid #ddd; background-size: cover; }
    .profile-layout { display: flex; gap: 30px; align-items: flex-start; }
    .profile-sidebar { flex: 0 0 220px; }
    .profile-main { flex: 1; min-width: 0; }
    .profile-avatar-upload { 
        position: relative; 
        width: 80px; 
        height: 80px; 
        margin-bottom: 15px; 
        cursor: pointer; 
        overflow: hidden; 
        border-radius: 50%;
        background: #f0f0f0;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .profile-avatar-upload img { 
        width: 100%; 
        height: 100%; 
        object-fit: contain;
        transform-origin: center center;
        transition: transform 0.2s; 
    }
    .profile-avatar-upload input[type="file"] { position: absolute; width: 100%; height: 100%; opacity: 0; cursor: pointer; top: 0; left: 0; }
    .avatar-scale-control { margin-top: 10px; }
    body[data-theme='grey'] {
        --bg-gradient: linear-gradient(135deg, #e0e0e0, #cfcfcf);
        --primary: #b0b0b0; --primary-dark: #999999; --secondary: #e8e8e8; --success: #a0a0a0; --danger: #e0a0a0; --danger-dark: #cc8888;
    }
    body[data-theme='grey'] .header h1, body[data-theme='grey'] .panel-title, body[data-theme='grey'] .form-group label, body[data-theme='grey'] .file-name { color: #555; }
    body[data-theme='grey'] .role-badge { background: #b0b0b0; }
    body[data-theme='grey'] .container { background: rgba(245,245,245,0.95); }
    body[data-theme='grey'] .btn-secondary { background: #e8e8e8; color: #555; }

    body[data-theme='red'] {
        --bg-gradient: linear-gradient(135deg, #f8d7da, #f5c2c7);
        --primary: #e74c3c; --primary-dark: #c0392b; --secondary: #fde8e8; --success: #e74c3c; --danger: #e74c3c; --danger-dark: #c0392b;
    }
    body[data-theme='red'] .header h1, body[data-theme='red'] .panel-title, body[data-theme='red'] .form-group label, body[data-theme='red'] .file-name { color: #922b21; }
    body[data-theme='red'] .role-badge { background: #e74c3c; }
    body[data-theme='red'] .container { background: rgba(255,245,245,0.95); }
    body[data-theme='red'] .btn-secondary { background: #fde8e8; color: #922b21; }

    body[data-theme='orange'] {
        --bg-gradient: linear-gradient(135deg, #ffe0b2, #ffcc80);
        --primary: #fb8c00; --primary-dark: #f57c00; --secondary: #ffe0b2; --success: #fb8c00; --danger: #ff7043; --danger-dark: #e64a19;
    }
    body[data-theme='orange'] .header h1, body[data-theme='orange'] .panel-title, body[data-theme='orange'] .form-group label, body[data-theme='orange'] .file-name { color: #e65100; }
    body[data-theme='orange'] .role-badge { background: #fb8c00; }
    body[data-theme='orange'] .container { background: rgba(255,250,240,0.95); }
    body[data-theme='orange'] .btn-secondary { background: #ffe0b2; color: #e65100; }

    body[data-theme='pink'] {
        --bg-gradient: linear-gradient(135deg, #f8bbd0, #f48fb1);
        --primary: #ec407a; --primary-dark: #d81b60; --secondary: #fce4ec; --success: #ec407a; --danger: #ef5350; --danger-dark: #c62828;
    }
    body[data-theme='pink'] .header h1, body[data-theme='pink'] .panel-title, body[data-theme='pink'] .form-group label, body[data-theme='pink'] .file-name { color: #880e4f; }
    body[data-theme='pink'] .role-badge { background: #ec407a; }
    body[data-theme='pink'] .container { background: rgba(255,245,250,0.95); }
    body[data-theme='pink'] .btn-secondary { background: #fce4ec; color: #880e4f; }

    body[data-theme='blue'] {
        --bg-gradient: linear-gradient(135deg, #bbdefb, #90caf9);
        --primary: #1976d2; --primary-dark: #1565c0; --secondary: #e3f2fd; --success: #1976d2; --danger: #e53935; --danger-dark: #c62828;
    }
    body[data-theme='blue'] .header h1, body[data-theme='blue'] .panel-title, body[data-theme='blue'] .form-group label, body[data-theme='blue'] .file-name { color: #0d47a1; }
    body[data-theme='blue'] .role-badge { background: #1976d2; }
    body[data-theme='blue'] .container { background: rgba(245,250,255,0.95); }
    body[data-theme='blue'] .btn-secondary { background: #e3f2fd; color: #0d47a1; }

    body[data-theme='lightblue'] {
        --bg-gradient: linear-gradient(135deg, #b3e5fc, #81d4fa);
        --primary: #0288d1; --primary-dark: #0277bd; --secondary: #e1f5fe; --success: #0288d1; --danger: #ef5350; --danger-dark: #c62828;
    }
    body[data-theme='lightblue'] .header h1, body[data-theme='lightblue'] .panel-title, body[data-theme='lightblue'] .form-group label, body[data-theme='lightblue'] .file-name { color: #01579b; }
    body[data-theme='lightblue'] .role-badge { background: #0288d1; }
    body[data-theme='lightblue'] .container { background: rgba(240,250,255,0.95); }
    body[data-theme='lightblue'] .btn-secondary { background: #e1f5fe; color: #01579b; }

    @media (max-width: 800px) {
        .admin-dashboard { flex-direction: column; }
        .header { flex-direction: column; gap: 10px; }
        .header .user-info { flex-wrap: wrap; justify-content: center; }
        .profile-layout { flex-direction: column; }
        .profile-sidebar { flex: 1; width: 100%; }
    }
    /* Новые стили для профиля и редактора аватара */
    .profile-close-btn { position: absolute; top: 20px; right: 20px; font-size: 2em; color: #2d5a48; background: none; border: none; cursor: pointer; }
    .avatar-editor { display: none; margin-top: 15px; background: #f0f8f4; padding: 20px; border-radius: 10px; border: 1px solid #cde5db; }
    .avatar-editor.active { display: block; }
    .avatar-preview-container { 
        width: 150px; 
        height: 150px; 
        border-radius: 50%; 
        overflow: hidden; 
        position: relative; 
        margin: 0 auto; 
        border: 3px solid var(--primary); 
        cursor: grab;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #f0f0f0;
    }
    .avatar-preview-container:active { cursor: grabbing; }
    .avatar-preview-img { 
        width: 100%; 
        height: 100%; 
        object-fit: contain; 
        transform-origin: center center; 
        transition: none; 
    }
    .avatar-controls { display: flex; align-items: center; justify-content: center; gap: 10px; margin-top: 15px; }
    .avatar-controls button { background: var(--primary); color: white; border: none; border-radius: 50%; width: 36px; height: 36px; font-size: 1.2em; cursor: pointer; }
    .avatar-controls button:hover { background: var(--primary-dark); }
    .avatar-save-btn { margin-top: 15px; text-align: center; }
</style>
'''

UPLOAD_FOLDER = 'uploads'
AVATAR_FOLDER = 'avatars'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AVATAR_FOLDER, exist_ok=True)

def get_db():
    db = sqlite3.connect('database.db')
    db.row_factory = sqlite3.Row
    return db

def cleanup_invalid_users():
    with get_db() as db:
        users = db.execute('SELECT * FROM users').fetchall()
        for user in users:
            if not is_valid_username(user['username']) or not is_valid_password(user['password']):
                files = db.execute('SELECT * FROM files WHERE user_id = ?', (user['id'],)).fetchall()
                for f in files:
                    path = os.path.join(UPLOAD_FOLDER, str(user['id']), f['filename'])
                    if os.path.exists(path):
                        try:
                            os.remove(path)
                        except:
                            pass
                db.execute('DELETE FROM files WHERE user_id = ?', (user['id'],))
                db.execute('DELETE FROM users WHERE id = ?', (user['id'],))
        db.commit()

def init_db():
    with get_db() as db:
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT,
                role TEXT DEFAULT 'user'
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                original_name TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_public INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS password_resets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        columns = [row[1] for row in db.execute('PRAGMA table_info(users)').fetchall()]
        if 'email' not in columns:
            db.execute('ALTER TABLE users ADD COLUMN email TEXT')
        if 'avatar' not in columns:
            db.execute('ALTER TABLE users ADD COLUMN avatar TEXT')
        if 'theme' not in columns:
            db.execute('ALTER TABLE users ADD COLUMN theme TEXT DEFAULT "green"')
        if 'avatar_scale' not in columns:
            db.execute('ALTER TABLE users ADD COLUMN avatar_scale REAL DEFAULT 1.0')
        if 'avatar_offset_x' not in columns:
            db.execute('ALTER TABLE users ADD COLUMN avatar_offset_x REAL DEFAULT 0.0')
        if 'avatar_offset_y' not in columns:
            db.execute('ALTER TABLE users ADD COLUMN avatar_offset_y REAL DEFAULT 0.0')
        db.commit()
    cleanup_invalid_users()

init_db()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            return render_template_string(STYLES + '''
                <div class="bubble"></div><div class="bubble"></div><div class="bubble"></div>
                <div class="bubble"></div><div class="bubble"></div><div class="bubble"></div>
                <div class="bubble"></div><div class="bubble"></div>
                <div class="container">
                    <div class="error-box">
                        <h2>Доступ запрещён</h2>
                        <p>Только администраторы имеют доступ к этой странице.</p>
                        <a href="/dashboard" class="btn btn-primary">Назад</a>
                    </div>
                </div>
            ''')
        return f(*args, **kwargs)
    return decorated

def render_with_bubbles(template, **kwargs):
    theme = 'green'
    avatar_url = None
    if 'user_id' in session:
        with get_db() as db:
            user = db.execute('SELECT theme, avatar FROM users WHERE id = ?', (session['user_id'],)).fetchone()
            if user:
                theme = user['theme'] or 'green'
                avatar_url = user['avatar']
    theme = kwargs.pop('theme', theme)
    avatar_url = kwargs.pop('avatar_url', avatar_url)
    bubbles_html = '''
        <div class="bubble"></div><div class="bubble"></div><div class="bubble"></div>
        <div class="bubble"></div><div class="bubble"></div><div class="bubble"></div>
        <div class="bubble"></div><div class="bubble"></div>
    '''
    body_start = f'<body data-theme="{theme}">'
    body_end = '</body>'
    full_template = body_start + bubbles_html + template + body_end
    return render_template_string(STYLES + full_template, **kwargs, theme=theme, avatar_url=avatar_url)

def send_reset_email(to_email: str, reset_url: str) -> bool:
    smtp_server = os.environ.get('SMTP_SERVER', 'smtp.yandex.ru')
    smtp_port = int(os.environ.get('SMTP_PORT', 465))
    sender_email = os.environ.get('SMTP_EMAIL')
    sender_password = os.environ.get('SMTP_PASSWORD')
    if not sender_email or not sender_password:
        print('SMTP не настроен')
        return False
    msg = MIMEMultipart('alternative')
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = 'Сброс пароля BUBL SERVICE'
    text = f'''Здравствуйте!

Для смены пароля перейдите по ссылке:
{reset_url}

Ссылка действительна 30 минут.
'''
    html = f'''
    <html>
    <body style="font-family: Arial, sans-serif; background-color:#d8f3e4; padding:20px;">
        <div style="max-width:600px;margin:0 auto;background:white;border-radius:10px;padding:30px;text-align:center;">
            <h1 style="color:#2d5a48; font-size:24px; margin-bottom:20px;">СБРОС ПАРОЛЯ BUBL SERVICE</h1>
            <p style="color:#333; margin-bottom:20px;">Для смены пароля нажмите кнопку ниже:</p>
            <a href="{reset_url}" style="display:inline-block;padding:12px 24px;background-color:#8fceb0;color:white;text-decoration:none;border-radius:8px;font-weight:bold;font-size:16px;">Смена</a>
            <p style="margin-top:20px;color:#666;">Ссылка действительна 30 минут.</p>
        </div>
    </body>
    </html>
    '''
    part1 = MIMEText(text, 'plain', 'utf-8')
    part2 = MIMEText(html, 'html', 'utf-8')
    msg.attach(part1)
    msg.attach(part2)
    try:
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f'Ошибка отправки: {e}')
        return False

# ---------- Маршруты ----------
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_with_bubbles('''
        <div class="container">
            <div class="header">
                <h1>Файловый сервер</h1>
            </div>
            <div style="text-align: center; margin-top: 30px;">
                <p style="font-size: 1.1em; margin-bottom: 30px;">Добро пожаловать!</p>
                <a href="/login" class="btn btn-primary">Войти</a>
                <a href="/register" class="btn btn-secondary">Регистрация</a>
            </div>
        </div>
    ''')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form.get('email', '').strip()  # email необязателен
        role = 'user'
        theme = 'green'
        if not is_valid_username(username) or not is_valid_password(password):
            return render_with_bubbles('''
                <div class="container">
                    <div class="error-box">
                        <h2>Ошибка</h2>
                        <p>Логин и пароль должны быть не короче 6 символов, пароль должен содержать заглавную букву.</p>
                        <a href="/register" class="btn btn-primary">Назад</a>
                    </div>
                </div>
            ''')
        # Валидация email только если он введён
        if email and not is_valid_email(email):
            return render_with_bubbles('''
                <div class="container">
                    <div class="error-box">
                        <h2>Ошибка</h2>
                        <p>Введите корректный email или оставьте поле пустым.</p>
                        <a href="/register" class="btn btn-primary">Назад</a>
                    </div>
                </div>
            ''')
        with get_db() as db:
            user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            if user:
                return render_with_bubbles('''
                    <div class="container">
                        <div class="error-box">
                            <h2>Ошибка</h2>
                            <p>Пользователь уже существует.</p>
                            <a href="/register" class="btn btn-primary">Назад</a>
                        </div>
                    </div>
                ''')
            # Проверка уникальности email только если он указан
            if email:
                email_exists = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
                if email_exists:
                    return render_with_bubbles('''
                        <div class="container">
                            <div class="error-box">
                                <h2>Ошибка</h2>
                                <p>Email уже используется.</p>
                                <a href="/register" class="btn btn-primary">Назад</a>
                            </div>
                        </div>
                    ''')
            email_value = email if email else None
            cursor = db.execute('INSERT INTO users (username, password, email, role, theme) VALUES (?, ?, ?, ?, ?)',
                               (username, password, email_value, role, theme))
            db.commit()
            user_id = cursor.lastrowid
        session['user_id'] = user_id
        session['username'] = username
        session['role'] = role
        session.permanent = True
        return redirect(url_for('dashboard'))
    return render_with_bubbles('''
        <div class="container">
            <div class="form-box">
                <h2>Регистрация</h2>
                <form method="post">
                    <div class="form-group">
                        <label>Логин:</label>
                        <input type="text" name="username" required minlength="6">
                    </div>
                    <div class="form-group">
                        <label>Эл. почта (необязательно):</label>
                        <input type="email" name="email">
                        <small style="display:block; margin-top:5px; color:#666;">Укажите почту, если хотите иметь возможность восстановить пароль.</small>
                    </div>
                    <div class="form-group">
                        <label>Пароль:</label>
                        <input type="password" name="password" id="reg_password" required minlength="6">
                        <span class="toggle-password" onclick="togglePassword('reg_password', this)">👁️</span>
                    </div>
                    <button type="submit" class="btn btn-primary">Зарегистрироваться</button>
                </form>
                <p style="margin-top: 15px;">Уже есть аккаунт? <a href="/login" class="btn btn-secondary btn-sm">Войти</a></p>
            </div>
        </div>
        <script>
            function togglePassword(inputId, eyeIcon) {
                const input = document.getElementById(inputId);
                if (input.type === 'password') {
                    input.type = 'text';
                    eyeIcon.textContent = '🙈';
                } else {
                    input.type = 'password';
                    eyeIcon.textContent = '👁️';
                }
            }
        </script>
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with get_db() as db:
            user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            if user and user['password'] == password:
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                session.permanent = True
                return redirect(url_for('dashboard'))
            else:
                return render_with_bubbles('''
                    <div class="container">
                        <div class="error-box">
                            <h2>Ошибка входа</h2>
                            <p>Неверный логин или пароль.</p>
                            <a href="/login" class="btn btn-primary">Попробовать снова</a>
                        </div>
                    </div>
                ''')
    return render_with_bubbles('''
        <div class="container">
            <div class="form-box">
                <h2>Вход</h2>
                <form method="post">
                    <div class="form-group">
                        <label>Логин:</label>
                        <input type="text" name="username" required>
                    </div>
                    <div class="form-group">
                        <label>Пароль:</label>
                        <input type="password" name="password" id="login_password" required>
                        <span class="toggle-password" onclick="togglePassword('login_password', this)">👁️</span>
                    </div>
                    <button type="submit" class="btn btn-primary">Войти</button>
                </form>
                <p style="margin-top: 15px;">Нет аккаунта? <a href="/register" class="btn btn-secondary btn-sm">Регистрация</a></p>
                <p style="margin-top: 10px;"><a href="/forgot_password" class="btn btn-secondary btn-sm">Забыли пароль?</a></p>
            </div>
        </div>
        <script>
            function togglePassword(inputId, eyeIcon) {
                const input = document.getElementById(inputId);
                if (input.type === 'password') {
                    input.type = 'text';
                    eyeIcon.textContent = '🙈';
                } else {
                    input.type = 'password';
                    eyeIcon.textContent = '👁️';
                }
            }
        </script>
    ''')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email'].strip()
        if not is_valid_email(email):
            return render_with_bubbles('''
                <div class="container">
                    <div class="error-box">
                        <h2>Ошибка</h2>
                        <p>Введите корректный email.</p>
                        <a href="/forgot_password" class="btn btn-primary">Назад</a>
                    </div>
                </div>
            ''')
        with get_db() as db:
            user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
            if not user:
                return render_with_bubbles('''
                    <div class="container">
                        <div class="error-box">
                            <h2>Ошибка</h2>
                            <p>Такая почта не зарегистрирована.</p>
                            <a href="/forgot_password" class="btn btn-primary">Назад</a>
                        </div>
                    </div>
                ''')
            token = uuid.uuid4().hex
            expires_at = (datetime.now() + timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S')
            db.execute('INSERT INTO password_resets (user_id, token, expires_at) VALUES (?, ?, ?)',
                       (user['id'], token, expires_at))
            db.commit()
            reset_url = url_for('reset_password', token=token, _external=True)
            if send_reset_email(email, reset_url):
                return render_with_bubbles('''
                    <div class="container">
                        <div class="success-box">
                            <h2>Проверьте почту</h2>
                            <p>Ссылка отправлена на ''' + email + '''.</p>
                            <a href="/login" class="btn btn-primary">Вернуться ко входу</a>
                        </div>
                    </div>
                ''')
            else:
                return render_with_bubbles('''
                    <div class="container">
                        <div class="error-box">
                            <h2>Ошибка отправки</h2>
                            <p>Не удалось отправить email.</p>
                            <a href="/login" class="btn btn-primary">Вернуться ко входу</a>
                        </div>
                    </div>
                ''')
    return render_with_bubbles('''
        <div class="container">
            <div class="form-box">
                <h2>Забыли пароль?</h2>
                <form method="post">
                    <div class="form-group">
                        <label>Эл. почта:</label>
                        <input type="email" name="email" required>
                    </div>
                    <button type="submit" class="btn btn-primary">Отправить</button>
                </form>
                <p style="margin-top: 15px;"><a href="/login" class="btn btn-secondary btn-sm">Вернуться ко входу</a></p>
            </div>
        </div>
    ''')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    with get_db() as db:
        reset = db.execute('SELECT * FROM password_resets WHERE token = ?', (token,)).fetchone()
        if not reset:
            return render_with_bubbles('''
                <div class="container">
                    <div class="error-box">
                        <h2>Недействительная ссылка</h2>
                        <p>Срок действия ссылки истёк.</p>
                        <a href="/forgot_password" class="btn btn-primary">Запросить новую</a>
                    </div>
                </div>
            ''')
        if request.method == 'POST':
            new_password = request.form['password']
            if not is_valid_password(new_password):
                return render_with_bubbles('''
                    <div class="container">
                        <div class="error-box">
                            <h2>Ошибка</h2>
                            <p>Пароль должен быть не короче 6 символов и содержать заглавную букву.</p>
                            <a href="/reset_password/''' + token + '''" class="btn btn-primary">Назад</a>
                        </div>
                    </div>
                ''')
            db.execute('UPDATE users SET password = ? WHERE id = ?', (new_password, reset['user_id']))
            db.execute('DELETE FROM password_resets WHERE token = ?', (token,))
            db.commit()
            return render_with_bubbles('''
                <div class="container">
                    <div class="success-box">
                        <h2>Пароль изменён</h2>
                        <a href="/login" class="btn btn-primary">Войти</a>
                    </div>
                </div>
            ''')
    return render_with_bubbles('''
        <div class="container">
            <div class="form-box">
                <h2>Новый пароль</h2>
                <form method="post">
                    <div class="form-group">
                        <label>Новый пароль:</label>
                        <input type="password" name="password" id="new_password" required minlength="6">
                        <span class="toggle-password" onclick="togglePassword('new_password', this)">👁️</span>
                    </div>
                    <button type="submit" class="btn btn-primary">Сохранить</button>
                </form>
            </div>
        </div>
        <script>
            function togglePassword(inputId, eyeIcon) {
                const input = document.getElementById(inputId);
                if (input.type === 'password') {
                    input.type = 'text';
                    eyeIcon.textContent = '🙈';
                } else {
                    input.type = 'password';
                    eyeIcon.textContent = '👁️';
                }
            }
        </script>
    ''', token=token)

@app.route('/logout')
def logout():
    session.clear()
    return render_with_bubbles('''
        <div class="container">
            <div class="success-box">
                <h2>До свидания!</h2>
                <a href="/" class="btn btn-primary">На главную</a>
            </div>
        </div>
    ''')

@app.route('/dashboard')
@login_required
def dashboard():
    username = session['username']
    role = session['role']
    user_id = session['user_id']
    with get_db() as db:
        # Получаем параметры аватара текущего пользователя
        user = db.execute('SELECT avatar_scale, avatar_offset_x, avatar_offset_y FROM users WHERE id = ?', (user_id,)).fetchone()
        avatar_scale = user['avatar_scale'] if user and 'avatar_scale' in user.keys() else 1.0
        avatar_offset_x = user['avatar_offset_x'] if user and 'avatar_offset_x' in user.keys() else 0.0
        avatar_offset_y = user['avatar_offset_y'] if user and 'avatar_offset_y' in user.keys() else 0.0

        public_files = db.execute('''
            SELECT files.*, users.username 
            FROM files JOIN users ON files.user_id = users.id 
            WHERE files.is_public = 1 ORDER BY files.uploaded_at DESC
        ''').fetchall()
        private_files = []
        if role == 'admin':
            private_files = db.execute('''
                SELECT files.*, users.username 
                FROM files JOIN users ON files.user_id = users.id 
                WHERE files.is_public = 0 ORDER BY files.uploaded_at DESC
            ''').fetchall()
    
    if role != 'admin':
        return render_with_bubbles('''
            <div class="container">
                <div class="header">
                    <h1>Доступные файлы</h1>
                    <div class="user-info">
                        <a href="/profile">
                            {% if avatar_url %}
                                <div class="avatar">
                                    <img src="/avatar/{{ session['user_id'] }}" style="transform: translate(-50%, -50%) scale({{ avatar_scale }}) translate({{ avatar_offset_x }}px, {{ avatar_offset_y }}px);">
                                </div>
                            {% else %}
                                <div class="avatar">{{ username[0]|upper }}</div>
                            {% endif %}
                        </a>
                        <span class="role-badge">Пользователь: {{ username }}</span>
                        <button class="settings-gear" onclick="toggleSettingsMenu()">⚙️</button>
                        <div class="settings-menu" id="settingsMenu">
                            <a href="/profile">Профиль</a>
                        </div>
                        <a href="/logout" class="btn btn-secondary btn-sm">Выйти</a>
                    </div>
                </div>
                {% if public_files %}
                <div class="file-list">
                    {% for file in public_files %}
                    <div class="file-item">
                        <div class="file-info">
                            <div class="file-name">📄 {{ file.original_name }}</div>
                            <div class="file-meta">Загрузил: {{ file.username }}</div>
                        </div>
                        <div class="file-actions">
                            <a href="/download/{{ file.id }}" class="btn btn-success btn-sm">⬇️ Скачать</a>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% else %}
                <p>Пока нет файлов.</p>
                {% endif %}
            </div>
            <script>
                function toggleSettingsMenu() {
                    document.getElementById('settingsMenu').classList.toggle('show');
                }
                window.onclick = function(event) {
                    if (!event.target.matches('.settings-gear')) {
                        var menus = document.getElementsByClassName('settings-menu');
                        for (var i = 0; i < menus.length; i++) menus[i].classList.remove('show');
                    }
                }
            </script>
        ''', public_files=public_files, username=username,
           avatar_scale=avatar_scale, avatar_offset_x=avatar_offset_x, avatar_offset_y=avatar_offset_y)
    
    return render_with_bubbles('''
        <div class="container">
            <div class="header">
                <h1>Панель администратора</h1>
                <div class="user-info">
                    <a href="/profile">
                        {% if avatar_url %}
                            <div class="avatar">
                                <img src="/avatar/{{ session['user_id'] }}" style="transform: translate(-50%, -50%) scale({{ avatar_scale }}) translate({{ avatar_offset_x }}px, {{ avatar_offset_y }}px);">
                            </div>
                        {% else %}
                            <div class="avatar">{{ username[0]|upper }}</div>
                        {% endif %}
                    </a>
                    <span class="role-badge">Администратор: {{ username }}</span>
                    <button class="settings-gear" onclick="toggleSettingsMenu()">⚙️</button>
                    <div class="settings-menu" id="settingsMenu">
                        <a href="/profile">Профиль</a>
                        <a href="/admin/users">Участники</a>
                    </div>
                    <a href="/logout" class="btn btn-secondary btn-sm">Выйти</a>
                </div>
            </div>
            <div class="admin-dashboard">
                <div class="panel">
                    <div class="panel-title">
                        <span>Общедоступные файлы</span>
                        <a href="/upload?visibility=public" class="btn btn-primary btn-sm">Загрузить</a>
                    </div>
                    <div class="file-list">
                        {% for file in public_files %}
                        <div class="file-item">
                            <div class="file-info">
                                <div class="file-name">📄 {{ file.original_name }}</div>
                                <div class="file-meta">Загрузил: {{ file.username }}</div>
                            </div>
                            <div class="file-actions">
                                <a href="/download/{{ file.id }}" class="btn btn-success btn-sm">⬇️</a>
                                <a href="/rename/{{ file.id }}" class="btn btn-secondary btn-sm">✏️</a>
                                <a href="/delete/{{ file.id }}" class="btn btn-danger btn-sm" onclick="return confirm('Удалить файл?')">🗑️</a>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
                <div class="panel">
                    <div class="panel-title">
                        <span>Приватные файлы</span>
                        <a href="/upload?visibility=private" class="btn btn-primary btn-sm">Загрузить</a>
                    </div>
                    <div class="file-list">
                        {% for file in private_files %}
                        <div class="file-item">
                            <div class="file-info">
                                <div class="file-name">📄 {{ file.original_name }}</div>
                                <div class="file-meta">Загрузил: {{ file.username }}</div>
                            </div>
                            <div class="file-actions">
                                <a href="/download/{{ file.id }}" class="btn btn-success btn-sm">⬇️</a>
                                <a href="/delete/{{ file.id }}" class="btn btn-danger btn-sm" onclick="return confirm('Удалить файл?')">🗑️</a>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
        <script>
            function toggleSettingsMenu() {
                document.getElementById('settingsMenu').classList.toggle('show');
            }
            window.onclick = function(event) {
                if (!event.target.matches('.settings-gear')) {
                    var menus = document.getElementsByClassName('settings-menu');
                    for (var i = 0; i < menus.length; i++) menus[i].classList.remove('show');
                }
            }
        </script>
    ''', username=username, public_files=public_files, private_files=private_files,
       avatar_scale=avatar_scale, avatar_offset_x=avatar_offset_x, avatar_offset_y=avatar_offset_y)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = session['user_id']
    with get_db() as db:
        user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    
    themes = [
        {'value': 'green', 'label': 'Зелёная', 'preview': 'linear-gradient(135deg, #8fceb0, #6bb894)'},
        {'value': 'grey', 'label': 'Серая', 'preview': 'linear-gradient(135deg, #b0b0b0, #999999)'},
        {'value': 'red', 'label': 'Красная', 'preview': 'linear-gradient(135deg, #e74c3c, #c0392b)'},
        {'value': 'orange', 'label': 'Оранжевая', 'preview': 'linear-gradient(135deg, #fb8c00, #f57c00)'},
        {'value': 'pink', 'label': 'Розовая', 'preview': 'linear-gradient(135deg, #ec407a, #d81b60)'},
        {'value': 'blue', 'label': 'Синяя', 'preview': 'linear-gradient(135deg, #1976d2, #1565c0)'},
        {'value': 'lightblue', 'label': 'Голубая', 'preview': 'linear-gradient(135deg, #0288d1, #0277bd)'},
    ]
    
    if request.method == 'POST':
        new_username = request.form['username'].strip()
        new_email = request.form.get('email', '').strip()
        new_theme = request.form.get('theme', 'green')
        if new_theme not in ['green', 'grey', 'red', 'orange', 'pink', 'blue', 'lightblue']:
            new_theme = 'green'
        if not is_valid_username(new_username):
            return jsonify({'status': 'error', 'message': 'Логин слишком короткий'}), 400
        if new_email and not is_valid_email(new_email):
            return jsonify({'status': 'error', 'message': 'Некорректный email'}), 400
        with get_db() as db:
            if new_email:
                existing = db.execute('SELECT id FROM users WHERE email = ? AND id != ?', (new_email, user_id)).fetchone()
                if existing:
                    return jsonify({'status': 'error', 'message': 'Этот email уже используется'}), 400
            email_value = new_email if new_email else None
            db.execute('UPDATE users SET username=?, email=?, theme=? WHERE id=?',
                       (new_username, email_value, new_theme, user_id))
            db.commit()
        session['username'] = new_username
        return jsonify({'status': 'ok'})
    
    # Безопасно извлекаем параметры аватара
    avatar_scale = user['avatar_scale'] if 'avatar_scale' in user.keys() else 1.0
    avatar_offset_x = user['avatar_offset_x'] if 'avatar_offset_x' in user.keys() else 0.0
    avatar_offset_y = user['avatar_offset_y'] if 'avatar_offset_y' in user.keys() else 0.0

    return render_with_bubbles('''
        <div class="container" style="position: relative;">
            <button class="profile-close-btn" onclick="window.location.href='/dashboard'" title="Закрыть">×</button>
            <h2 style="margin-bottom: 20px;">Настройки профиля</h2>
            <div class="profile-layout">
                <div class="profile-sidebar">
                    <h3>Тема оформления</h3>
                    <div class="theme-selector">
                        {% for theme in themes %}
                        <label class="theme-option {% if user.theme == theme.value %}selected{% endif %}" onclick="setTheme('{{ theme.value }}')">
                            <input type="radio" name="theme" value="{{ theme.value }}" {% if user.theme == theme.value %}checked{% endif %}>
                            <span class="theme-preview" style="background: {{ theme.preview }};"></span>
                            {{ theme.label }}
                        </label>
                        {% endfor %}
                    </div>
                </div>
                <div class="profile-main">
                    <form id="profile-form" method="post">
                        <div class="form-group">
                            <label>Никнейм:</label>
                            <input type="text" name="username" id="username-input" value="{{ user.username }}" required minlength="6">
                        </div>
                        <div class="form-group">
                            <label>Эл. почта (необязательно):</label>
                            <input type="email" name="email" id="email-input" value="{{ user.email or '' }}">
                            <small style="display:block; margin-top:5px; color:#666;">Почта нужна для восстановления пароля. Без неё восстановить доступ будет невозможно.</small>
                        </div>
                    </form>
                    <!-- Форма для аватара -->
                    <form id="avatar-form" enctype="multipart/form-data" style="display: none;">
                        <input type="file" name="avatar" id="avatar-input" accept=".png,.jpg,.jpeg">
                        <input type="hidden" name="avatar_scale" id="avatar-scale-hidden" value="1.0">
                        <input type="hidden" name="avatar_offset_x" id="avatar-offset-x-hidden" value="0">
                        <input type="hidden" name="avatar_offset_y" id="avatar-offset-y-hidden" value="0">
                    </form>
                    <div class="form-group">
                        <label>Аватар:</label>
                        <div class="profile-avatar-upload" id="avatar-upload-area">
                            {% if user.avatar %}
                                <img id="avatar-preview" src="/avatar/{{ user.id }}" alt="Аватар" style="transform: scale({{ avatar_scale }}) translate({{ avatar_offset_x }}px, {{ avatar_offset_y }}px);">
                            {% else %}
                                <div id="avatar-preview" style="width:100%;height:100%;background: var(--primary); display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 2em;">{{ user.username[0]|upper }}</div>
                            {% endif %}
                        </div>
                        <button type="button" class="btn btn-secondary btn-sm" onclick="document.getElementById('avatar-input').click();">Выбрать файл</button>
                    </div>

                    <!-- Редактор аватара (появляется после выбора файла) -->
                    <div class="avatar-editor" id="avatar-editor">
                        <div class="avatar-preview-container" id="avatar-preview-container">
                            <img id="avatar-editor-img" class="avatar-preview-img" src="" alt="Предпросмотр">
                        </div>
                        <div class="avatar-controls">
                            <button type="button" id="zoom-out" title="Уменьшить">−</button>
                            <span id="zoom-value">100%</span>
                            <button type="button" id="zoom-in" title="Увеличить">+</button>
                        </div>
                        <div class="avatar-save-btn">
                            <button type="button" class="btn btn-primary" id="save-avatar-btn">Готово</button>
                        </div>
                        <p style="text-align:center; font-size:0.9em; color:#666;">Перетаскивайте изображение для настройки положения, используйте колесо мыши или кнопки для масштабирования.</p>
                    </div>
                </div>
            </div>
        </div>
        <script>
            // ===== Мгновенное сохранение темы и ника (и email) =====
            function setTheme(theme) {
                document.body.dataset.theme = theme;
                // Сохраняем тему
                fetch('/profile', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: new URLSearchParams({
                        username: document.getElementById('username-input').value,
                        email: document.getElementById('email-input').value,
                        theme: theme
                    })
                }).then(r => r.json()).then(data => {
                    if (data.status !== 'ok') console.error('Ошибка сохранения темы');
                });
                // Обновляем визуальное выделение
                var radios = document.getElementsByName('theme');
                for (var i = 0; i < radios.length; i++) {
                    radios[i].checked = (radios[i].value === theme);
                    if (radios[i].value === theme) {
                        radios[i].parentElement.classList.add('selected');
                    } else {
                        radios[i].parentElement.classList.remove('selected');
                    }
                }
            }

            // Автосохранение ника и email при потере фокуса или Enter
            document.getElementById('username-input').addEventListener('change', function() {
                saveUsernameAndTheme();
            });
            document.getElementById('username-input').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.blur();
                }
            });
            document.getElementById('email-input').addEventListener('change', function() {
                saveUsernameAndTheme();
            });
            document.getElementById('email-input').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.blur();
                }
            });

            function saveUsernameAndTheme() {
                var username = document.getElementById('username-input').value;
                var email = document.getElementById('email-input').value;
                var theme = document.querySelector('input[name="theme"]:checked').value;
                fetch('/profile', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: new URLSearchParams({
                        username: username,
                        email: email,
                        theme: theme
                    })
                }).then(r => r.json()).then(data => {
                    if (data.status === 'ok') {
                        // Обновляем аватар-заглушку, если имя изменилось
                        var preview = document.getElementById('avatar-preview');
                        if (preview.tagName === 'DIV' && username.length > 0) {
                            preview.textContent = username[0].toUpperCase();
                        }
                    } else {
                        alert('Ошибка: ' + data.message);
                    }
                });
            }

            // ===== Редактор аватара =====
            const avatarInput = document.getElementById('avatar-input');
            const avatarEditor = document.getElementById('avatar-editor');
            const avatarEditorImg = document.getElementById('avatar-editor-img');
            const avatarPreviewContainer = document.getElementById('avatar-preview-container');
            const zoomInBtn = document.getElementById('zoom-in');
            const zoomOutBtn = document.getElementById('zoom-out');
            const zoomValueSpan = document.getElementById('zoom-value');
            const saveAvatarBtn = document.getElementById('save-avatar-btn');
            const hiddenScale = document.getElementById('avatar-scale-hidden');
            const hiddenOffsetX = document.getElementById('avatar-offset-x-hidden');
            const hiddenOffsetY = document.getElementById('avatar-offset-y-hidden');

            let currentScale = 1.0;
            let offsetX = 0;
            let offsetY = 0;
            let isDragging = false;
            let startX, startY;

            // Загрузка файла
            avatarInput.addEventListener('change', function(e) {
                const file = e.target.files[0];
                if (!file) return;
                const reader = new FileReader();
                reader.onload = function(ev) {
                    avatarEditorImg.src = ev.target.result;
                    avatarEditor.classList.add('active');
                    // Сброс параметров
                    currentScale = 1.0;
                    offsetX = 0;
                    offsetY = 0;
                    updateTransform();
                };
                reader.readAsDataURL(file);
            });

            function updateTransform() {
                avatarEditorImg.style.transform = `scale(${currentScale}) translate(${offsetX}px, ${offsetY}px)`;
                zoomValueSpan.textContent = Math.round(currentScale * 100) + '%';
                // Обновляем скрытые поля
                hiddenScale.value = currentScale;
                hiddenOffsetX.value = offsetX;
                hiddenOffsetY.value = offsetY;
            }

            // Масштабирование кнопками
            zoomInBtn.addEventListener('click', function() {
                currentScale = Math.min(3.0, currentScale + 0.1);
                updateTransform();
            });
            zoomOutBtn.addEventListener('click', function() {
                currentScale = Math.max(0.5, currentScale - 0.1);
                updateTransform();
            });

            // Масштабирование колесом мыши
            avatarPreviewContainer.addEventListener('wheel', function(e) {
                e.preventDefault();
                const delta = e.deltaY > 0 ? -0.1 : 0.1;
                currentScale = Math.min(3.0, Math.max(0.5, currentScale + delta));
                updateTransform();
            });

            // Перетаскивание
            avatarPreviewContainer.addEventListener('mousedown', function(e) {
                isDragging = true;
                startX = e.clientX - offsetX;
                startY = e.clientY - offsetY;
                avatarPreviewContainer.style.cursor = 'grabbing';
            });
            document.addEventListener('mousemove', function(e) {
                if (!isDragging) return;
                offsetX = e.clientX - startX;
                offsetY = e.clientY - startY;
                updateTransform();
            });
            document.addEventListener('mouseup', function() {
                isDragging = false;
                avatarPreviewContainer.style.cursor = 'grab';
            });

            // Сохранение аватара
            saveAvatarBtn.addEventListener('click', function() {
                const formData = new FormData();
                formData.append('avatar', avatarInput.files[0]);
                formData.append('avatar_scale', currentScale);
                formData.append('avatar_offset_x', offsetX);
                formData.append('avatar_offset_y', offsetY);

                fetch('/update_avatar', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'ok') {
                        // Обновляем аватар в интерфейсе
                        const preview = document.getElementById('avatar-preview');
                        if (preview.tagName === 'IMG') {
                            preview.src = '/avatar/' + data.user_id + '?t=' + new Date().getTime();
                            preview.style.transform = `scale(${currentScale}) translate(${offsetX}px, ${offsetY}px)`;
                        } else {
                            // Заменяем div на img
                            const img = document.createElement('img');
                            img.id = 'avatar-preview';
                            img.src = '/avatar/' + data.user_id + '?t=' + new Date().getTime();
                            img.style.width = '100%';
                            img.style.height = '100%';
                            img.style.objectFit = 'contain';
                            img.style.transform = `scale(${currentScale}) translate(${offsetX}px, ${offsetY}px)`;
                            preview.parentNode.replaceChild(img, preview);
                        }
                        // Закрываем редактор
                        avatarEditor.classList.remove('active');
                        avatarInput.value = ''; // очищаем input
                    } else {
                        alert('Ошибка сохранения аватара');
                    }
                })
                .catch(err => {
                    console.error(err);
                    alert('Ошибка сети');
                });
            });
        </script>
    ''', user=user, themes=themes, theme=user['theme'], avatar_url=user['avatar'],
       avatar_scale=avatar_scale, avatar_offset_x=avatar_offset_x, avatar_offset_y=avatar_offset_y)

# Новый маршрут для обновления аватара
@app.route('/update_avatar', methods=['POST'])
@login_required
def update_avatar():
    user_id = session['user_id']
    if 'avatar' not in request.files:
        return jsonify({'status': 'error', 'message': 'Файл не выбран'}), 400
    file = request.files['avatar']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'Файл не выбран'}), 400
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else 'jpg'
    if ext not in ['png', 'jpg', 'jpeg']:
        return jsonify({'status': 'error', 'message': 'Неподдерживаемый формат'}), 400
    filename = f"user_{user_id}.{ext}"
    filepath = os.path.join(AVATAR_FOLDER, filename)
    file.save(filepath)
    scale = float(request.form.get('avatar_scale', 1.0))
    offset_x = float(request.form.get('avatar_offset_x', 0.0))
    offset_y = float(request.form.get('avatar_offset_y', 0.0))
    scale = max(0.5, min(3.0, scale))  # ограничение
    with get_db() as db:
        db.execute('UPDATE users SET avatar=?, avatar_scale=?, avatar_offset_x=?, avatar_offset_y=? WHERE id=?',
                   (filename, scale, offset_x, offset_y, user_id))
        db.commit()
    return jsonify({'status': 'ok', 'user_id': user_id})

@app.route('/set_theme/<theme>', methods=['POST'])
@login_required
def set_theme(theme):
    if theme not in ['green', 'grey', 'red', 'orange', 'pink', 'blue', 'lightblue']:
        return jsonify({'status': 'error', 'message': 'Invalid theme'}), 400
    with get_db() as db:
        db.execute('UPDATE users SET theme=? WHERE id=?', (theme, session['user_id']))
        db.commit()
    return jsonify({'status': 'ok'})

@app.route('/avatar/<int:user_id>')
def avatar(user_id):
    with get_db() as db:
        user = db.execute('SELECT avatar FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user or not user['avatar']:
        return '', 404
    filepath = os.path.join(AVATAR_FOLDER, user['avatar'])
    if os.path.exists(filepath):
        return send_file(filepath)
    return '', 404

@app.route('/upload', methods=['GET', 'POST'])
@admin_required
def upload():
    visibility = request.args.get('visibility', 'public')
    if visibility not in ['public', 'private']:
        visibility = 'public'
    visibility_label = 'общедоступный' if visibility == 'public' else 'приватный'
    if request.method == 'POST':
        if 'file' not in request.files:
            return "Файл не выбран", 400
        file = request.files['file']
        if file.filename == '':
            return "Файл не выбран", 400
        user_id = session['user_id']
        user_folder = os.path.join(UPLOAD_FOLDER, str(user_id))
        os.makedirs(user_folder, exist_ok=True)
        original_name = file.filename
        ext = original_name.rsplit('.', 1)[-1].lower() if '.' in original_name else ''
        new_name = f"{uuid.uuid4()}.{ext}"
        save_path = os.path.join(user_folder, new_name)
        file.save(save_path)
        is_public = 1 if visibility == 'public' else 0
        with get_db() as db:
            db.execute('INSERT INTO files (filename, original_name, user_id, is_public) VALUES (?, ?, ?, ?)',
                       (new_name, original_name, user_id, is_public))
            db.commit()
        return redirect(url_for('dashboard'))
    return render_with_bubbles('''
        <div class="container">
            <div class="form-box">
                <h2>Загрузка файла ({{ visibility_label }})</h2>
                <form method="post" enctype="multipart/form-data">
                    <div class="form-group">
                        <label>Выберите файл:</label>
                        <input type="file" name="file" required>
                    </div>
                    <input type="hidden" name="visibility" value="{{ visibility }}">
                    <button type="submit" class="btn btn-primary">Загрузить</button>
                </form>
                <p style="margin-top:15px;"><a href="/dashboard" class="btn btn-secondary btn-sm">Назад</a></p>
            </div>
        </div>
    ''', visibility_label=visibility_label, visibility=visibility)

@app.route('/download/<int:file_id>')
@login_required
def download(file_id):
    with get_db() as db:
        file_record = db.execute('SELECT * FROM files WHERE id = ?', (file_id,)).fetchone()
    if not file_record:
        return "Файл не найден", 404
    if file_record['is_public'] == 0 and session.get('role') != 'admin':
        return render_with_bubbles('''
            <div class="container">
                <div class="error-box">
                    <h2>Доступ запрещён</h2>
                    <a href="/dashboard" class="btn btn-primary">Назад</a>
                </div>
            </div>
        ''')
    user_folder = os.path.join(UPLOAD_FOLDER, str(file_record['user_id']))
    file_path = os.path.join(user_folder, file_record['filename'])
    if not os.path.exists(file_path):
        return "Файл не найден", 404
    return send_file(file_path, as_attachment=True, download_name=file_record['original_name'])

@app.route('/delete/<int:file_id>')
@admin_required
def delete_file(file_id):
    with get_db() as db:
        file_record = db.execute('SELECT * FROM files WHERE id = ?', (file_id,)).fetchone()
        if not file_record:
            return "Файл не найден", 404
        file_path = os.path.join(UPLOAD_FOLDER, str(file_record['user_id']), file_record['filename'])
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        db.execute('DELETE FROM files WHERE id = ?', (file_id,))
        db.commit()
    return redirect(url_for('dashboard'))

@app.route('/rename/<int:file_id>', methods=['GET', 'POST'])
@admin_required
def rename_file(file_id):
    with get_db() as db:
        file_record = db.execute('SELECT * FROM files WHERE id = ?', (file_id,)).fetchone()
    if not file_record:
        return "Файл не найден", 404
    if request.method == 'POST':
        new_name = request.form['new_name'].strip()
        if new_name:
            with get_db() as db:
                db.execute('UPDATE files SET original_name = ? WHERE id = ?', (new_name, file_id))
                db.commit()
            return redirect(url_for('dashboard'))
    return render_with_bubbles('''
        <div class="container">
            <div class="form-box">
                <h2>Переименовать</h2>
                <form method="post">
                    <div class="form-group">
                        <input type="text" name="new_name" value="{{ file.original_name }}" required>
                    </div>
                    <button type="submit" class="btn btn-primary">Сохранить</button>
                    <a href="/dashboard" class="btn btn-secondary">Отмена</a>
                </form>
            </div>
        </div>
    ''', file=file_record)

@app.route('/admin/users')
@admin_required
def admin_users():
    with get_db() as db:
        users = db.execute('SELECT id, username, email, password, role FROM users ORDER BY id').fetchall()
    return render_with_bubbles('''
        <div class="container">
            <div class="header">
                <h1>Участники ({{ users|length }})</h1>
                <a href="/dashboard" class="btn btn-secondary btn-sm">Назад</a>
            </div>
            <table class="user-table">
                <thead><tr><th>ID</th><th>Логин</th><th>Эл. почта</th><th>Пароль</th><th>Роль</th><th>Действия</th></tr></thead>
                <tbody>
                    {% for user in users %}
                    <tr>
                        <td>{{ user.id }}</td><td>{{ user.username }}</td><td>{{ user.email or '—' }}</td>
                        <td>{{ user.password }}</td>
                        <td>{% if user.role == 'admin' %}Администратор{% else %}Пользователь{% endif %}</td>
                        <td>
                            <a href="/admin/edit_user/{{ user.id }}" class="btn btn-secondary btn-sm">✏️</a>
                            <a href="/admin/delete_user/{{ user.id }}" class="btn btn-danger btn-sm" onclick="return confirm('Удалить участника?')">🗑️</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    ''', users=users)

@app.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    with get_db() as db:
        user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            return "Пользователь не найден", 404
        if request.method == 'POST':
            new_username = request.form['username'].strip()
            new_email = request.form.get('email', '').strip()
            new_role = request.form['role']
            new_password = request.form['password'].strip()
            if not is_valid_username(new_username):
                return "Логин слишком короткий", 400
            if new_email and not is_valid_email(new_email):
                return "Некорректный email", 400
            if new_password:
                if not is_valid_password(new_password):
                    return "Пароль не соответствует требованиям", 400
                db.execute('UPDATE users SET username=?, password=?, email=?, role=? WHERE id=?',
                           (new_username, new_password, new_email if new_email else None, new_role, user_id))
            else:
                db.execute('UPDATE users SET username=?, email=?, role=? WHERE id=?',
                           (new_username, new_email if new_email else None, new_role, user_id))
            db.commit()
            return redirect(url_for('admin_users'))
    return render_with_bubbles('''
        <div class="container">
            <div class="form-box">
                <h2>Редактирование участника</h2>
                <form method="post">
                    <div class="form-group"><label>Логин:</label><input type="text" name="username" value="{{ user.username }}" required></div>
                    <div class="form-group"><label>Эл. почта (необязательно):</label><input type="email" name="email" value="{{ user.email or '' }}"></div>
                    <div class="form-group"><label>Новый пароль (оставьте пустым, чтобы не менять):</label><input type="password" name="password"></div>
                    <div class="form-group"><label>Роль:</label><select name="role">
                        <option value="user" {% if user.role == 'user' %}selected{% endif %}>Пользователь</option>
                        <option value="admin" {% if user.role == 'admin' %}selected{% endif %}>Администратор</option>
                    </select></div>
                    <button type="submit" class="btn btn-primary">Сохранить</button>
                    <a href="/admin/users" class="btn btn-secondary">Отмена</a>
                </form>
            </div>
        </div>
    ''', user=user)

@app.route('/admin/delete_user/<int:user_id>')
@admin_required
def delete_user(user_id):
    if user_id == session['user_id']:
        return "Нельзя удалить самого себя", 400
    with get_db() as db:
        files = db.execute('SELECT * FROM files WHERE user_id = ?', (user_id,)).fetchall()
        for f in files:
            path = os.path.join(UPLOAD_FOLDER, str(user_id), f['filename'])
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
        db.execute('DELETE FROM files WHERE user_id = ?', (user_id,))
        db.execute('DELETE FROM users WHERE id = ?', (user_id,))
        db.commit()
    return redirect(url_for('admin_users'))

if __name__ == '__main__':
    app.run(debug=True)
