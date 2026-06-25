import os
import json
import glob
import sys
from pathlib import Path
from datetime import datetime

# Add project root to sys.path so we can import my_agent
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from my_agent.core.rag_engine import RAGManager

def find_all_output_dirs(base_paths=[r"d:\agent", r"d:\tuyen_sinh_project"]):
    """Tìm tất cả các thư mục output_... và output_pdf_... (chống trùng theo tên thư mục)."""
    found_dirs = []
    seen_basenames = set()
    for base in base_paths:
        if not os.path.exists(base):
            continue
        dirs1 = glob.glob(os.path.join(base, "output_*"))
        dirs2 = glob.glob(os.path.join(base, "output_pdf_*"))
        for d in dirs1 + dirs2:
            if os.path.isdir(d) and not d.endswith(".zip") and "processed" not in d:
                basename = os.path.basename(d).lower()
                if basename not in seen_basenames:
                    seen_basenames.add(basename)
                    found_dirs.append(os.path.abspath(d))
    return found_dirs

def load_json_documents(data_path):
    """Đọc tệp JSON và trích xuất cấu trúc văn bản kèm Metadata."""
    documents = []
    
    # Duyệt file
    for root, dirs, files in os.walk(data_path):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        
                        text = data.get("text", "").strip()
                        if not text or len(text) < 50:
                            continue
                            
                        # Trích xuất metadata JSON của crawler
                        raw_meta = data.get("metadata", {})
                        
                        # Chuyển đổi metadata sang chuẩn LanceDB engine
                        # Lấy năm từ created_at
                        year = datetime.now().year
                        if "created_at" in raw_meta:
                            try:
                                dt = datetime.fromisoformat(raw_meta["created_at"])
                                year = dt.year
                            except:
                                pass
                                
                        meta = {
                            "year": year,
                            "university_code": raw_meta.get("university_code", ""),
                            "university_name": raw_meta.get("university_name", ""),
                            "source_url": raw_meta.get("source_url", "")
                        }
                        
                        documents.append({
                            "text": text,
                            "metadata": meta
                        })
                        
                except Exception as e:
                    print(f"Lỗi đọc {file}: {e}", flush=True)
                    
    return documents

def main():
    topic = "admissions"
    
    print(f"\n--- BẮT ĐẦU NẠP DỮ LIỆU TUYỂN SINH TỰ ĐỘNG ---", flush=True)
    data_paths = find_all_output_dirs()
    
    if not data_paths:
        print("❌ Không tìm thấy thư mục dữ liệu 'output_...' hay 'output_pdf_...' nào.", flush=True)
        return
        
    print(f"Các thư mục tìm thấy: {data_paths}", flush=True)
    
    # 1. Tải văn bản cấu trúc JSON từ tất cả các thư mục
    all_documents = []
    for path in data_paths:
        print(f"Đang tải dữ liệu từ: {path}", flush=True)
        docs = load_json_documents(path)
        print(f"-> Trích xuất thành công {len(docs)} tài liệu.", flush=True)
        all_documents.extend(docs)
        
    if not all_documents:
        print("❌ Không tìm thấy dữ liệu văn bản hợp lệ trong bất kỳ thư mục nào.", flush=True)
        return
    
    print(f"Tổng số tài liệu trích xuất unique: {len(all_documents)} với Metadata. Chuẩn bị Semantic Chunking.", flush=True)
    
    # 2. Khởi tạo RAG Engine và xóa bảng cũ trước khi nạp mới
    engine = RAGManager()
    db = engine.get_db_connection(topic)
    table_name = f"{topic}_data"
    
    # Sử dụng list_tables() thay cho table_names() bị deprecated
    if table_name in db.list_tables():
        print(f"--- Đang làm sạch bảng cũ '{table_name}' để nạp mới hoàn toàn ---", flush=True)
        db.drop_table(table_name)
        
    # 3. Nạp tài liệu bằng phương pháp append_documents (chia batch nhỏ để in log real-time)
    print(f"\n--- Đang thực hiện Vector Embedding và ghi CSDL ---", flush=True)
    try:
        # Nạp với doc_batch_size=10 để in log tiến độ sau mỗi 10 tài liệu
        total_chunks = engine.append_documents(all_documents, topic, doc_batch_size=10)
        print(f"\n✅ THÀNH CÔNG! Đã nạp thành công {total_chunks} chunks vào CSDL '{topic}'.", flush=True)
    except Exception as e:
        print(f"Lỗi quá trình tạo index: {e}", flush=True)

if __name__ == "__main__":
    main()
