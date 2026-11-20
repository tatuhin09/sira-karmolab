"""WSGI entry point for a single-instance HTTPS training demo."""
import json
import os
import secrets
import threading
from pathlib import Path
from uuid import UUID

from flask import Flask, g, jsonify, request, send_from_directory
from werkzeug.exceptions import BadRequest
from assessment import CASES, POLICY, POLICY_HASH, POLICY_VERSION
from ai_review import review
from store import Store
from core.research_contracts import ProviderExecutionResult

ROOT = Path(__file__).resolve().parent


def create_app(data_path=None, public_host=None):
    app = Flask(__name__, static_folder=None)
    app.config['MAX_CONTENT_LENGTH'] = 16000
    host = public_host if public_host is not None else os.getenv('KARMOLAB_PUBLIC_HOST', '')
    host = host.lower()
    data = Path(data_path or os.getenv('KARMOLAB_DATA_PATH', str(ROOT/'runtime'/'practice.sqlite3')))
    store = Store(data)
    lock = threading.Lock()

    def session_id():
        if not hasattr(g, 'practice_session'):
            value = request.cookies.get('karmolab', '')
            valid = len(value) == 64 and all(c in '0123456789abcdef' for c in value)
            g.practice_session = value if valid else secrets.token_hex(32)
            g.new_session = not valid
        return g.practice_session

    @app.before_request
    def boundary():
        name = request.host.partition(':')[0].lower()
        allowed = {host} if host else {'localhost', '127.0.0.1'}
        if name not in allowed:
            return jsonify(error='invalid_host'), 403
        if request.method == 'POST':
            expected = f'https://{host}' if host else f'http://{request.host}'
            if request.headers.get('Origin') not in (None, expected):
                return jsonify(error='invalid_origin'), 403
            if request.mimetype != 'application/json':
                return jsonify(error='json_required'), 415

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'same-origin'
        response.headers['X-Frame-Options'] = 'DENY'
        if request.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store'
        if getattr(g, 'new_session', False):
            response.set_cookie('karmolab', g.practice_session, httponly=True,
                                secure=bool(host), samesite='Strict', path='/')
        return response

    @app.get('/healthz')
    def health():
        return jsonify(status='ok', mode='training_demo')

    @app.get('/api/policy')
    def policy():
        session_id()
        return jsonify(policy_version=POLICY_VERSION, policy_hash=POLICY_HASH,
                       result=ProviderExecutionResult(status='completed', provider_id='karmolab.sample_policy',
                           capability='local_policy', records=tuple(POLICY)).to_dict(), demo=True)

    @app.get('/api/history')
    def history():
        return jsonify(attempts=store.history(session_id()))

    @app.post('/api/assess')
    @app.post('/api/revision')
    @app.post('/api/review')
    def mutate():
        try:
            payload = request.get_json()
            if not isinstance(payload, dict):
                raise ValueError('invalid_body')
            identifier = str(UUID(payload.get('id', '')))
            session = session_id()
            if request.path == '/api/assess':
                answer, case = payload.get('answer'), payload.get('case_id')
                if not isinstance(answer, str) or not 1 <= len(answer.strip()) <= 1500 or case not in CASES:
                    raise ValueError('invalid_answer')
                answer = answer.strip()
                with lock:
                    attempt = store.get(session, identifier)
                    if attempt:
                        if attempt['answer'] != answer or attempt['case_id'] != case:
                            raise ValueError('submission_id_conflict')
                    else:
                        result = review(answer, case, data.parent/'api-budget.sqlite3')
                        attempt = store.add(session, identifier, case, answer, result)
                return jsonify(attempt)
            if request.path == '/api/revision':
                text = payload.get('revision')
                if not isinstance(text, str) or not 1 <= len(text.strip()) <= 1500:
                    raise ValueError('invalid_revision')
                store.revise(session, identifier, text.strip())
            else:
                text, verdict = payload.get('note'), payload.get('verdict')
                if not isinstance(text, str) or not 1 <= len(text.strip()) <= 1500 or verdict not in {'pending','ready','needs_practice'}:
                    raise ValueError('invalid_review')
                store.review(session, identifier, text.strip(), verdict)
            return jsonify(saved=True)
        except (ValueError, TypeError, AttributeError, RecursionError, BadRequest):
            return jsonify(error='invalid_request'), 400

    @app.get('/')
    def index():
        return send_from_directory(ROOT/'dist', 'index.html')

    @app.get('/<path:filename>')
    def assets(filename):
        return send_from_directory(ROOT/'dist', filename)

    @app.errorhandler(413)
    def too_large(error):
        return jsonify(error='invalid_request'), 413

    return app


app = create_app()
