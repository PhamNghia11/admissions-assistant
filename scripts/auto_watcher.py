import os
import time
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from my_agent.core.rag_engine import RAGManager

# Thiet lap cac duong dan
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOT_FOLDER = os.path.join(BASE_DIR, "hot_folder")
PROCESSED_FOLDER = os.path.join(HOT_FOLDER, "processed")

# Khoi tao RAG Manager
engine = RAGManager()

class IngestionHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        
        file_path = event.src_path
        filename = os.path.basename(file_path)
        
        # Bo qua cac file trong thu muc processed hoac file tam thoi
        if "processed" in file_path or filename.startswith("~") or filename.startswith("."):
            return

        print(f"\n[HOT FOLDER] Phat hien file moi: {filename}")
        
        # Doi file duoc ghi xong hoan toan (khong con bi khoa boi tien trinh khac)
        max_wait = 60
        waited = 0
        while waited < max_wait:
            try:
                # Thu mo file o che do append, neu thanh cong nghia la file da san sang
                with open(file_path, 'a'):
                    pass
                break
            except IOError:
                time.sleep(1)
                waited += 1
                
        if waited >= max_wait:
            print(f"!!! Loi: File {filename} bi khoa qua lau (>{max_wait}s), bo qua.")
            return
            
        # Xac dinh topic dua tren thu muc cha
        parent_dir = os.path.basename(os.path.dirname(file_path))
        topic = parent_dir if parent_dir != "hot_folder" else "general"
        
        try:
            print(f"--- Dang tu dong nap '{filename}' vao chu de '{topic}' ---")
            ext = os.path.splitext(filename)[1].lower()
            
            if ext == ".pdf":
                engine.ingest_pdf(file_path, topic)
            elif ext in [".docx", ".doc"]:
                engine.ingest_docx(file_path, topic)
            else:
                print(f"!!! Dinh dang {ext} chua duoc ho tro tu dong.")
                return

            # Sau khi nap xong, di chuyen vao thu muc processed
            dest_path = os.path.join(PROCESSED_FOLDER, topic, filename)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            
            # Neu file da ton tai thi xoa truoc khi move
            if os.path.exists(dest_path):
                os.remove(dest_path)
                
            os.rename(file_path, dest_path)
            print(f"--- Hoan tat! File da duoc chuyen vao: {dest_path} ---")
            
        except Exception as e:
            print(f"!!! Loi khi nap file tu dong: {e}")

def main():
    # Tao cac thu muc can thiet
    os.makedirs(HOT_FOLDER, exist_ok=True)
    os.makedirs(PROCESSED_FOLDER, exist_ok=True)
    
    # Tao cac sub-folder mau de nguoi dung biet cho ném file
    for sub in ["legal", "admissions", "health", "wiki", "general"]:
        os.makedirs(os.path.join(HOT_FOLDER, sub), exist_ok=True)

    event_handler = IngestionHandler()
    observer = Observer()
    observer.schedule(event_handler, HOT_FOLDER, recursive=True)
    
    print(f"=== HE THONG TU DONG NAP DU LIEU DANG CHAY ===")
    print(f"Theo doi thu muc: {HOT_FOLDER}")
    print("Hay nem file PDF/Word vao cac thu muc con tuong ung de AI tu hoc.")
    print("Bam Ctrl+C de dung.")
    
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
