import re

# Read the file
with open('templates/detail.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove existing Chart.js scripts from head or body
content = re.sub(r'<script src=.*chart.*js.*></script>', '', content, flags=re.IGNORECASE)

# 2. Remove the previous inline script block for the chart
# We'll replace it with a new one at the end of the body
pattern_script_block = r'window\.addEventListener\(\'load\', function\(\) \{[\s\S]*?\}\);'
content = re.sub(pattern_script_block, '', content)

# 3. Append new script at the end of body
# Using Chart.js 3.9.1 which is very stable
new_footer_script = '''
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Chart.js 3.9.1...');
    
    const ctx = document.getElementById('financialChart');
    if (!ctx) {
        console.error('Canvas element not found');
        return;
    }
    
    // Force canvas size
    ctx.style.width = '100%';
    ctx.style.height = '100%';
    
    // Data Preparation
    const years = [];
    const sales = [];
    const profits = [];
    
    try {
        {% if company.financials %}
            {% for fin in company.financials | reverse %}
                years.push('{{ fin.fiscal_year }}');
                sales.push({{ (fin.sales_revenue / 1000)|int if fin.sales_revenue is not none else 0 }});
                profits.push({{ (fin.operating_income / 1000)|int if fin.operating_income is not none else 0 }});
            {% endfor %}
        {% endif %}
    } catch (e) {
        console.error('Data parsing error:', e);
    }
    
    console.log('Chart Data:', { years, sales, profits });
    
    if (years.length === 0) {
        ctx.parentElement.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#666;">데이터가 없습니다.</div>';
        return;
    }

    // Check if Chart is loaded
    if (typeof Chart === 'undefined') {
        ctx.parentElement.innerHTML = '<div style="color:red;text-align:center;padding:50px;">Chart.js 로드 실패</div>';
        return;
    }

    try {
        const chartCtx = ctx.getContext('2d');
        
        new Chart(chartCtx, {
            type: 'bar',
            data: {
                labels: years,
                datasets: [
                    {
                        label: '매출액 (천원)',
                        data: sales,
                        backgroundColor: 'rgba(54, 162, 235, 0.5)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1,
                        yAxisID: 'y',
                        order: 2,
                        barPercentage: 0.5
                    },
                    {
                        label: '당기순이익 (천원)',
                        data: profits,
                        type: 'line',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        backgroundColor: 'rgba(255, 99, 132, 0.5)',
                        borderWidth: 2,
                        pointBackgroundColor: '#fff',
                        pointBorderColor: 'rgba(255, 99, 132, 1)',
                        pointRadius: 4,
                        fill: false,
                        borderDash: [5, 5],
                        yAxisID: 'y1',
                        order: 1,
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: { position: 'top' },
                    title: { 
                        display: true, 
                        text: '매출 및 당기순이익 추이 (단위: 천원)',
                        font: { size: 14, weight: 'bold' }
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: { display: true, text: '매출액' },
                        grid: { borderDash: [2, 2] }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: { display: true, text: '당기순이익' },
                        grid: { display: false }
                    }
                }
            }
        });
        console.log('Chart created successfully');
    } catch (err) {
        console.error('Chart creation error:', err);
        ctx.parentElement.innerHTML = '<div style="color:red;padding:20px;">차트 생성 오류: ' + err.message + '</div>';
    }
});
</script>
'''

# Insert before closing body tag
if '</body>' in content:
    content = content.replace('</body>', new_footer_script + '\n</body>')
else:
    content += new_footer_script

with open('templates/detail.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Moved script to body end and switched to Chart.js 3.9.1")
