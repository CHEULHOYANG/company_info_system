
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, 'templates')
detail_path = os.path.join(template_dir, 'detail.html')
company_detail_path = os.path.join(template_dir, 'company_detail.html')

with open(detail_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replacements
content = content.replace('company.basic.', 'company.')
content = content.replace('company.additional.', 'additional.')
content = content.replace('company.financials', 'financial_data')
content = content.replace('company.representatives', 'representatives')
content = content.replace('company.shareholders', 'shareholders')
content = content.replace('company.stock_valuation', 'stock_valuation')

with open(company_detail_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Successfully created {company_detail_path} from {detail_path}")
