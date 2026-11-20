"""Run the local Karmolab prototype with SIRA contracts and private session history."""
import argparse
import json
import secrets
import threading
from functools import partial
from http.cookies import SimpleCookie
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID

from core.research_contracts import ResearchRequest, ProviderExecutionResult
from assessment import POLICY, POLICY_VERSION, CASES, assess
from store import Store
from ai_review import review

ASSESS_LOCK = threading.Lock()

ROOT = Path(__file__).resolve().parent

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, store, **kwargs):
        self.store = store
        super().__init__(*args, directory=str(ROOT / "dist"), **kwargs)

    def session(self):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie",""))
            value = cookie.get("karmolab")
            if value and len(value.value)==64 and all(c in "0123456789abcdef" for c in value.value):
                return value.value
        except Exception:
            pass
        self.new_cookie = secrets.token_hex(32)
        return self.new_cookie

    def respond(self, payload, code=200):
        encoded = json.dumps(payload,ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Content-Length",str(len(encoded)))
        self.send_header("Cache-Control","no-store")
        self.send_header("X-Content-Type-Options","nosniff")
        if getattr(self,"new_cookie",None):
            self.send_header("Set-Cookie",f"karmolab={self.new_cookie}; HttpOnly; SameSite=Strict; Path=/")
            self.new_cookie = None
        self.end_headers()
        self.wfile.write(encoded)

    def local_host(self):
        return self.headers.get("Host") in {
            f"127.0.0.1:{self.server.server_port}",f"localhost:{self.server.server_port}"
        }

    def do_GET(self):
        if not self.local_host():
            return self.respond({"error":"invalid_host"},403)
        path = urlsplit(self.path).path
        if path == "/api/policy":
            self.session()
            request = ResearchRequest("Customer service policy","local_policy",max_results=3)
            result = ProviderExecutionResult(status="completed",provider_id="karmolab.sample_policy",
                capability=request.capability,records=tuple(POLICY),resource_usage={"requests":0})
            return self.respond({"policy_version":POLICY_VERSION,"result":result.to_dict()})
        if path == "/api/history":
            return self.respond({"attempts":self.store.history(self.session())})
        if path.startswith("/api/"):
            return self.respond({"error":"not_found"},404)
        return super().do_GET()

    def do_POST(self):
        origin = self.headers.get("Origin")
        expected = f"http://{self.headers.get('Host')}"
        if not self.local_host() or (origin and origin != expected):
            return self.respond({"error":"invalid_origin"},403)
        if self.headers.get("Content-Type","").split(";")[0] != "application/json":
            return self.respond({"error":"json_required"},415)
        try:
            length = int(self.headers.get("Content-Length","0"))
            if not 0 < length <= 16000:
                raise ValueError("invalid_size")
            data = json.loads(self.rfile.read(length))
            if not isinstance(data,dict):
                raise ValueError("invalid_body")
            identifier = str(UUID(data.get("id","")))
            session = self.session()
            if self.path == "/api/assess":
                answer = data.get("answer")
                case_id = data.get("case_id")
                if not isinstance(answer,str) or not 1 <= len(answer.strip()) <= 1500 or case_id not in CASES:
                    raise ValueError("invalid_answer")
                with ASSESS_LOCK:
                    attempt = self.store.get(session, identifier)
                    if attempt:
                        if attempt['answer'] != answer.strip() or attempt['case_id'] != case_id:
                            raise ValueError('submission_id_conflict')
                    else:
                        result = review(answer.strip(),case_id,self.store.path.parent/'api-budget.sqlite3')
                        attempt = self.store.add(session,identifier,case_id,answer.strip(),result)
                return self.respond(attempt)
            if self.path == "/api/revision":
                revision = data.get("revision")
                if not isinstance(revision,str) or not 1 <= len(revision.strip()) <= 1500:
                    raise ValueError("invalid_revision")
                self.store.revise(session,identifier,revision.strip())
                return self.respond({"saved":True})
            if self.path == "/api/review":
                note = data.get("note")
                verdict = data.get("verdict")
                if not isinstance(note,str) or not 1 <= len(note.strip()) <= 1500 or verdict not in {"needs_practice","ready","pending"}:
                    raise ValueError("invalid_review")
                self.store.review(session,identifier,note.strip(),verdict)
                return self.respond({"saved":True})
            return self.respond({"error":"not_found"},404)
        except (ValueError,TypeError,AttributeError,RecursionError):
            return self.respond({"error":"invalid_request"},400)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port",type=int,default=8766)
    parser.add_argument("--data",type=Path,default=ROOT/"runtime"/"practice.sqlite3")
    args = parser.parse_args()
    store = Store(args.data)
    server = ThreadingHTTPServer(("127.0.0.1",args.port),partial(Handler,store=store))
    print(f"Karmolab http://127.0.0.1:{server.server_port}",flush=True)
    server.serve_forever()
