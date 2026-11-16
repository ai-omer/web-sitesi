import os
from database import SessionLocal, CommunityPost, UPLOADS_DIR

def clean_all_posts():
    db = SessionLocal()
    try:
        posts = db.query(CommunityPost).all()
        print(f"Toplam {len(posts)} gönderi bulundu.")
        
        # Gönderileri sil
        for p in posts:
            print(f"Siliniyor: ID {p.id} - User: {p.username}")
            # Eğer görseli varsa dosyayı da sil
            if p.image_path and os.path.exists(p.image_path):
                try:
                    os.remove(p.image_path)
                    print(f"  Görsel silindi: {os.path.basename(p.image_path)}")
                except Exception as e:
                    print(f"  Görsel silinemedi: {e}")
            db.delete(p)
        
        db.commit()
        print("Tüm gönderiler veritabanından başarıyla temizlendi!")
        
        # uploads klasöründeki kalan diğer dosyaları da temizle (opsiyonel)
        remaining_files = os.listdir(UPLOADS_DIR)
        if remaining_files:
            print(f"Uploads klasöründe sahipsiz {len(remaining_files)} dosya bulundu, temizleniyor...")
            for filename in remaining_files:
                file_path = os.path.join(UPLOADS_DIR, filename)
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                        print(f"  Temizlendi: {filename}")
                    except Exception as e:
                        print(f"  Temizlenemedi: {filename} - {e}")
                        
    except Exception as e:
        print(f"Hata oluştu: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clean_all_posts()
