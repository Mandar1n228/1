#!/usr/bin/env python3
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, render_template_string, request

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "app3.db"

app = Flask(__name__)

PAGE_TEMPLATE = """
<!doctype html>
<html lang="uk">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Контроль присвоєння рангу та спеціального звання</title>
  <style>
    :root {
      --bg: #f5f7fb;
      --card: #ffffff;
      --border: #d7dfeb;
      --text: #1f2a37;
      --muted: #5f6b7a;
      --green: #16a34a;
      --red: #dc2626;
      --yellow: #facc15;
      --yellow-text: #4d3c00;
      --blue: #2563eb;
    }
    * { box-sizing: border-box; }
    body { margin: 0; background: var(--bg); color: var(--text); font-family: Inter, Arial, sans-serif; }
    .container { width: min(1400px, 96vw); margin: 20px auto; }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 16px; box-shadow: 0 6px 20px rgba(15, 23, 42, 0.08); }
    h1 { margin: 0 0 12px; font-size: 1.35rem; }
    .notice { margin-bottom: 14px; padding: 10px 12px; border-radius: 10px; border: 1px solid #c7d3e3; background: #eef3fb; color: #1e40af; line-height: 1.5; }
    .toolbar { display: flex; justify-content: flex-end; margin-bottom: 10px; }
    .add-btn { border: none; background: var(--green); color: #fff; width: 34px; height: 34px; border-radius: 999px; font-size: 1.2rem; font-weight: 700; cursor: pointer; }
    .add-btn:hover { filter: brightness(1.05); }
    table { width: 100%; border-collapse: collapse; }
    th, td { border: 1px solid var(--border); padding: 8px; text-align: left; font-size: 0.92rem; }
    th { background: #ecf2fb; }
    tbody tr:nth-child(even) { background: #fafcff; }
    .actions { display: flex; gap: 6px; }
    .btn { border: none; padding: 6px 10px; border-radius: 8px; cursor: pointer; font-weight: 600; }
    .btn-edit { background: var(--yellow); color: var(--yellow-text); }
    .btn-del { background: var(--red); color: #fff; }
    .backdrop { position: fixed; inset: 0; display: none; align-items: flex-start; justify-content: center; background: rgba(10, 16, 30, 0.45); z-index: 2000; padding-top: 24px; }
    .backdrop.open { display: flex; }
    .modal { width: min(620px, 96vw); background: #fff; border-radius: 12px; border: 1px solid var(--border); padding: 14px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .field label { display: block; font-size: 0.85rem; margin-bottom: 4px; color: var(--muted); }
    .field input, .field textarea { width: 100%; border: 1px solid var(--border); border-radius: 8px; padding: 8px; }
    .date-wrap { display: flex; gap: 6px; align-items: center; }
    .date-wrap input[type="checkbox"] { width: auto; }
    .modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 12px; }
    .btn-save { background: var(--blue); color: #fff; }
    .btn-cancel { background: #e5e7eb; color: #111827; }
    @media (max-width: 900px) {
      .grid { grid-template-columns: 1fr; }
      table { font-size: 0.82rem; display: block; overflow-x: auto; white-space: nowrap; }
    }
  </style>
</head>
<body>
<div class="container">
  <div class="card">
    <h1>Контроль присвоєння рангу та спеціального звання</h1>
    <div id="notice" class="notice"></div>
    <div class="toolbar"><button class="add-btn" id="openCreate" type="button" title="Додати">+</button></div>
    <table>
      <thead>
        <tr>
          <th>№</th>
          <th>ПІБ</th>
          <th>Дата призначення на посаду</th>
          <th>Дата присвоєння рангу</th>
          <th>Черговий ранг</th>
          <th>Дата присвоєння спецзвання</th>
          <th>Чергове спецзвання</th>
          <th>Примітка</th>
          <th>Дії</th>
        </tr>
      </thead>
      <tbody id="rows"></tbody>
    </table>
  </div>
</div>

<div class="backdrop" id="modalBg">
  <div class="modal">
    <h3 id="modalTitle">Додати запис</h3>
    <form id="entryForm">
      <input type="hidden" id="entryId" />
      <div class="grid">
        <div class="field" style="grid-column:1/-1;">
          <label for="pib">ПІБ *</label>
          <input id="pib" required maxlength="255" />
        </div>
        <div class="field">
          <label for="appointment_date">Дата призначення на посаду *</label>
          <div class="date-wrap">
            <input id="appointment_date" type="date" required />
            <label><input id="appointment_dash" type="checkbox" /> прочерк</label>
          </div>
        </div>
        <div class="field">
          <label for="rank_date">Дата присвоєння рангу *</label>
          <div class="date-wrap">
            <input id="rank_date" type="date" required />
            <label><input id="rank_dash" type="checkbox" /> прочерк</label>
          </div>
        </div>
        <div class="field">
          <label for="special_date">Дата присвоєння спецзвання *</label>
          <div class="date-wrap">
            <input id="special_date" type="date" required />
            <label><input id="special_dash" type="checkbox" /> прочерк</label>
          </div>
        </div>
        <div class="field" style="grid-column:1/-1;">
          <label for="note">Примітка</label>
          <textarea id="note" rows="2" maxlength="500"></textarea>
        </div>
      </div>
      <div class="modal-actions">
        <button type="button" class="btn btn-cancel" id="cancelBtn">Скасувати</button>
        <button type="submit" class="btn btn-save">Зберегти</button>
      </div>
    </form>
  </div>
</div>

<script>
  const rows = document.getElementById('rows');
  const notice = document.getElementById('notice');
  const modalBg = document.getElementById('modalBg');
  const form = document.getElementById('entryForm');
  const title = document.getElementById('modalTitle');

  const fields = {
    id: document.getElementById('entryId'),
    pib: document.getElementById('pib'),
    appointment_date: document.getElementById('appointment_date'),
    rank_date: document.getElementById('rank_date'),
    special_date: document.getElementById('special_date'),
    note: document.getElementById('note'),
    appointment_dash: document.getElementById('appointment_dash'),
    rank_dash: document.getElementById('rank_dash'),
    special_dash: document.getElementById('special_dash'),
  };

  function setupDash(dateEl, dashEl) {
    dashEl.addEventListener('change', () => {
      if (dashEl.checked) {
        dateEl.value = '';
        dateEl.disabled = true;
        dateEl.required = false;
      } else {
        dateEl.disabled = false;
        dateEl.required = true;
      }
    });
  }

  setupDash(fields.appointment_date, fields.appointment_dash);
  setupDash(fields.rank_date, fields.rank_dash);
  setupDash(fields.special_date, fields.special_dash);

  function openModal(edit = false) {
    title.textContent = edit ? 'Редагувати запис' : 'Додати запис';
    modalBg.classList.add('open');
  }

  function closeModal() {
    modalBg.classList.remove('open');
    form.reset();
    fields.id.value = '';
    [
      [fields.appointment_date, fields.appointment_dash],
      [fields.rank_date, fields.rank_dash],
      [fields.special_date, fields.special_dash]
    ].forEach(([d, c]) => {
      d.disabled = false;
      d.required = true;
      c.checked = false;
    });
  }

  async function load() {
    const res = await fetch('/api/entries');
    const data = await res.json();

    notice.innerHTML = `${data.notice_current}<br>${data.notice_next}`;

    rows.innerHTML = '';
    data.entries.forEach((item) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${item.id}</td>
        <td>${item.pib}</td>
        <td>${item.appointment_date}</td>
        <td>${item.rank_date}</td>
        <td>${item.next_rank_date}</td>
        <td>${item.special_date}</td>
        <td>${item.next_special_date}</td>
        <td>${item.note || ''}</td>
        <td>
          <div class="actions">
            <button type="button" class="btn btn-edit" data-id="${item.id}">Редагувати</button>
            <button type="button" class="btn btn-del" data-del="${item.id}">Видалити</button>
          </div>
        </td>`;
      rows.appendChild(tr);
    });
  }

  document.getElementById('openCreate').addEventListener('click', () => openModal(false));
  document.getElementById('cancelBtn').addEventListener('click', closeModal);
  modalBg.addEventListener('click', (e) => { if (e.target === modalBg) closeModal(); });

  rows.addEventListener('click', async (e) => {
    const editId = e.target.getAttribute('data-id');
    const delId = e.target.getAttribute('data-del');

    if (editId) {
      const res = await fetch(`/api/entries/${editId}`);
      const item = await res.json();
      fields.id.value = item.id;
      fields.pib.value = item.pib;

      const dateFields = [
        ['appointment_date', 'appointment_dash'],
        ['rank_date', 'rank_dash'],
        ['special_date', 'special_dash']
      ];
      for (const [dateKey, dashKey] of dateFields) {
        if (item[dateKey] === '-') {
          fields[dashKey].checked = true;
          fields[dateKey].value = '';
          fields[dateKey].disabled = true;
          fields[dateKey].required = false;
        } else {
          fields[dashKey].checked = false;
          fields[dateKey].disabled = false;
          fields[dateKey].required = true;
          fields[dateKey].value = item[dateKey];
        }
      }
      fields.note.value = item.note || '';
      openModal(true);
    }

    if (delId) {
      if (!confirm('Видалити запис?')) return;
      await fetch(`/api/entries/${delId}`, { method: 'DELETE' });
      await load();
    }
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      pib: fields.pib.value.trim(),
      appointment_date: fields.appointment_dash.checked ? '-' : fields.appointment_date.value,
      rank_date: fields.rank_dash.checked ? '-' : fields.rank_date.value,
      special_date: fields.special_dash.checked ? '-' : fields.special_date.value,
      note: fields.note.value.trim(),
    };

    if (!payload.pib || !payload.appointment_date || !payload.rank_date || !payload.special_date) {
      alert('Заповніть обов\'язкові поля. Для дати можна обрати прочерк.');
      return;
    }

    const id = fields.id.value;
    const method = id ? 'PUT' : 'POST';
    const url = id ? `/api/entries/${id}` : '/api/entries';

    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json();
      alert(err.error || 'Помилка збереження');
      return;
    }

    closeModal();
    await load();
  });

  load();
</script>
</body>
</html>
"""


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pib TEXT NOT NULL,
                appointment_date TEXT NOT NULL,
                rank_date TEXT NOT NULL,
                special_date TEXT NOT NULL,
                note TEXT DEFAULT ''
            )
            """
        )


def parse_date(value: str) -> Optional[date]:
    if not value or value.strip() == "-":
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def add_years(dt: date, years: int) -> date:
    try:
        return dt.replace(year=dt.year + years)
    except ValueError:
        return dt.replace(month=2, day=28, year=dt.year + years)


def week_bounds(base: date) -> tuple[date, date]:
    start = base - timedelta(days=base.weekday())
    end = start + timedelta(days=6)
    return start, end


def in_range(dt: date, start: date, end: date) -> bool:
    return start <= dt <= end


def serialize_row(row: sqlite3.Row) -> dict:
    rank_dt = parse_date(row["rank_date"])
    special_dt = parse_date(row["special_date"])
    return {
        "id": row["id"],
        "pib": row["pib"],
        "appointment_date": row["appointment_date"],
        "rank_date": row["rank_date"],
        "next_rank_date": add_years(rank_dt, 3).isoformat() if rank_dt else "-",
        "special_date": row["special_date"],
        "next_special_date": add_years(special_dt, 2).isoformat() if special_dt else "-",
        "note": row["note"],
    }


def build_notice(entries: list[dict]) -> tuple[str, str]:
    today = date.today()
    cur_start, cur_end = week_bounds(today)
    next_start = cur_start + timedelta(days=7)
    next_end = next_start + timedelta(days=6)

    current_hits = []
    next_hits = []

    for item in entries:
        for kind, key in (("ранг", "next_rank_date"), ("спецзвання", "next_special_date")):
            value = item[key]
            if value == "-":
                continue
            dt = parse_date(value)
            if not dt:
                continue
            text = f"{item['pib']} — {dt.isoformat()} ({kind})"
            if in_range(dt, cur_start, cur_end):
                current_hits.append(text)
            elif in_range(dt, next_start, next_end):
                next_hits.append(text)

    if current_hits:
        current_line = "Цього тижня зміни: " + "; ".join(current_hits)
    else:
        current_line = "На цьому тижні нових призначень немає."

    if next_hits:
        next_line = "Наступного тижня очікуються: " + "; ".join(next_hits)
    elif not current_hits:
        next_line = "У найближчі два тижні призначень немає."
    else:
        next_line = "Наступного тижня призначень немає."

    return current_line, next_line


def validate_payload(data: dict) -> Optional[str]:
    required = ["pib", "appointment_date", "rank_date", "special_date"]
    for key in required:
        val = str(data.get(key, "")).strip()
        if not val:
            return f"Поле {key} є обов'язковим"
        if key != "pib" and val != "-":
            if parse_date(val) is None:
                return f"Поле {key} має бути датою YYYY-MM-DD або '-'"
    return None


@app.route("/")
def index():
    return render_template_string(PAGE_TEMPLATE)


@app.get("/api/entries")
def list_entries():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM entries ORDER BY pib COLLATE NOCASE ASC, id ASC").fetchall()
    entries = [serialize_row(r) for r in rows]
    notice_current, notice_next = build_notice(entries)
    return jsonify({"entries": entries, "notice_current": notice_current, "notice_next": notice_next})


@app.get("/api/entries/<int:entry_id>")
def get_entry(entry_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
    if not row:
        return jsonify({"error": "Запис не знайдено"}), 404
    return jsonify(serialize_row(row))


@app.post("/api/entries")
def create_entry():
    data = request.get_json(silent=True) or {}
    err = validate_payload(data)
    if err:
        return jsonify({"error": err}), 400

    with get_conn() as conn:
        conn.execute(
            "INSERT INTO entries (pib, appointment_date, rank_date, special_date, note) VALUES (?, ?, ?, ?, ?)",
            (
                data["pib"].strip(),
                data["appointment_date"].strip(),
                data["rank_date"].strip(),
                data["special_date"].strip(),
                str(data.get("note", "")).strip(),
            ),
        )
    return jsonify({"ok": True}), 201


@app.put("/api/entries/<int:entry_id>")
def update_entry(entry_id: int):
    data = request.get_json(silent=True) or {}
    err = validate_payload(data)
    if err:
        return jsonify({"error": err}), 400

    with get_conn() as conn:
        cur = conn.execute(
            """
            UPDATE entries
            SET pib = ?, appointment_date = ?, rank_date = ?, special_date = ?, note = ?
            WHERE id = ?
            """,
            (
                data["pib"].strip(),
                data["appointment_date"].strip(),
                data["rank_date"].strip(),
                data["special_date"].strip(),
                str(data.get("note", "")).strip(),
                entry_id,
            ),
        )
    if cur.rowcount == 0:
        return jsonify({"error": "Запис не знайдено"}), 404
    return jsonify({"ok": True})


@app.delete("/api/entries/<int:entry_id>")
def delete_entry(entry_id: int):
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    if cur.rowcount == 0:
        return jsonify({"error": "Запис не знайдено"}), 404
    return jsonify({"ok": True})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5004, debug=False)
else:
    init_db()
