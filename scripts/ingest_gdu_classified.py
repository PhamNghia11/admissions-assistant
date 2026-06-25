import os
import sys
import io
import re
import pandas as pd
from pathlib import Path

# Add project root to sys.path
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from my_agent.core.rag_engine import RAGManager
from pypdf import PdfReader
import docx

# Custom safe print helper to handle Windows encoding issues without crashing
def safe_print(text):
    try:
        sys.stdout.buffer.write((str(text) + "\n").encode("utf-8"))
        sys.stdout.buffer.flush()
    except Exception:
        try:
            print(str(text))
        except Exception:
            pass

# Robust text reader that tries multiple encodings
def read_text_file(file_path):
    encodings = ["utf-8", "utf-8-sig", "utf-16", "windows-1258", "latin-1"]
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    # Ultimate fallback with ignore errors
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

RAW_DIR = r"d:\agent\RAW\K_CNTT\01_RAW_CLASSIFIED"

def parse_qa_text(content, filename, major, criteria):
    blocks = content.split("====")
    documents = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
            
        lines = block.split("\n")
        q_text = ""
        a_text = ""
        db_file = filename
        db_path = f"01_RAW_CLASSIFIED/{criteria}/{major}"
        source_web = "https://giadinh.edu.vn"
        tag = criteria
        
        current_field = None
        current_val = []
        
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
                
            if line_str.startswith("QUESTION:") or line_str.startswith("Q:") or re.match(r"^Q\d+:", line_str):
                if current_field == "A":
                    a_text = " ".join(current_val)
                current_field = "Q"
                parts = line_str.split(":", 1)
                current_val = [parts[1].strip()] if len(parts) > 1 else []
            elif line_str.startswith("ANSWER:") or line_str.startswith("A:") or re.match(r"^A\d+:", line_str):
                if current_field == "Q":
                    q_text = " ".join(current_val)
                current_field = "A"
                parts = line_str.split(":", 1)
                current_val = [parts[1].strip()] if len(parts) > 1 else []
            elif line_str.startswith("DB_FILE:") or line_str.startswith("SOURCE_FILE_CTDT="):
                parts = line_str.split(":", 1) if ":" in line_str else line_str.split("=", 1)
                db_file = parts[1].strip() if len(parts) > 1 else filename
            elif line_str.startswith("DB_PATH:") or line_str.startswith("DB_PATH="):
                parts = line_str.split(":", 1) if ":" in line_str else line_str.split("=", 1)
                db_path = parts[1].strip() if len(parts) > 1 else db_path
            elif line_str.startswith("SOURCE_WEB:") or line_str.startswith("SOURCE_WEB="):
                parts = line_str.split(":", 1) if ":" in line_str else line_str.split("=", 1)
                source_web = parts[1].strip() if len(parts) > 1 else source_web
            elif line_str.startswith("TAG:") or line_str.startswith("TAG="):
                parts = line_str.split(":", 1) if ":" in line_str else line_str.split("=", 1)
                tag = parts[1].strip() if len(parts) > 1 else tag
            else:
                if current_field:
                    current_val.append(line_str)
                    
        if current_field == "Q":
            q_text = " ".join(current_val)
        elif current_field == "A":
            a_text = " ".join(current_val)
            
        if q_text and a_text:
            text = f"[Tệp: {db_file}] [Đường dẫn: {db_path}] [Tiêu chí: {tag}]\n[Chuyên ngành: {major}]\nHỏi: {q_text}\nTrả lời: {a_text}"
            documents.append({
                "text": text,
                "metadata": {
                    "year": 2026,
                    "university_code": "GDU",
                    "university_name": "Đại học Gia Định",
                    "source_url": source_web
                }
            })
    return documents

def parse_excel_file(file_path, filename, major, criteria):
    documents = []
    try:
        xls = pd.ExcelFile(file_path)
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            if df.empty:
                continue
            df = df.fillna("")
            for idx, row in df.iterrows():
                row_parts = []
                for col in df.columns:
                    val = str(row[col]).strip()
                    if val:
                        row_parts.append(f"{col}: {val}")
                if row_parts:
                    text_line = f"[Tệp: {filename}] [Bảng: {sheet_name}] [Chuyên ngành: {major}] [Tiêu chí: {criteria}]\nDữ liệu: " + ", ".join(row_parts)
                    documents.append({
                        "text": text_line,
                        "metadata": {
                            "year": 2026,
                            "university_code": "GDU",
                            "university_name": "Đại học Gia Định",
                            "source_url": "https://giadinh.edu.vn"
                        }
                    })
    except Exception as e:
        safe_print(f"Lỗi đọc Excel {filename}: {e}")
    return documents

def parse_docx_file(file_path, filename, major, criteria):
    documents = []
    try:
        doc = docx.Document(file_path)
        full_text = "\n".join(para.text for para in doc.paragraphs)
        if full_text.strip():
            header = f"[Tệp: {filename}] [Chuyên ngành: {major}] [Tiêu chí: {criteria}]\nNội dung chính:\n"
            documents.append({
                "text": header + full_text,
                "metadata": {
                    "year": 2026,
                    "university_code": "GDU",
                    "university_name": "Đại học Gia Định",
                    "source_url": "https://giadinh.edu.vn"
                }
            })
    except Exception as e:
        safe_print(f"Lỗi đọc Word {filename}: {e}")
    return documents

