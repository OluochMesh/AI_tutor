from flask import Blueprint, render_template, redirect, url_for, session

# Blueprint setup
frontend = Blueprint('frontend', __name__)

# 🏠 Home Page
@frontend.route('/')
def home():
    return render_template('home.html')


# 👤 Authentication Pages
@frontend.route('/login')
def login():
    return render_template('login.html')


@frontend.route('/register')
def register():
    return render_template('register.html')


# 📊 Dashboard (Protected)
@frontend.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('frontend.login'))
    return render_template('dashboard.html', user=session['user'])


# 🧠 Learning (AI Tutor) Page
@frontend.route('/learn')
def learn():
    if 'user' not in session:
        return redirect(url_for('frontend.login'))
    return render_template('learn.html', user=session['user'])


# 📈 Analytics Page (Protected)
@frontend.route('/analytics')
def analytics():
    if 'user' not in session:
        return redirect(url_for('frontend.login'))

    # Example data (replace later with backend data)
    data = {
        "total_users": 124,
        "active_sessions": 48,
        "lessons_completed": 320
    }

    return render_template('analytics.html', **data, user=session['user'])


# 💳 Subscription / Plans Page
@frontend.route('/subscription')
def subscription():
    if 'user' not in session:
        return redirect(url_for('frontend.login'))
    return render_template('subscription.html', user=session['user'])


# ⚙️ Settings Page
@frontend.route('/settings')
def settings():
    if 'user' not in session:
        return redirect(url_for('frontend.login'))
    return render_template('settings.html', user=session['user'])


# 📤 Data Export Page
@frontend.route('/export-data')
def export_data():
    if 'user' not in session:
        return redirect(url_for('frontend.login'))
    return render_template('export_data.html', user=session['user'])


# 🚪 Logout Route
@frontend.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('frontend.login'))




