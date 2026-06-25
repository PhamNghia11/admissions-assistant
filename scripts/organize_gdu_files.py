import os
import shutil
import glob
import sys
import io

# Thiết lập encoding console để in tiếng Việt mượt mà trên Windows
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass

# Thư mục nguồn và đích
SRC_DIR = r"d:\agent\hot_folder\admissions"
RAW_DIR = r"d:\agent\RAW\K_CNTT\01_RAW_CLASSIFIED"

# Danh sách 16 tiêu chí tiêu chuẩn
CRITERIA = [
    "01_NGANH_CTDT",
    "02_TIEUCHI_TUYENSINH",
    "03_PHUONGTHUC_XETTUYEN",
    "04_HOCPHI_CHIPHI",
    "05_DICHVU_SINHVIEN",
    "06_HOCBONG_TAICHINH",
    "07_KTX_CSVC",
    "08_COHOI_VIECLAM",
    "09_GIANGVIEN_PPGD",
    "10_UYTIN_THUONGHIEU",
    "11_VITRI_CAMPUS",
    "12_CLB_HOATDONG",
    "13_LIENKET_QUOCTE",
    "14_THUCTAP_DOANHNGHIEP",
    "15_TRUONG_THPT",
    "16_KEYPOINT_NGANH"
]

# Danh sách 8 chuyên ngành chuẩn của khoa CNTT theo quy định
MAJORS = ["ANM", "ATTT", "CNTT", "IoT", "KHDL", "KTPM", "MMTTDL", "TTNT"]

# Bản đồ phân loại file cụ thể về chuyên ngành
MAJOR_MAP = {
    "KTPM": "KTPM",
    "ATTT": "ATTT",
    "ATTTM": "ATTT",
    "ANM": "ANM",
    "IOT": "IoT",
    "LAP TRINH KET NOI VAN VAT": "IoT",
    "KHDL": "KHDL",
    "BIGDATA": "KHDL",
    "KHAI THAC DU LIEU LON": "KHDL",
    "MMT": "MMTTDL",
    "MMTTTDL": "MMTTDL",
    "MMT&TTDL": "MMTTDL",
    "TTNT": "TTNT",
    "CNTT": "CNTT",
    "DHKTS": "CNTT",
    "DO HOA KY THUAT SO": "CNTT",
    "TKVM": "CNTT",
    "THIET KE VI MACH": "CNTT",
}

def get_major_from_name(filename):
    filename_upper = filename.upper()
    for key, val in MAJOR_MAP.items():
        if key in filename_upper:
            return val
    return None