def parse_pdf_file(file_path, filename, major, criteria):
    documents = []
    try:
        reader = PdfReader(file_path)
        full_text = ""
        for page in reader.pages:
            full_text += (page.extract_text() or "") + "\n"
        if full_text.strip():
            header = f"[Tệp: {filename}] [Chuyên ngành: {major}] [Tiêu chí: {criteria}]\nNội dung chính:\n"
            documents.append({
                "text": header + full_text,
                "metadata": {
                    "year": 2026,
                    "university_code": "GDU",
                    "university_name": "Đại học Gia Định",
                    "source_url": "https://giadinh.edu.vn"
                }
            })
    except Exception as e:
        safe_print(f"Lỗi đọc PDF {filename}: {e}")
    return documents

def main():
    safe_print("\n--- BẮT ĐẦU NẠP DỮ LIỆU GDU ĐÃ PHÂN LOẠI VÀO CSDL ---")
    
    if not os.path.exists(RAW_DIR):
        safe_print(f"❌ Không tìm thấy thư mục phân loại: {RAW_DIR}")
        return
        
    all_documents = []
    
    # Duyệt qua cấu trúc 16 tiêu chí và chuyên ngành
    for criteria in os.listdir(RAW_DIR):
        criteria_path = os.path.join(RAW_DIR, criteria)
        if not os.path.isdir(criteria_path):
            continue
            
        for major in os.listdir(criteria_path):
            major_path = os.path.join(criteria_path, major)
            if not os.path.isdir(major_path):
                continue
                
            # Duyệt các file trực tiếp trong thư mục chuyên ngành (QA_<major>.txt)
            for file in os.listdir(major_path):
                file_path = os.path.join(major_path, file)
                if os.path.isfile(file_path):
                    filename_lower = file.lower()
                    if file.endswith(".txt") and ("qa" in filename_lower or "qna" in filename_lower):
                        try:
                            content = read_text_file(file_path)
                            docs = parse_qa_text(content, file, major, criteria)
                            safe_print(f" -> Trích xuất được {len(docs)} Q&A từ file: {file} ({major}/{criteria})")
                            all_documents.extend(docs)
                        except Exception as e:
                            safe_print(f"Lỗi file {file}: {e}")
                            
            # Duyệt thư mục con 01_FILE_CHINH
            file_chinh_path = os.path.join(major_path, "01_FILE_CHINH")
            if os.path.exists(file_chinh_path):
                for file in os.listdir(file_chinh_path):
                    file_path = os.path.join(file_chinh_path, file)
                    if not os.path.isfile(file_path):
                        continue
                        
                    ext = os.path.splitext(file)[1].lower()
                    filename_lower = file.lower()
                    
                    if ext == ".txt":
                        try:
                            content = read_text_file(file_path)
                            if "====" in content:
                                docs = parse_qa_text(content, file, major, criteria)
                            else:
                                docs = [{
                                    "text": f"[Tệp: {file}] [Chuyên ngành: {major}] [Tiêu chí: {criteria}]\nNội dung:\n" + content,
                                    "metadata": {
                                        "year": 2026,
                                        "university_code": "GDU",
                                        "university_name": "Đại học Gia Định",
                                        "source_url": "https://giadinh.edu.vn"
                                    }
                                }]
                            safe_print(f" -> Trích xuất được {len(docs)} tài liệu từ file text: {file}")
                            all_documents.extend(docs)
                        except Exception as e:
                            safe_print(f"Lỗi file text {file}: {e}")
                            
                    elif ext == ".docx":
                        docs = parse_docx_file(file_path, file, major, criteria)
                        safe_print(f" -> Trích xuất được {len(docs)} tài liệu từ file Word: {file}")
                        all_documents.extend(docs)
                        
                    elif ext == ".pdf":
                        docs = parse_pdf_file(file_path, file, major, criteria)
                        safe_print(f" -> Trích xuất được {len(docs)} tài liệu từ file PDF: {file}")
                        all_documents.extend(docs)
                        
                    elif ext == ".xlsx":
                        docs = parse_excel_file(file_path, file, major, criteria)
                        safe_print(f" -> Trích xuất được {len(docs)} dòng dữ liệu từ file Excel: {file}")
                        all_documents.extend(docs)

    if not all_documents:
        safe_print("❌ Không trích xuất được tài liệu hợp lệ nào từ thư mục phân loại.")
        return
        
    safe_print(f"\nTổng số tài liệu/Q&A/bản ghi trích xuất thành công: {len(all_documents)}.")
    safe_print("Đang tiến hành tạo Vector Embedding và nạp nối tiếp vào CSDL LanceDB...")
    
    # Khởi tạo RAG Engine và thực hiện nạp nối tiếp (append)
    engine = RAGManager()
    topic = "admissions"
    
    try:
        # Nạp nối tiếp bằng append_documents
        total_chunks = engine.append_documents(all_documents, topic, doc_batch_size=20)
        safe_print(f"\n✅ THÀNH CÔNG! Đã nạp thêm {total_chunks} chunks dữ liệu GDU vào CSDL '{topic}'.")
    except Exception as e:
        safe_print(f"❌ Lỗi quá trình nạp Vector: {e}")

if __name__ == "__main__":
    main()
