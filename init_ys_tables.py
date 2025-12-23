import sqlite3
import sys
sys.path.insert(0, 'g:/company_project_system')

from web_app import init_ys_honers_tables

print('YS Honers 테이블 생성 중...')
init_ys_honers_tables()
print('완료!')
