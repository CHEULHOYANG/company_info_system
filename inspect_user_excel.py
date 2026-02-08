import pandas as pd

file_path = r"F:\ai_data\GFCAISearch_경기안양시_최신근로자수10인이상_제조_260203_1118.xlsx"

try:
    # Read without header
    df = pd.read_excel(file_path, header=None, nrows=10)
    
    found_header = False
    for i, row in df.iterrows():
        row_list = row.tolist()
        # Check for keywords
        if "사업자번호" in [str(x) for x in row_list]:
            print(f"Header found at Row {i}")
            for col_idx, val in enumerate(row_list):
                 print(f"  Col {col_idx}: {val}")
            found_header = True
            break
            
    if not found_header:
        print("Header '사업자번호' not found in first 10 rows.")
        
except Exception as e:
    print(f"Error reading file: {e}")
