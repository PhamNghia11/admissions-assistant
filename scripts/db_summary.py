import os
import sys
import io
import lancedb

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass

def summary():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "my_agent", "data", "admissions"))
    table_name = "admissions_data"
    
    if not os.path.exists(db_path):
        print(f"Error: Database folder '{db_path}' does not exist.")
        return
        
    try:
        db = lancedb.connect(db_path)
        table = db.open_table(table_name)
        df = table.to_pandas()
        
        print("\n" + "="*85)
        print("THONG KE DU LIEU TRONG DATABASE TUYEN SINH (LANCEDB)")
        print("="*85)
        print(f"Tong so doan tri thuc (chunks): {len(df)}")
        print("-"*85)
        
        if 'university_name' in df.columns:
            grouped = df.groupby(['university_name', 'university_code']).size().reset_index(name='chunks_count')
            print(f"{'STT':<4} | {'Ten Truong Dai Hoc':<45} | {'Ma Truong':<10} | {'So Chunks':<10}")
            print("-"*85)
            for idx, row in grouped.iterrows():
                uni_name = row['university_name'] if row['university_name'] else "Chua phan loai"
                uni_code = row['university_code'] if row['university_code'] else "N/A"
                count = row['chunks_count']
                # Clean up accents to prevent any console encoding errors
                print(f"{idx + 1:<4} | {uni_name:<45} | {uni_code:<10} | {count:<10}")
        else:
            print("Cơ sở dữ liệu đang dùng định dạng cũ, không chứa trường phân loại trường học.")
            
        print("="*85)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    summary()
