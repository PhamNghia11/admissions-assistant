import os
import sys

def main():
    print("--- DANG TONG HOP CONTEXT DU AN CHO CLAUDE ---")
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_file = os.path.join(project_root, "project_context_for_claude.txt")
    
    # Danh sach cac file tai lieu va ma nguon quan trong nhat
    files_to_merge = [
        # Tai lieu he thong
        ("PROJECT_KNOWLEDGE.md", os.path.join(project_root, "PROJECT_KNOWLEDGE.md")),
        ("ARCHITECTURE.md", os.path.join(project_root, "ARCHITECTURE.md")),
        
        # De cuong & Walkthrough (Lay tu appDataDir - Thay bang duong dan that luc run)
        ("de_tai_bao_cao_tuyen_sinh.md", os.path.join(
            os.environ.get("USERPROFILE", "C:\\Users\\ACER"), 
            ".gemini\\antigravity-ide\\brain\\e67e94b6-bcc2-4355-ba55-eb1ec14674f2\\de_tai_bao_cao_tuyen_sinh.md"
        )),
        ("walkthrough.md", os.path.join(
            os.environ.get("USERPROFILE", "C:\\Users\\ACER"), 
            ".gemini\\antigravity-ide\\brain\\e67e94b6-bcc2-4355-ba55-eb1ec14674f2\\walkthrough.md"
        )),
        
        # Ma nguon backend cot loi
        ("my_agent/agent.py", os.path.join(project_root, "my_agent", "agent.py")),
        ("my_agent/core/rag_engine.py", os.path.join(project_root, "my_agent", "core", "rag_engine.py")),
        ("my_agent/application/assistant_application.py", os.path.join(project_root, "my_agent", "application", "assistant_application.py")),
        ("auth_server.py", os.path.join(project_root, "auth_server.py")),
        
        # Cac script nap du lieu GDU moi viet
        ("scripts/organize_gdu_files.py", os.path.join(project_root, "scripts", "organize_gdu_files.py")),
        ("scripts/ingest_gdu_classified.py", os.path.join(project_root, "scripts", "ingest_gdu_classified.py")),
    ]
    
    with open(output_file, "w", encoding="utf-8") as out:
        out.write("======================================================================\n")
        out.write("TOAN BO CONTEXT VA MA NGUON DU AN X-AGENT CHATBOT TU VAN TUYEN SINH GDU\n")
        out.write("======================================================================\n\n")
        
        for name, path in files_to_merge:
            if os.path.exists(path):
                print(f"-> Dang doc: {name}")
                out.write(f"######################################################################\n")
                out.write(f"FILE: {name}\n")
                out.write(f"PATH: {path}\n")
                out.write(f"######################################################################\n\n")
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        out.write(f.read())
                except Exception as e:
                    out.write(f"Loi doc file: {e}\n")
                out.write("\n\n")
            else:
                print(f"x Khong tim thay: {name} tai {path}")
                out.write(f"!!! KHONG TIM THAY FILE: {name}\n\n")
                
    print(f"=== TONG HOP THANH CONG! ===")
    print(f"File dau ra da duoc tao tai: {output_file}")
    print("Ban chi can gui file nay len Claude va yeu cau viet bao cao theo de cuong ben trong.")

if __name__ == "__main__":
    main()
