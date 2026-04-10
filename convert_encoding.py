with open('email_service_old.py', 'r', encoding='cp949') as f:
    content = f.read()
with open('email_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('UTF-8·Î º¯È¯µÊ')