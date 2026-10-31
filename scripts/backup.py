"""Create a consistent SQLite snapshot without copying a live WAL file."""
import argparse
import os
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

def backup(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if not source.is_file():
        raise ValueError('Source database does not exist')
    if destination.exists():
        raise ValueError('Refusing to overwrite an existing backup')
    os.umask(0o077)
    destination.parent.mkdir(parents=True,exist_ok=True)
    src=sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)
    dst=sqlite3.connect(destination)
    try:
        src.backup(dst)
        if dst.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
            raise RuntimeError('Backup integrity check failed')
    finally:
        src.close(); dst.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',default=os.environ.get('DB_PATH','data/mood.sqlite'))
    parser.add_argument('--destination',default='backups/mood-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.sqlite')
    args=parser.parse_args()
    backup(args.source,args.destination)
    print('Backup created:',args.destination)
