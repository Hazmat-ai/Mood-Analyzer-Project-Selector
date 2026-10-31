"""Same-origin Flask API and production frontend. Use gunicorn 'app:create_app()'."""
import hashlib
import hmac
import ipaddress
import json
import os
import re
import secrets
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from flask import Flask, g, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException
from backend.catalog import PROJECT_BANKS, PROJECTS, public_project
from backend.database import initialize, get_db, close_db
from models.specialty_data import SPECIALTIES
from models.quiz_data import QUESTIONS
from models.mood_axes import describe_mood
from logic.scoring import calculate_mood
from logic.matcher import get_candidates, spin_wheel, describe_match_reason

TOKEN = re.compile(r'^[a-f0-9]{64}$')
KEY = re.compile(r'^[a-zA-Z0-9_-]{16,80}$')
TTL = 30 * 86400

def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()

def create_app(config=None):
    app = Flask(__name__, static_folder=None)
    production = os.environ.get('APP_ENV') == 'production'
    app.config.update(
        DATABASE=os.environ.get('DB_PATH', 'data/mood.sqlite'),
        APP_ORIGIN=os.environ.get('APP_ORIGIN', 'http://localhost:5000'),
        PRODUCTION=production, PROXY_TOKEN=os.environ.get('PROXY_TOKEN', ''),
        RATE_LIMIT=180, SESSION_CREATION_LIMIT=30, MAX_CONTENT_LENGTH=4096,
        FRONTEND_DIST=str(Path(__file__).parent / 'frontend' / 'dist'),
    )
    if config:
        app.config.update(config)
    origin = app.config['APP_ORIGIN']
    parsed = urlsplit(origin)
    if parsed.scheme not in ('http', 'https') or origin != f'{parsed.scheme}://{parsed.netloc}' or not parsed.hostname or parsed.username or parsed.password:
        raise RuntimeError('APP_ORIGIN must be a canonical HTTP(S) origin')
    if app.config['PRODUCTION'] and (parsed.scheme != 'https' or (production and not os.environ.get('APP_ORIGIN') and not config)):
        raise RuntimeError('Production requires an explicit HTTPS APP_ORIGIN')
    proxy_token = app.config['PROXY_TOKEN']
    if proxy_token and not TOKEN.fullmatch(proxy_token):
        raise RuntimeError('PROXY_TOKEN must be 64 lowercase hexadecimal characters')
    initialize(app.config['DATABASE'])
    app.teardown_appcontext(close_db)
    cookie_name = '__Host-mood' if app.config['PRODUCTION'] else 'mood_session'
    allowed_origins = {origin}
    if not app.config['PRODUCTION']:
        allowed_origins.add('http://localhost:5173')

    def fail(code, status):
        return jsonify(error=code, request_id=g.request_id), status

    def body(fields):
        if request.mimetype != 'application/json':
            return None, fail('JSON_REQUIRED', 415)
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or set(data) != set(fields):
            return None, fail('INVALID_BODY', 400)
        return data, None

    @app.before_request
    def protect():
        g.request_id = str(uuid.uuid4())
        g.viewer = None
        if request.host != parsed.netloc:
            return fail('INVALID_HOST', 421)
        if not request.path.startswith('/api/'):
            return None
        if request.headers.get('Sec-Fetch-Site') == 'cross-site':
            return fail('CROSS_SITE', 403)
        supplied_origin = request.headers.get('Origin')
        if supplied_origin and supplied_origin not in allowed_origins:
            return fail('INVALID_ORIGIN', 403)
        db = get_db()
        now = int(time.time())
        if request.path == '/api/health' and request.method == 'GET':
            return None
        ip = request.remote_addr or 'unknown'
        forwarded = request.headers.get('X-Real-IP', '')
        provided_token = request.headers.get('X-Mood-Proxy-Token', '')
        if proxy_token and TOKEN.fullmatch(provided_token) and hmac.compare_digest(provided_token, proxy_token):
            try:
                ip = str(ipaddress.ip_address(forwarded))
            except ValueError:
                pass
        g.ip_hash = digest(ip)
        with db:
            db.execute('DELETE FROM sessions WHERE expires <= ?', (now,))
            db.execute('DELETE FROM rate_limits WHERE reset_at <= ?', (now,))
            db.execute('INSERT INTO rate_limits VALUES (?, ?, 0, 0) ON CONFLICT(ip_hash) DO NOTHING', (g.ip_hash, now + 60))
            db.execute('UPDATE rate_limits SET requests=requests+1 WHERE ip_hash=?', (g.ip_hash,))
            count = db.execute('SELECT requests FROM rate_limits WHERE ip_hash=?', (g.ip_hash,)).fetchone()[0]
        if count > app.config['RATE_LIMIT']:
            response, status = fail('RATE_LIMIT', 429)
            response.headers['Retry-After'] = '60'
            return response, status
        raw = request.cookies.get(cookie_name, '')
        if TOKEN.fullmatch(raw):
            g.viewer = db.execute('SELECT * FROM sessions WHERE id=? AND expires>?', (digest(raw), now)).fetchone()
        public = request.path in ('/api/session', '/api/quiz', '/api/specialties') and request.method == 'GET'
        if not public and g.viewer is None:
            return fail('SESSION_REQUIRED', 401)
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            csrf = request.headers.get('X-CSRF-Token', '')
            if supplied_origin not in allowed_origins or not TOKEN.fullmatch(csrf) or not hmac.compare_digest(csrf, g.viewer['csrf']):
                return fail('CSRF_INVALID', 403)
        return None

    @app.after_request
    def headers(response):
        response.headers.update({
            'X-Request-Id': getattr(g, 'request_id', str(uuid.uuid4())),
            'X-Content-Type-Options': 'nosniff', 'X-Frame-Options': 'DENY',
            'Referrer-Policy': 'no-referrer', 'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
            'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'; object-src 'none'",
        })
        if request.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store'
        if app.config['PRODUCTION']:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000'
        return response

    @app.errorhandler(HTTPException)
    def http_error(error):
        return fail(error.name.upper().replace(' ', '_'), error.code)

    @app.errorhandler(Exception)
    def unexpected(error):
        app.logger.error('Request failed request_id=%s error_type=%s', g.request_id, type(error).__name__)
        return fail('INTERNAL_ERROR', 500)

    @app.get('/api/health')
    def health():
        get_db().execute('SELECT 1').fetchone()
        return jsonify(status='ok')

    @app.get('/api/session')
    def session():
        if g.viewer is not None:
            return jsonify(csrf_token=g.viewer['csrf'], expires_at=g.viewer['expires'])
        db = get_db()
        raw, csrf, expires = secrets.token_hex(32), secrets.token_hex(32), int(time.time()) + TTL
        with db:
            changed = db.execute('UPDATE rate_limits SET creations=creations+1 WHERE ip_hash=? AND creations<?', (g.ip_hash, app.config['SESSION_CREATION_LIMIT'])).rowcount
            if not changed:
                response, status = fail('SESSION_RATE_LIMIT', 429)
                response.headers['Retry-After'] = '60'
                return response, status
            db.execute('INSERT INTO sessions VALUES (?, ?, ?)', (digest(raw), csrf, expires))
        response = jsonify(csrf_token=csrf, expires_at=expires)
        response.set_cookie(cookie_name, raw, max_age=TTL, httponly=True, secure=app.config['PRODUCTION'], samesite='Strict', path='/')
        return response

    @app.get('/api/specialties')
    def specialties():
        return jsonify(SPECIALTIES)

    @app.get('/api/quiz')
    def quiz():
        return jsonify([{'id':q['id'], 'text':q['text'], 'options':[{'label':o['label']} for o in q['options']]} for q in QUESTIONS])

    @app.post('/api/submit-quiz')
    def submit():
        data, error = body(('specialty', 'answer_indexes', 'difficulty'))
        if error:
            return error
        specialty, answers, difficulty = data['specialty'], data['answer_indexes'], data['difficulty']
        if not isinstance(specialty, str) or specialty not in PROJECT_BANKS or difficulty not in ('easy', 'medium', 'hard'):
            return fail('INVALID_SELECTION', 400)
        if not isinstance(answers, list) or len(answers) != len(QUESTIONS) or any(type(i) is not int or i < 0 or i >= len(q['options']) for i, q in zip(answers, QUESTIONS)):
            return fail('INVALID_ANSWERS', 400)
        key = request.headers.get('Idempotency-Key', '')
        if not KEY.fullmatch(key):
            return fail('IDEMPOTENCY_KEY_REQUIRED', 400)
        payload_hash = hmac.new(request.cookies[cookie_name].encode(), json.dumps(data, sort_keys=True, separators=(',', ':')).encode(), hashlib.sha256).hexdigest()
        mood = calculate_mood([q['options'][i]['effect'] for i,q in zip(answers, QUESTIONS)])
        candidates = get_candidates(mood, difficulty, PROJECT_BANKS[specialty], pool_size=5)
        if not candidates:
            return fail('NO_CANDIDATES', 404)
        db = get_db()
        with db:
            db.execute('BEGIN IMMEDIATE')
            existing = db.execute('SELECT * FROM picks WHERE session_id=? AND request_key=?', (g.viewer['id'], key)).fetchone()
            if existing:
                if existing['payload_hash'] != payload_hash:
                    return fail('IDEMPOTENCY_CONFLICT', 409)
                result = PROJECTS.get(existing['project_id'])
                if result is None:
                    return fail('PROJECT_REMOVED', 409)
                pick_id = existing['id']
            else:
                result = spin_wheel(candidates, mood)
                pick_id = str(uuid.uuid4())
                db.execute('INSERT INTO picks(id,session_id,project_id,project_title,specialty,difficulty,timestamp,request_key,payload_hash) VALUES (?,?,?,?,?,?,?,?,?)', (pick_id,g.viewer['id'],result['id'],result['title'],specialty,difficulty,int(time.time()),key,payload_hash))
                db.execute('DELETE FROM picks WHERE session_id=? AND id NOT IN (SELECT id FROM picks WHERE session_id=? ORDER BY timestamp DESC, rowid DESC LIMIT 200)', (g.viewer['id'],g.viewer['id']))
        return jsonify(pick_id=pick_id, completed=bool(existing['completed']) if existing else False, mood_vector=mood, mood_description=describe_mood(mood), candidates=[{'id':p['id'],'title':p['title']} for p in candidates], result=public_project(result), reason=describe_match_reason(mood, result))

    def history_rows():
        rows = get_db().execute('SELECT id,project_id,project_title,specialty,difficulty,timestamp,completed FROM picks WHERE session_id=? ORDER BY timestamp DESC, rowid DESC LIMIT 200', (g.viewer['id'],)).fetchall()
        return [{**dict(row), 'completed':bool(row['completed']), 'timestamp':datetime.fromtimestamp(row['timestamp'],timezone.utc).isoformat()} for row in rows]

    @app.get('/api/picks/<pick_id>')
    def saved_pick(pick_id):
        row = get_db().execute('SELECT * FROM picks WHERE id=? AND session_id=?', (pick_id,g.viewer['id'])).fetchone()
        if row is None:
            return fail('PICK_NOT_FOUND', 404)
        project = PROJECTS.get(row['project_id'])
        if project is None:
            return fail('PROJECT_REMOVED', 404)
        return jsonify(pick_id=row['id'], result=public_project(project), completed=bool(row['completed']), reason='Reopened from your project history.')

    @app.get('/api/history')
    def history():
        return jsonify(history_rows())

    @app.post('/api/complete')
    def complete():
        data, error = body(('pick_id',))
        if error:
            return error
        if not isinstance(data['pick_id'], str) or len(data['pick_id']) > 80:
            return fail('INVALID_PICK', 400)
        with get_db() as db:
            updated = db.execute('UPDATE picks SET completed=1 WHERE id=? AND session_id=?', (data['pick_id'],g.viewer['id'])).rowcount
        return jsonify(status='ok') if updated else fail('PICK_NOT_FOUND', 404)

    @app.get('/api/export')
    def export():
        return jsonify(version=1, picks=history_rows())

    @app.delete('/api/history')
    def delete_history():
        with get_db() as db:
            db.execute('DELETE FROM picks WHERE session_id=?', (g.viewer['id'],))
        return jsonify(deleted=True)

    @app.delete('/api/session')
    def delete_session():
        with get_db() as db:
            db.execute('DELETE FROM sessions WHERE id=?', (g.viewer['id'],))
        response = jsonify(deleted=True)
        response.delete_cookie(cookie_name, path='/', secure=app.config['PRODUCTION'], httponly=True, samesite='Strict')
        return response

    @app.route('/', defaults={'path':''})
    @app.route('/<path:path>')
    def frontend(path):
        if path.startswith('api/') or path == 'api':
            return fail('NOT_FOUND', 404)
        root = Path(app.config['FRONTEND_DIST']).resolve()
        target = (root / path).resolve()
        if not target.is_relative_to(root) or '\\' in path:
            return fail('INVALID_PATH', 400)
        if target.is_file():
            return send_from_directory(root, path, max_age=31536000 if path.startswith('assets/') else 0)
        if '.' in Path(path).name:
            return fail('NOT_FOUND', 404)
        return send_from_directory(root, 'index.html', max_age=0)
    return app

if __name__ == '__main__':
    create_app().run(host='localhost', port=5000, debug=False)
