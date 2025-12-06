import sqlite3

DB_PATH = "instance\FlaskDataBase.db"   # ⚠️ để đúng đường dẫn DB của bạn

def grant_admin(username):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Kiểm tra user có tồn tại không
    cur.execute("SELECT id, username FROM user WHERE username = ?", (username,))
    user = cur.fetchone()

    if not user:
        print("❌ Không tìm thấy user:", username)
        conn.close()
        return

    # Cấp quyền admin
    cur.execute("UPDATE user SET is_admin = 1 WHERE username = ?", (username,))
    conn.commit()
    conn.close()

    print(f"✔️ Đã cấp quyền admin cho user: {username}")

if __name__ == "__main__":
    grant_admin("kera")     # ⚠️ sửa tên user vào đây
