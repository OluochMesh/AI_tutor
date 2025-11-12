from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, session, request, g, make_response

# Blueprint setup
frontend = Blueprint('frontend', __name__)

NO_CACHE_HEADERS = {
    'Cache-Control': 'no-store, no-cache, must-revalidate, private',
    'Pragma': 'no-cache',
    'Expires': '0',
}


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('frontend.login'))
        return view_func(*args, **kwargs)

    return wrapped_view


@frontend.before_app_request
def load_logged_in_user():
    g.user = session.get('user')


@frontend.before_app_request
def enforce_login_for_protected_routes():
    protected_endpoints = {
        'frontend.dashboard',
        'frontend.learn',
        'frontend.analytics',
        'frontend.subscription',
        'frontend.settings',
        'frontend.export_data',
    }
    endpoint = request.endpoint
    if endpoint in protected_endpoints and not session.get('user_id'):
        return redirect(url_for('frontend.login'))


@frontend.after_app_request
def add_no_cache_headers(response):
    if request.blueprint == 'frontend':
        for header, value in NO_CACHE_HEADERS.items():
            response.headers[header] = value
    return response


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
@login_required
def dashboard():
    return render_template('dashboard.html', user=session.get('user'))


# 🧠 Learning (AI Tutor) Page
@frontend.route('/learn')
@login_required
def learn():
    return render_template('learn.html', user=session.get('user'))


# 📈 Analytics Page (Protected)
@frontend.route('/analytics')
@login_required
def analytics():
    # Example data (replace later with backend data)
    data = {
        "total_users": 124,
        "active_sessions": 48,
        "lessons_completed": 320
    }

    return render_template('analytics.html', **data, user=session.get('user'))


# 💳 Subscription / Plans Page
@frontend.route('/subscription')
@login_required
def subscription():
    return render_template('subscription.html', user=session.get('user'))


# ⚙️ Settings Page
@frontend.route('/settings')
@login_required
def settings():
    return render_template('settings.html', user=session.get('user'))


# 📤 Data Export Page
@frontend.route('/export-data')
@login_required
def export_data():
    return render_template('export_data.html', user=session.get('user'))


# 🚪 Logout Route
@frontend.route('/logout')
def logout():
    session.clear()
    response = make_response(redirect(url_for('frontend.login')))
    for header, value in NO_CACHE_HEADERS.items():
        response.headers[header] = value
    return response