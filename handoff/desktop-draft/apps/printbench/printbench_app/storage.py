from __future__ import annotations
import json
import os
import sqlite3
import sys
from pathlib import Path
from threading import RLock
import keyring


def data_dir():
    if sys.platform == 'win32':
        base = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData/Local'))
    elif sys.platform == 'darwin':
        base = Path.home() / 'Library/Application Support'
    else:
        base = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share'))
    return base / 'PRINTBENCH'


class Store:
    def __init__(self, root=None, vault=None):
        self.root = Path(root) if root else data_dir()
        self.root.mkdir(parents=True, exist_ok=True)
        if os.name != 'nt': self.root.chmod(0o700)
        self.vault = vault or keyring
        self.lock = RLock()
        self.db = sqlite3.connect(self.root / 'history.db', check_same_thread=False)
        self.db.execute('CREATE TABLE IF NOT EXISTS history(ts REAL, payload TEXT)')
        self.db.execute('CREATE TABLE IF NOT EXISTS commands(id TEXT PRIMARY KEY, ts REAL, result TEXT)')
        self.db.commit()

    def config(self):
        path = self.root / 'settings.json'
        return json.loads(path.read_text()) if path.exists() else {}

    def save(self, values):
        with self.lock:
            current = self.config()
            current.update(values)
            path = self.root / 'settings.json'
            tmp = path.with_suffix('.tmp')
            tmp.write_text(json.dumps(current, indent=2), encoding='utf-8')
            tmp.replace(path)

    def secret(self, name):
        return self.vault.get_password('PRINTBENCH', name)

    def set_secret(self, name, value):
        if value: self.vault.set_password('PRINTBENCH', name, value)
        else:
            try: self.vault.delete_password('PRINTBENCH', name)
            except keyring.errors.PasswordDeleteError: pass

    def record(self, ts, snapshot):
        with self.lock:
            self.db.execute('INSERT INTO history VALUES (?,?)', (ts, json.dumps(snapshot)))
            # Bound local retention; native slicer/project files remain outside this database.
            self.db.execute('DELETE FROM history WHERE rowid NOT IN (SELECT rowid FROM history ORDER BY rowid DESC LIMIT 20000)')
            self.db.commit()

    def history(self, limit=240):
        with self.lock:
            return [json.loads(row[0]) for row in self.db.execute('SELECT payload FROM history ORDER BY rowid DESC LIMIT ?', (limit,)).fetchall()[::-1]]

    def claim(self, command_id, ts):
        with self.lock:
            try:
                self.db.execute('INSERT INTO commands VALUES (?, ?, ?)', (command_id, ts, 'claimed'))
                self.db.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def result(self, command_id, result):
        with self.lock:
            self.db.execute('UPDATE commands SET result=? WHERE id=?', (result, command_id))
            self.db.commit()
