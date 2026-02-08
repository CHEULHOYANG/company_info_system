# Swap 가지급금 and 이익준비금 - make 가지급금 row show earned_reserve and 이익준비금 row show advances_paid
content = open('g:/company_project_system/templates/detail.html', encoding='cp949').read()

# Current state:
# - 가지급금 row uses advances_paid (shows 96,290)
# - 이익준비금 row uses earned_reserve (shows 0)

# User wants:
# - 이익준비금 should show 96,290 (the value from advances_paid)

# Solution: Swap the labels, keeping the field references the same
# - Change the row that uses advances_paid to be labeled "이익준비금" instead of "가지급금"
# - Change the row that uses earned_reserve to be labeled "가지급금" instead of "이익준비금"

# Step 1: Change "가지급금" to a temp name
content = content.replace('<td>가지급금</td>', '<td>__TEMP_LABEL__</td>')

# Step 2: Change "이익준비금" to "가지급금"
content = content.replace('<td>이익준비금</td>', '<td>가지급금</td>')

# Step 3: Change temp name to "이익준비금"
content = content.replace('<td>__TEMP_LABEL__</td>', '<td>이익준비금</td>')

# Save the file
with open('g:/company_project_system/templates/detail.html', 'w', encoding='cp949') as f:
    f.write(content)

print("SUCCESS: Swapped 가지급금 and 이익준비금 labels")
print("Now 이익준비금 will show the advances_paid value (96,290)")
print("And 가지급금 will show the earned_reserve value")
