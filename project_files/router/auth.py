from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import check_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('kullanici_adi')
        password = request.form.get('sifre')

        conn = sqlite3.connect('bulutis.db')
        c = conn.cursor()
        c.execute("SELECT id, kullanici_adi, sifre FROM kullanicilar WHERE kullanici_adi = ?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['logged_in'] = True
            session['username'] = user[1]
            return redirect(url_for('main.index'))

    return render_template('login.html', error=error)

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))