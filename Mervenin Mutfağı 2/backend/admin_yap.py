import sqlite3

conn = sqlite3.connect('mervenin_mutfagi.db')
cursor = conn.cursor()

# Şifresini bildiğin kendi kullanıcı adın
hedef_kullanici = 'merve' 

# Rolü admin yapıyoruz
cursor.execute("UPDATE users SET role = 'admin' WHERE username = ?", (hedef_kullanici,))
conn.commit()

# Kontrol ediyoruz
cursor.execute("SELECT username, role FROM users WHERE username = ?", (hedef_kullanici,))
kullanici = cursor.fetchone()

if kullanici:
    print("Islem Basarili! Kullanici adi: " + str(kullanici[0]) + " -> Yeni Rolu: " + str(kullanici[1]))
else:
    print("HATA: Bu kullanici adina sahip bir hesap bulunamadi!")

conn.close()