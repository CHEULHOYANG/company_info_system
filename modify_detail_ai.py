# -*- coding: utf-8 -*-
"""
detail.html 파일 안전하게 수정
"""
import os
from datetime import datetime

def safe_modify_detail():
    file_path = 'templates/detail.html'
    
    # 1. 백업 생성
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'templates/detail.html.backup_{timestamp}'
    
    with open(file_path, 'rb') as f:
        original = f.read()
    
    print(f"Original file size: {len(original)} bytes")
    
    if len(original) < 10000:
        print("ERROR: File seems too small, aborting")
        return
    
    # 백업 저장
    with open(backup_path, 'wb') as f:
        f.write(original)
    print(f"Backup saved to: {backup_path}")
    
    content = original
    
    # 2. Chart.js 스크립트 추가 확인
    if b'chart.umd.min.js' not in content:
        head_end = content.find(b'</head>')
        if head_end != -1:
            chart_script = b'\n    <script src="/static/js/chart.umd.min.js"></script>'
            content = content[:head_end] + chart_script + content[head_end:]
            print("Added Chart.js script")
    else:
        print("Chart.js already present")
    
    # 3. startAIAnalysis 함수 찾기
    func_pattern = b'function startAIAnalysis()'
    func_start = content.find(func_pattern)
    
    if func_start == -1:
        print("startAIAnalysis function not found")
        return
    
    print(f"Found startAIAnalysis at position: {func_start}")
    
    # 함수 끝 찾기
    func_end = func_start
    brace_count = 0
    in_function = False
    i = func_start
    while i < len(content):
        byte = content[i:i+1]
        if byte == b'{':
            brace_count += 1
            in_function = True
        elif byte == b'}':
            brace_count -= 1
            if in_function and brace_count == 0:
                func_end = i + 1
                break
        i += 1
    
    if func_end == func_start:
        print("Failed to find function end")
        return
    
    old_func = content[func_start:func_end]
    print(f"Old function length: {len(old_func)} bytes")
    
    # 4. 새 함수 정의 (영문 + 한글 최소화)
    new_function = b'''function startAIAnalysis() {
        console.log('[DEBUG] startAIAnalysis called');
        
        var bizNo = window.currentBizNo || document.body.dataset.bizNo || '1018100340';
        var resultsDiv = document.getElementById('aiAnalysisResults');
        if (!resultsDiv) {
            console.error('aiAnalysisResults not found');
            return;
        }
        
        resultsDiv.innerHTML = '<div style="text-align:center;padding:40px;">' +
            '<div style="width:50px;height:50px;border:4px solid #f3f3f3;border-top:4px solid #2c5aa0;border-radius:50%;margin:0 auto 20px;animation:spin 1s linear infinite;"></div>' +
            '<p style="color:#666;">AI analyzing company data...</p>' +
            '<div id="analysisProgress"></div>' +
            '</div><style>@keyframes spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}</style>';
        
        var steps = ['Loading data...', 'Analyzing shareholders...', 'Analyzing financials...', 'Generating report...'];
        var stepIdx = 0;
        var progressDiv = document.getElementById('analysisProgress');
        var progressInt = setInterval(function() {
            if (stepIdx < steps.length && progressDiv) {
                var el = document.createElement('div');
                el.style.marginTop = '5px';
                el.style.color = '#888';
                el.style.fontSize = '13px';
                el.textContent = steps[stepIdx];
                progressDiv.appendChild(el);
                stepIdx++;
            }
        }, 1000);
        
        fetch('/api/company-analysis-data/' + bizNo)
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (!data.success) throw new Error(data.message || 'Data load failed');
                return fetch('/api/ai-analysis', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({biz_no: bizNo, company_name: data.data.company_name || ''})
                }).then(function(r) { return r.json(); })
                  .then(function(aiData) { return {analysisData: data.data, aiResult: aiData}; });
            })
            .then(function(result) {
                clearInterval(progressInt);
                if (!result.aiResult.success) throw new Error(result.aiResult.message || 'AI analysis failed');
                displayEnhancedResults(result.analysisData, result.aiResult.analysis, resultsDiv);
            })
            .catch(function(err) {
                clearInterval(progressInt);
                console.error(err);
                resultsDiv.innerHTML = '<div style="text-align:center;padding:30px;background:#fff5f5;border-radius:10px;">' +
                    '<p style="color:#dc3545;font-weight:bold;">Error: ' + err.message + '</p>' +
                    '<button onclick="startAIAnalysis()" style="padding:10px 20px;background:#2c5aa0;color:white;border:none;border-radius:5px;cursor:pointer;margin-top:10px;">Retry</button></div>';
            });
    }'''
    
    # 5. 함수 교체
    content = content[:func_start] + new_function + content[func_end:]
    print(f"Replaced function. New content length: {len(content)} bytes")
    
    # 6. displayEnhancedResults 함수가 없으면 추가
    if b'function displayEnhancedResults' not in content:
        enhanced_func = b'''
    
    function displayEnhancedResults(data, analysis, container) {
        var proposals = [];
        if (data.shareholders && data.shareholders.length > 0 && data.shareholders[0].ownership_percent > 50) {
            proposals.push({title: 'Succession Planning', reason: 'Major shareholder: ' + data.shareholders[0].ownership_percent.toFixed(1) + '%'});
        }
        if (data.financials && data.financials.length > 0) {
            var latest = data.financials[0];
            if (latest.sales_revenue > 10000000000) {
                proposals.push({title: 'Cash Management', reason: 'Revenue: ' + (latest.sales_revenue/100000000).toFixed(0) + 'B'});
            }
            if (latest.retained_earnings > 1000000000) {
                proposals.push({title: 'Asset Management', reason: 'Retained Earnings: ' + (latest.retained_earnings/100000000).toFixed(0) + 'B'});
            }
        }
        if (proposals.length === 0) {
            proposals.push({title: 'Company Analysis Report', reason: 'Initial meeting material'});
        }
        
        var proposalHtml = proposals.map(function(p) {
            return '<div style="display:flex;align-items:center;gap:12px;padding:12px;background:#fff;border-radius:8px">' +
                '<div><div style="font-weight:600">' + p.title + '</div><div style="font-size:12px;color:#666">' + p.reason + '</div></div></div>';
        }).join('');
        
        var chartsHtml = '';
        if ((data.shareholders && data.shareholders.length > 0) || (data.financials && data.financials.length > 0)) {
            chartsHtml = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:20px 0">' +
                '<div style="background:#fff;padding:20px;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.05)"><h4 style="color:#2c5aa0;margin:0 0 15px">Shareholders</h4><canvas id="shareholderChart" style="max-height:250px"></canvas></div>' +
                '<div style="background:#fff;padding:20px;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.05)"><h4 style="color:#2c5aa0;margin:0 0 15px">Financials</h4><canvas id="financialChart" style="max-height:250px"></canvas></div></div>';
        }
        
        container.innerHTML = chartsHtml +
            '<div style="background:linear-gradient(135deg,#e8f5e9,#f1f8e9);padding:20px;border-radius:12px;border:2px solid #4caf50;margin-bottom:20px">' +
            '<h4 style="color:#2e7d32;margin:0 0 15px">Recommended Services</h4><div style="display:grid;gap:10px">' + proposalHtml + '</div></div>' +
            '<div style="display:grid;gap:15px">' +
            '<div style="background:#f8f9fa;padding:20px;border-radius:10px;border-left:4px solid #2c5aa0"><h4 style="color:#2c5aa0;margin:0 0 10px">Company Overview</h4><p style="line-height:1.8;margin:0">' + (analysis.summary || 'No data') + '</p></div>' +
            '<div style="background:#f8f9fa;padding:20px;border-radius:10px;border-left:4px solid #28a745"><h4 style="color:#28a745;margin:0 0 10px">Financial Analysis</h4><p style="line-height:1.8;margin:0">' + (analysis.financial_analysis || 'No data') + '</p></div>' +
            '<div style="background:#f8f9fa;padding:20px;border-radius:10px;border-left:4px solid #ffc107"><h4 style="color:#e6a800;margin:0 0 10px">Risk Assessment</h4><p style="line-height:1.8;margin:0">' + (analysis.risk_assessment || 'No data') + '</p></div>' +
            '<div style="background:#f8f9fa;padding:20px;border-radius:10px;border-left:4px solid #6f42c1"><h4 style="color:#6f42c1;margin:0 0 10px">Recommendations</h4><p style="line-height:1.8;margin:0">' + (analysis.recommendations || 'No data') + '</p></div></div>' +
            '<div style="text-align:center;margin-top:20px"><button onclick="startAIAnalysis()" style="padding:10px 25px;background:#6c757d;color:white;border:none;border-radius:5px;cursor:pointer">Analyze Again</button></div>';
        
        if (typeof Chart !== 'undefined') {
            setTimeout(function() {
                if (data.shareholders && data.shareholders.length > 0) {
                    var ctx1 = document.getElementById('shareholderChart');
                    if (ctx1) {
                        var top5 = data.shareholders.slice(0, 5);
                        new Chart(ctx1, {
                            type: 'doughnut',
                            data: {labels: top5.map(function(s){return s.name.substring(0,8);}), datasets: [{data: top5.map(function(s){return s.ownership_percent;}), backgroundColor: ['#2c5aa0','#4a9fd9','#28a745','#ffc107','#dc3545']}]},
                            options: {responsive: true, plugins: {legend: {position: 'right'}}}
                        });
                    }
                }
                if (data.financials && data.financials.length > 0) {
                    var ctx2 = document.getElementById('financialChart');
                    if (ctx2) {
                        var sorted = data.financials.slice().reverse();
                        new Chart(ctx2, {
                            type: 'bar',
                            data: {labels: sorted.map(function(f){return f.year + '';}), datasets: [{label: 'Revenue', data: sorted.map(function(f){return f.sales_revenue/100000000;}), backgroundColor: 'rgba(44,90,160,0.7)'}, {label: 'Op.Income', data: sorted.map(function(f){return f.operating_income/100000000;}), backgroundColor: 'rgba(40,167,69,0.7)'}]},
                            options: {responsive: true, scales: {y: {beginAtZero: true}}}
                        });
                    }
                }
            }, 200);
        }
    }
'''
        # 마지막 </script> 찾기
        last_script = content.rfind(b'</script>')
        if last_script != -1:
            content = content[:last_script] + enhanced_func + content[last_script:]
            print("Added displayEnhancedResults function")
    else:
        print("displayEnhancedResults already exists")
    
    # 7. 파일 저장
    with open(file_path, 'wb') as f:
        f.write(content)
    
    print(f"File saved successfully. New size: {len(content)} bytes")
    print("DONE!")

if __name__ == '__main__':
    safe_modify_detail()
