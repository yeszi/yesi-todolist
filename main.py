import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import json
import os

# ===============================
# KONFIGURASI SUPABASE
# ===============================
SUPABASE_URL = "https://tzwgbrdsqzysvxndutmt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR6d2dicmRzcXp5c3Z4bmR1dG10Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI3NjM0NzUsImV4cCI6MjA3ODMzOTQ3NX0.GWBuHYUCRljZSJ3yLWhab7c2lzKfeLUuS7OwZKHWfwY"
BUCKET_NAME = "todos"
LOCAL_FILE = "todos_local.json"

# ===============================
# INISIALISASI SUPABASE
# ===============================
def init_supabase():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.warning(f"⚠️ Tidak bisa konek ke Supabase: {e}")
        return None

supabase: Client | None = init_supabase()

# ===============================
# FUNGSI BANTUAN
# ===============================
def load_local_todos():
    if os.path.exists(LOCAL_FILE):
        with open(LOCAL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"date": str(datetime.now().date()), "todos": [], "completed": []}

def save_local_todos(todos):
    with open(LOCAL_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, indent=2)

# ===============================
# FUNGSI SUPABASE
# ===============================
def load_todos():
    if supabase is None:
        st.info("📂 Menggunakan data lokal (offline mode)")
        return load_local_todos()
    try:
        response = supabase.storage.from_(BUCKET_NAME).download("todos.json")
        todos = json.loads(response.decode("utf-8"))
        save_local_todos(todos)
        return todos
    except Exception as e:
        st.warning(f"⚠️ Gagal load dari Supabase: {e}")
        return load_local_todos()

def save_todos(todos):
    save_local_todos(todos)
    if supabase is None:
        st.info("📂 Disimpan lokal (Supabase tidak terhubung).")
        return False
    try:
        json_data = json.dumps(todos, indent=2)
        supabase.storage.from_(BUCKET_NAME).upload(
            "todos.json",
            json_data.encode("utf-8"),
            {"content-type": "application/json", "upsert": "true"}
        )
        st.success("✅ Disimpan ke Supabase dan lokal.")
        return True
    except Exception as e:
        st.warning(f"⚠️ Gagal simpan ke Supabase: {e}")
        return False

# ===============================
# ANTARMUKA STREAMLIT
# ===============================
st.set_page_config(page_title="🗓️ To-Do List Manager", layout="centered")

st.title("🗓️ Daily To-Do List Manager")

todos = load_todos()

st.subheader("📋 Pending Tasks")
if not todos["todos"]:
    st.info("Tidak ada tugas pending.")
else:
    for i, t in enumerate(todos["todos"]):
        if st.checkbox(f"{t['task']} ({t['created_at']})", key=f"todo_{i}"):
            task = todos["todos"].pop(i)
            todos["completed"].append(task)
            save_todos(todos)
            st.experimental_rerun()

st.subheader("✅ Completed Tasks")
if not todos["completed"]:
    st.info("Belum ada tugas selesai.")
else:
    for t in todos["completed"]:
        st.write(f"- {t['task']}")

# Tambah tugas baru
st.subheader("➕ Tambah Tugas Baru")
task = st.text_input("Masukkan tugas baru:", key="new_task")

if st.button("Tambah"):
    if task.strip():
        new_todo = {
            "id": len(todos["todos"]) + 1,
            "task": task.strip(),
            "created_at": datetime.now().strftime("%H:%M:%S")
        }
        todos["todos"].append(new_todo)
        save_todos(todos)
        st.experimental_rerun()
    else:
        st.warning("⚠️ Tugas tidak boleh kosong.")
