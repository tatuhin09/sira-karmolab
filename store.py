"""Session-isolated local practice history with idempotent submissions."""
import json
import sqlite3
from contextlib import closing
from pathlib import Path

class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as db, db:
            db.execute("""CREATE TABLE IF NOT EXISTS attempts(
                id TEXT NOT NULL, session TEXT NOT NULL, case_id TEXT NOT NULL,
                answer TEXT NOT NULL, assessment TEXT NOT NULL,
                created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                note TEXT NOT NULL DEFAULT '', verdict TEXT NOT NULL DEFAULT 'pending',
                PRIMARY KEY(session,id))""")
            columns = {row[1] for row in db.execute("PRAGMA table_info(attempts)")}
            if "revision" not in columns:
                db.execute("ALTER TABLE attempts ADD COLUMN revision TEXT NOT NULL DEFAULT ''")

    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def get(self, session, identifier):
        with closing(self.connect()) as db, db:
            row = db.execute("SELECT * FROM attempts WHERE session=? AND id=?", (session, identifier)).fetchone()
        return self.decode(row) if row else None

    def add(self, session, identifier, case_id, answer, assessment):
        with closing(self.connect()) as db, db:
            db.execute("INSERT OR IGNORE INTO attempts(id,session,case_id,answer,assessment) VALUES(?,?,?,?,?)",
                       (identifier,session,case_id,answer,json.dumps(assessment,ensure_ascii=False)))
            row = db.execute("SELECT * FROM attempts WHERE session=? AND id=?",(session,identifier)).fetchone()
            if row["answer"] != answer or row["case_id"] != case_id:
                raise ValueError("submission_id_conflict")
            return self.decode(row)

    @staticmethod
    def decode(row):
        result = dict(row)
        result.pop("session")
        result["assessment"] = json.loads(result["assessment"])
        return result

    def history(self, session):
        with closing(self.connect()) as db, db:
            rows = db.execute("SELECT * FROM attempts WHERE session=? ORDER BY rowid DESC LIMIT 50",(session,)).fetchall()
        return [self.decode(row) for row in rows]

    def review(self, session, identifier, note, verdict):
        with closing(self.connect()) as db, db:
            cursor = db.execute("UPDATE attempts SET note=?,verdict=? WHERE session=? AND id=?",
                                (note,verdict,session,identifier))
            if not cursor.rowcount:
                raise ValueError("attempt_not_found")


    def revise(self, session, identifier, revision):
        with closing(self.connect()) as db, db:
            cursor = db.execute("UPDATE attempts SET revision=? WHERE session=? AND id=?",
                                (revision,session,identifier))
            if not cursor.rowcount:
                raise ValueError("attempt_not_found")
