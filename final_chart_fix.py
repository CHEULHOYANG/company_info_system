import re

# Read the file
with open('templates/detail.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update Library Loading (Head section)
# We will use a reliable CDN first, and fallback to local if needed.
# Also adding an error handler to alert the user.
head_script = '''
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js" onerror="this.onerror=null;this.src='{{ url_for('static', filename='js/chart.umd.min.js') }}';"></script>
'''

# Replace existing script tag
pattern_script_tag = r'<script src=.*chart.*js.*></script>'
if re.search(pattern_script_tag, content):
    content = re.sub(pattern_script_tag, head_script, content)
else:
    # If not found (maybe due to previous edits), insert in head
    content = content.replace('</head>', head_script + '\n</head>')

# 2. Update Chart Script with Safer Data Injection
# We'll replace the entire window.load script block
pattern_script_block = r'window\.addEventListener\(\'load\', function\(\) \{[\s\S]*?\}\);'

new_script_block = '''window.addEventListener('load', function() {
                                    console.log('Window loaded, initializing chart...');
                                    
                                    const ctx = document.getElementById('financialChart');
                                    if (!ctx) {
                                        console.error('Canvas element not found');
                                        return;
                                    }
                                    
                                    // Visual check
                                    ctx.style.background = '#fff';
                                    
                                    // Check Library
                                    if (typeof Chart === 'undefined') {
                                        ctx.parentElement.innerHTML = '<div style="color:red;text-align:center;padding:50px;">Chart.js 라이브러리를 불러오지 못했습니다.<br>페이지를 새로고침 해주세요.</div>';
                                        return;
                                    }

                                    // Safe Data Injection
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
                                        ctx.parentElement.innerHTML = '데이터 처리 중 오류 발생';
                                        return;
                                    }
                                    
                                    console.log('Chart Data:', { years, sales, profits });
                                    
                                    if (years.length === 0) {
                                        ctx.parentElement.innerHTML = '<div style="text-align:center;padding:50px;color:#666;">데이터가 없습니다.</div>';
                                        return;
                                    }

                                    try {
                                        const chartCtx = ctx.getContext('2d');
                                        
                                        // Gradient
                                        let gradientSales = 'rgba(54, 162, 235, 0.5)';
                                        try {
                                            gradientSales = chartCtx.createLinearGradient(0, 0, 0, 300);
                                            gradientSales.addColorStop(0, 'rgba(54, 162, 235, 0.8)');
                                            gradientSales.addColorStop(1, 'rgba(54, 162, 235, 0.2)');
                                        } catch(e) {}

                                        new Chart(chartCtx, {
                                            type: 'bar',
                                            data: {
                                                labels: years,
                                                datasets: [
                                                    {
                                                        label: '매출액 (천원)',
                                                        data: sales,
                                                        backgroundColor: gradientSales,
                                                        borderColor: 'rgba(54, 162, 235, 1)',
                                                        borderWidth: 1,
                                                        borderRadius: 4,
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
                                                        beginAtZero: true
                                                    },
                                                    y1: {
                                                        type: 'linear',
                                                        display: true,
                                                        position: 'right',
                                                        title: { display: true, text: '당기순이익' },
                                                        grid: { display: false },
                                                        beginAtZero: true
                                                    }
                                                }
                                            }
                                        });
                                    } catch (err) {
                                        console.error('Chart creation error:', err);
                                        ctx.parentElement.innerHTML = '<div style="color:red;padding:20px;">차트 생성 오류: ' + err.message + '</div>';
                                    }
                                });'''

content = re.sub(pattern_script_block, new_script_block, content, flags=re.DOTALL)

with open('templates/detail.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Applied final fix for chart rendering")
