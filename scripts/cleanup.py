"""Run periodically even when the web service has no visitors."""
import os
import sqlite3
import time
from pathlib import Path
path=Path(os.environ.get('DB_PATH','data/mood.sqlite')).resolve()
if not path.is_file():
    raise SystemExit('Database does not exist; cleanup did not create one')
db=sqlite3.connect(path)
try:
    db.execute('PRAGMA foreign_keys=ON')
    with db:
        db.execute('DELETE FROM sessions WHERE expires<=?',(int(time.time()),))
        db.execute('DELETE FROM rate_limits WHERE reset_at<=?',(int(time.time()),))
finally:
    db.close()
