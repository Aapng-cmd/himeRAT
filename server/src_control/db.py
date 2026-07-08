import json
import sqlite3
from datetime import datetime, timezone


def _utc_now() -> str:
  return datetime.now(timezone.utc).isoformat()


class ComputerDatabase:
  def __init__(self, db_name="computers.db"):
    self.conn = sqlite3.connect(db_name, check_same_thread=False)
    self.conn.row_factory = sqlite3.Row
    self.cursor = self.conn.cursor()
    self._init_schema()

  def _init_schema(self):
    self.cursor.execute(
      """
      CREATE TABLE IF NOT EXISTS computers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        system_hash TEXT UNIQUE,
        pid INTEGER,
        user TEXT,
        local_ip TEXT NOT NULL,
        hostname TEXT,
        os_info TEXT,
        kernel TEXT,
        status INTEGER DEFAULT 1,
        last_seen TEXT
      )
      """
    )
    self.cursor.execute(
      """
      CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        computer_id INTEGER NOT NULL,
        task_name TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TEXT,
        FOREIGN KEY (computer_id) REFERENCES computers(id)
      )
      """
    )
    self.cursor.execute(
      """
      CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        computer_id INTEGER NOT NULL,
        task_id INTEGER,
        task_name TEXT NOT NULL,
        result_json TEXT NOT NULL,
        created_at TEXT,
        FOREIGN KEY (computer_id) REFERENCES computers(id)
      )
      """
    )
    self._migrate_columns()
    self.conn.commit()

  def _migrate_columns(self):
    self.cursor.execute("PRAGMA table_info(computers)")
    cols = {row[1] for row in self.cursor.fetchall()}
    for col, typedef in [
      ("hostname", "TEXT"),
      ("os_info", "TEXT"),
      ("kernel", "TEXT"),
      ("last_seen", "TEXT"),
    ]:
      if col not in cols:
        self.cursor.execute(f"ALTER TABLE computers ADD COLUMN {col} {typedef}")

  def insert_computer(
    self,
    system_hash,
    pid,
    user,
    local_ip,
    hostname=None,
    os_info=None,
    kernel=None,
  ):
    try:
      self.cursor.execute(
        """
        INSERT INTO computers
          (system_hash, pid, user, local_ip, hostname, os_info, kernel, last_seen)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (system_hash, pid, user, local_ip, hostname, os_info, kernel, _utc_now()),
      )
      self.conn.commit()
      return self.cursor.lastrowid
    except sqlite3.IntegrityError:
      self.cursor.execute(
        "SELECT id FROM computers WHERE system_hash = ?",
        (system_hash,),
      )
      row = self.cursor.fetchone()
      if row:
        self.update_heartbeat(
          row["id"],
          hostname=hostname,
          os_info=os_info,
          kernel=kernel,
        )
        return row["id"]
      return None

  def update_heartbeat(self, computer_id, hostname=None, os_info=None, kernel=None):
    self.cursor.execute(
      """
      UPDATE computers
      SET last_seen = ?, hostname = COALESCE(?, hostname),
          os_info = COALESCE(?, os_info), kernel = COALESCE(?, kernel), status = 1
      WHERE id = ?
      """,
      (_utc_now(), hostname, os_info, kernel, computer_id),
    )
    self.conn.commit()

  def get_computers(self):
    self.cursor.execute("SELECT * FROM computers ORDER BY id DESC")
    return [dict(row) for row in self.cursor.fetchall()]

  def get_computer(self, computer_id):
    self.cursor.execute("SELECT * FROM computers WHERE id = ?", (computer_id,))
    row = self.cursor.fetchone()
    return dict(row) if row else None

  def enqueue_task(self, computer_id, task_name):
    self.cursor.execute(
      """
      INSERT INTO tasks (computer_id, task_name, status, created_at)
      VALUES (?, ?, 'pending', ?)
      """,
      (computer_id, task_name, _utc_now()),
    )
    self.conn.commit()
    return self.cursor.lastrowid

  def poll_task(self, computer_id):
    self.cursor.execute(
      """
      SELECT id, task_name FROM tasks
      WHERE computer_id = ? AND status = 'pending'
      ORDER BY id ASC LIMIT 1
      """,
      (computer_id,),
    )
    row = self.cursor.fetchone()
    if not row:
      return None
    self.cursor.execute(
      "UPDATE tasks SET status = 'running' WHERE id = ?",
      (row["id"],),
    )
    self.conn.commit()
    return {"task_id": row["id"], "task": row["task_name"]}

  def save_result(self, computer_id, task_id, task_name, result_dict):
    self.cursor.execute(
      """
      INSERT INTO results (computer_id, task_id, task_name, result_json, created_at)
      VALUES (?, ?, ?, ?, ?)
      """,
      (computer_id, task_id, task_name, json.dumps(result_dict), _utc_now()),
    )
    if task_id:
      self.cursor.execute(
        "UPDATE tasks SET status = 'done' WHERE id = ?",
        (task_id,),
      )
    self.conn.commit()
    return self.cursor.lastrowid

  def get_results(self, computer_id, limit=50):
    self.cursor.execute(
      """
      SELECT id, task_id, task_name, result_json, created_at
      FROM results WHERE computer_id = ?
      ORDER BY id DESC LIMIT ?
      """,
      (computer_id, limit),
    )
    rows = []
    for row in self.cursor.fetchall():
      item = dict(row)
      item["result"] = json.loads(item.pop("result_json"))
      rows.append(item)
    return rows

  def close(self):
    self.conn.close()
