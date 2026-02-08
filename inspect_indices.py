import pandas as pd

file_path = r"F:\ai_data\GFCAISearch_경기안양시_최신근로자수10인이상_제조_260203_1118.xlsx"

try:
    # Read without header
    df = pd.read_excel(file_path, header=None, nrows=10)
    
    found = False
    for r_idx, row in df.iterrows():
        for c_idx, val in enumerate(row):
            s_val = str(val).strip()
            if "사업자번호" in s_val:
                print(f"FOUND_BIZ_NO: Row={r_idx}, Col={c_idx}")
                found = True
            if "회사명" in s_val or "기업명" in s_val or "업체명" in s_val:
                print(f"FOUND_NAME: Row={r_idx}, Col={c_idx}")
                
    if not found:
        print("Required columns not found in first 10 rows.")
        
except Exception as e:
    print(f"Error: {e}")