def main():
    print("--- BẮT ĐẦU SẮP XẾP VÀ CHUẨN HÓA THƯ MỤC DỮ LIỆU GDU (SỬA LỖI TÊN FILE) ---")
    
    # Xóa thư mục đích cũ nếu tồn tại để phân loại sạch sẽ từ đầu
    if os.path.exists(RAW_DIR):
        print(" -> Đang làm sạch thư mục RAW cũ...")
        shutil.rmtree(RAW_DIR)
        
    # 1. Tạo cấu trúc thư mục 4 cấp độ
    print("\n[1] Đang khởi tạo cấu trúc thư mục 16 tiêu chí và 8 chuyên ngành...")
    for cri in CRITERIA:
        for major in MAJORS:
            major_path = os.path.join(RAW_DIR, cri, major)
            os.makedirs(os.path.join(major_path, "01_FILE_CHINH"), exist_ok=True)
            os.makedirs(os.path.join(major_path, "02_IMAGES"), exist_ok=True)
            os.makedirs(os.path.join(major_path, "03_VIDEOS"), exist_ok=True)
            os.makedirs(os.path.join(major_path, "04_LINKS"), exist_ok=True)

    # 2. Phân loại và di chuyển file
    print("\n[2] Đang phân loại và sao chép các file vào đúng vị trí...")
    
    files = [f for f in os.listdir(SRC_DIR) if os.path.isfile(os.path.join(SRC_DIR, f))]
    
    for filename in files:
        src_file = os.path.join(SRC_DIR, filename)
        
        # Bỏ qua các file zip
        if filename.endswith(".zip"):
            continue
            
        major = get_major_from_name(filename)
        filename_lower = filename.lower()
        ext = os.path.splitext(filename)[1].lower()
        
        # A. CÁC TÀI LIỆU VỀ CHƯƠNG TRÌNH ĐÀO TẠO & DANH SÁCH MÔN HỌC (01_NGANH_CTDT)
        if "ctdt" in filename_lower or "danhsachmonhoc" in filename_lower or "ban hanh ctdt" in filename_lower or "qd_gdu" in filename_lower:
            if major:
                dest_dir = os.path.join(RAW_DIR, "01_NGANH_CTDT", major, "01_FILE_CHINH")
                shutil.copy2(src_file, os.path.join(dest_dir, filename))
                print(f" -> [CTDT] Đã xếp '{filename}' vào 01_NGANH_CTDT/{major}")
            else:
                for m in MAJORS:
                    dest_dir = os.path.join(RAW_DIR, "01_NGANH_CTDT", m, "01_FILE_CHINH")
                    shutil.copy2(src_file, os.path.join(dest_dir, filename))
                print(f" -> [CTDT - Dùng chung] Đã sao chép '{filename}' vào 01_NGANH_CTDT cho tất cả chuyên ngành")
                
        # B. FILE HƯỚNG NGHIỆP / CƠ HỘI VIỆC LÀM (08_COHOI_VIECLAM)
        elif "career" in filename_lower or "jobs" in filename_lower or "viec_lam" in filename_lower:
            if major:
                dest_dir = os.path.join(RAW_DIR, "08_COHOI_VIECLAM", major, "01_FILE_CHINH")
                shutil.copy2(src_file, os.path.join(dest_dir, filename))
                print(f" -> [Cơ hội việc làm] Đã xếp '{filename}' vào 08_COHOI_VIECLAM/{major}")
            else:
                for m in MAJORS:
                    dest_dir = os.path.join(RAW_DIR, "08_COHOI_VIECLAM", m, "01_FILE_CHINH")
                    shutil.copy2(src_file, os.path.join(dest_dir, filename))
                print(f" -> [Cơ hội việc làm - Dùng chung] Đã sao chép '{filename}' vào 08_COHOI_VIECLAM cho tất cả chuyên ngành")
                
        # C. FILE Q&A TEXT (QA_*.txt hoặc 100QA_*.txt - CHỈ CHẤP NHẬN .txt)
        elif ("qa" in filename_lower or "qna" in filename_lower) and ext == ".txt":
            if major:
                dest_name = f"QA_{major}.txt"
                dest_path_ctdt = os.path.join(RAW_DIR, "01_NGANH_CTDT", major, dest_name)
                dest_path_tuyensinh = os.path.join(RAW_DIR, "02_TIEUCHI_TUYENSINH", major, dest_name)
                
                shutil.copy2(src_file, dest_path_ctdt)
                shutil.copy2(src_file, dest_path_tuyensinh)
                print(f" -> [Q&A Text] Đã xếp '{filename}' làm file QA chính thức cho {major}")
            else:
                for m in MAJORS:
                    dest_path = os.path.join(RAW_DIR, "02_TIEUCHI_TUYENSINH", m, "QA_TUYENSINH_CHUNG.txt")
                    shutil.copy2(src_file, dest_path)
                print(f" -> [Q&A - Tuyển sinh chung] Đã sao chép '{filename}' vào 02_TIEUCHI_TUYENSINH cho tất cả chuyên ngành")

        # D. CÁC TÀI LIỆU DÙNG CHUNG KHÁC (Xét tuyển, học phí, học bổng...) - ĐỐI VỚI FILE EXCEL LÀM TEMPLATE Q&A
        else:
            # Nếu là file Q&A dạng Excel (.xlsx), xếp vào 01_FILE_CHINH của tiêu chí 02_TIEUCHI_TUYENSINH
            if ("qa" in filename_lower or "qna" in filename_lower) and ext == ".xlsx":
                if major:
                    dest_dir = os.path.join(RAW_DIR, "02_TIEUCHI_TUYENSINH", major, "01_FILE_CHINH")
                    shutil.copy2(src_file, os.path.join(dest_dir, filename))
                    print(f" -> [Q&A Excel] Đã xếp file Excel '{filename}' vào 02_TIEUCHI_TUYENSINH/{major}")
                else:
                    for m in MAJORS:
                        dest_dir = os.path.join(RAW_DIR, "02_TIEUCHI_TUYENSINH", m, "01_FILE_CHINH")
                        shutil.copy2(src_file, os.path.join(dest_dir, filename))
                    print(f" -> [Q&A Excel - Dùng chung] Đã sao chép '{filename}' vào 02_TIEUCHI_TUYENSINH cho tất cả chuyên ngành")
            elif "hoc phi" in filename_lower or "hoc_phi" in filename_lower or "tuyen sinh" in filename_lower or "tuyen_sinh" in filename_lower or "xet tuyen" in filename_lower:
                for m in MAJORS:
                    shutil.copy2(src_file, os.path.join(RAW_DIR, "02_TIEUCHI_TUYENSINH", m, "01_FILE_CHINH", filename))
                    shutil.copy2(src_file, os.path.join(RAW_DIR, "03_PHUONGTHUC_XETTUYEN", m, "01_FILE_CHINH", filename))
                    shutil.copy2(src_file, os.path.join(RAW_DIR, "04_HOCPHI_CHIPHI", m, "01_FILE_CHINH", filename))
                    shutil.copy2(src_file, os.path.join(RAW_DIR, "06_HOCBONG_TAICHINH", m, "01_FILE_CHINH", filename))
                print(f" -> [Thông tin chung] Đã phân phối '{filename}' vào 02, 03, 04, 06 cho tất cả chuyên ngành")
            else:
                for m in MAJORS:
                    dest_dir = os.path.join(RAW_DIR, "02_TIEUCHI_TUYENSINH", m, "01_FILE_CHINH")
                    shutil.copy2(src_file, os.path.join(dest_dir, filename))
                print(f" -> [Khác] Đã sao chép '{filename}' vào 02_TIEUCHI_TUYENSINH cho tất cả chuyên ngành")

    # 3. Phân loại các file trong thư mục QnA_GDU (JSON)
    json_src = os.path.join(SRC_DIR, "QnA_GDU")
    if os.path.exists(json_src):
        print("\n[3] Đang phân loại các file JSON trong QnA_GDU...")
        json_files = glob.glob(os.path.join(json_src, "*.json"))
        for jf in json_files:
            jf_name = os.path.basename(jf)
            major = get_major_from_name(jf_name)
            if major:
                dest_dir = os.path.join(RAW_DIR, "01_NGANH_CTDT", major, "01_FILE_CHINH")
                shutil.copy2(jf, os.path.join(dest_dir, jf_name))
                print(f" -> [JSON] Đã xếp '{jf_name}' vào 01_NGANH_CTDT/{major}")
            else:
                for m in MAJORS:
                    dest_dir = os.path.join(RAW_DIR, "02_TIEUCHI_TUYENSINH", m, "01_FILE_CHINH")
                    shutil.copy2(jf, os.path.join(dest_dir, jf_name))
                print(f" -> [JSON - Tuyển sinh chung] Đã sao chép '{jf_name}' cho tất cả chuyên ngành")

    print("\n✅ HOÀN TẤT SẮP XẾP SỬA LỖI! Dữ liệu đã được tổ chức chuẩn hóa chính xác tại:")
    print(f"   {RAW_DIR}")

if __name__ == "__main__":
    main()
