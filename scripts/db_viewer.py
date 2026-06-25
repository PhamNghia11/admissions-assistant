import os
import sys
import io
import lancedb

# Thiết lập encoding console để in tiếng Việt mượt mà trên Windows
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass

def view_records(limit=3):
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "my_agent", "data", "admissions"))
    table_name = "admissions_data"
    
    if not os.path.exists(db_path):
        print(f"Error: Database folder '{db_path}' does not exist.")
        return
        
    try:
        db = lancedb.connect(db_path)
        table = db.open_table(table_name)
        df = table.to_pandas()
        
        # Lấy tham số mã trường từ dòng lệnh (nếu có)
        uni_code = sys.argv[1].upper() if len(sys.argv) > 1 else None
        
        if uni_code == "ALL":
            title = "HIỂN THỊ DỮ LIỆU TẤT CẢ CÁC TRƯỜNG TRONG CƠ SỞ DỮ LIỆU (Xem 5 bản ghi/trường)"
            print("\n" + "="*85)
            print(title)
            print("="*85)
            
            for code in df['university_code'].unique():
                school_df = df[df['university_code'] == code].head(limit)
                school_name = school_df.iloc[0].get('university_name') if not school_df.empty else code
                total_school_records = len(df[df['university_code'] == code])
                
                print(f"\n🏫 TRƯỜNG: {school_name} ({code}) - Xem {len(school_df)}/{total_school_records} bản ghi:")
                print("-"*85)
                for idx, row in school_df.iterrows():
                    text_preview = row['text']
                    if len(text_preview) > 250:
                        text_preview = text_preview[:250] + "..."
                    print(f"   📍 Bản ghi #{idx + 1}:")
                    print(f"      Nguồn:    {row.get('source_url') or row.get('source_name')}")
                    print(f"      Nội dung: {text_preview}")
                    print("      " + "-"*60)
            print("="*85)
            return
            
        elif uni_code:
            # Lọc theo mã trường cụ thể
            filtered_df = df[df['university_code'].str.upper() == uni_code]
            if filtered_df.empty:
                print(f"❌ Không tìm thấy trường nào có mã: {uni_code}")
                return
            df_to_show = filtered_df.head(limit)
            title = f"XEM DỮ LIỆU TRƯỜNG {uni_code} (Hiển thị {len(df_to_show)}/{len(filtered_df)} bản ghi)"
        else:
            # Hiển thị mẫu 2 bản ghi đầu tiên của mỗi trường
            df_to_show = df.groupby('university_code').head(2)
            title = "MẪU DỮ LIỆU TUYỂN SINH CỦA CÁC TRƯỜNG TRONG CƠ SỞ DỮ LIỆU"
            
        print("\n" + "="*85)
        print(title)
        print("="*85)
        
        for idx, row in df_to_show.iterrows():
            print(f"\n📍 Bản ghi #{idx + 1} (Mã trường: {row.get('university_code')}):")
            print(f"   - Trường:    {row.get('university_name')}")
            print(f"   - Nguồn:     {row.get('source_url') or row.get('source_name')}")
            text_preview = row['text']
            if len(text_preview) > 350:
                text_preview = text_preview[:350] + "..."
            print(f"   - Nội dung tri thức:\n     {text_preview}")
            print("-"*85)
            
        if not uni_code:
            print("\n💡 Gợi ý: Bạn có thể chạy kèm mã trường để xem nhiều dữ liệu hơn:")
            print("   .venv\\Scripts\\python.exe scripts/db_viewer.py GDU")
            print("   .venv\\Scripts\\python.exe scripts/db_viewer.py BKA")
            print("   .venv\\Scripts\\python.exe scripts/db_viewer.py BMU")
            print("   .venv\\Scripts\\python.exe scripts/db_viewer.py BUV")
            print("="*85)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    view_records()
