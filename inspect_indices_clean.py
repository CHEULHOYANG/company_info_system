import pandas as pd
import sys

# Windows console encoding fix
sys.stdout.reconfigure(encoding='utf-8')

file_path = r"F:\ai_data\GFCAISearch_경기안양시_최신근로자수10인이상_제조_260203_1118.xlsx"

try:
    df = pd.read_excel(file_path, header=None, nrows=10)
    
    for r_idx, row in df.iterrows():
        for c_idx, val in enumerate(row):
            s_val = str(val).strip()
            if "사업자번호" in s_val:
                print(f"BIZ_NO_COL: {c_idx}")
            if "회사명" in s_val or "기업명" in s_val or "업체명" in s_val:
                 # Check if it's "업체명(상호)" or similar
                 print(f"NAME_COL: {c_idx}")
except Exception as e:
    print(f"Error: {e}")
