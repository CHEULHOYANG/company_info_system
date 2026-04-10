# -*- coding: utf-8 -*-
"""
email_management.html 패치 스크립트
1. 전체 배경을 화이트 테마로 변경
2. BOUNCE 계정 해제 버튼 추가 (refreshGroupMembers)
3. 발송 이력 세부 LOG 기능 개선 (viewBatchDetails)
4. 발송 이력 탭의 세부 로그 영역 UI 개선
"""
import re

with open('templates/email_management.html', 'r', encoding='utf-8') as f:
    html = f.read()


# ─────────────────────────────────────────────
# 1. CSS: 전체 배경을 화이트 테마로 변경
# ─────────────────────────────────────────────

# 다크 CSS 변수를 라이트 테마로 변경
old_root = """:root {
            --neon-blue: #00f5ff;
            --neon-purple: #9d50ff;
            --neon-cyan: #00ffd5;
            --neon-coral: #ff4d6d;
            --warning-yellow: #ffcc00;
            --glass-bg: rgba(8, 12, 24, 0.85);
            --glass-border: rgba(255, 255, 255, 0.1);
            --deep-bg: #030712;
            --card-border: rgba(255, 255, 255, 0.08);
            --text-primary: #ffffff;
            --text-secondary: rgba(255, 255, 255, 0.6);
            --primary-glow: rgba(0, 245, 255, 0.3);
        }"""

new_root = """:root {
            --neon-blue: #0099cc;
            --neon-purple: #7c3aed;
            --neon-cyan: #0891b2;
            --neon-coral: #e11d48;
            --warning-yellow: #d97706;
            --glass-bg: rgba(255, 255, 255, 0.97);
            --glass-border: rgba(0, 0, 0, 0.08);
            --deep-bg: #f0f4f8;
            --card-border: rgba(0, 0, 0, 0.08);
            --text-primary: #1a202c;
            --text-secondary: rgba(30, 40, 60, 0.55);
            --primary-glow: rgba(0, 153, 204, 0.2);
        }"""

html = html.replace(old_root, new_root)

# body 배경 변경
old_body = """body {
            font-family: 'Inter', 'Noto Sans KR', sans-serif;
            background-color: var(--deep-bg);
            background-image: url('/static/images/deep_space_bg.png'); /* Cinematic space background */
            background-size: cover; background-position: center; background-attachment: fixed;
            color: var(--text-primary); min-height: 100vh; overflow-x: hidden; line-height: 1.6;
        }"""
new_body = """body {
            font-family: 'Inter', 'Noto Sans KR', sans-serif;
            background-color: #f0f4f8;
            background-image: none;
            color: var(--text-primary); min-height: 100vh; overflow-x: hidden; line-height: 1.6;
        }"""
html = html.replace(old_body, new_body)

# header 배경
old_header = """    height: 70px; display: flex; align-items: center; justify-content: space-between; flex-wrap: nowrap;
            padding: 0 40px; background: rgba(2, 6, 23, 0.85); -webkit-backdrop-filter: blur(25px); backdrop-filter: blur(25px);"""
new_header = """    height: 70px; display: flex; align-items: center; justify-content: space-between; flex-wrap: nowrap;
            padding: 0 40px; background: rgba(255, 255, 255, 0.97); -webkit-backdrop-filter: blur(25px); backdrop-filter: blur(25px);
            border-bottom: 1px solid rgba(0,0,0,0.1);"""
html = html.replace(old_header, new_header)

# nav-tabs 배경
old_nav = """        background: rgba(10, 17, 40, 0.95); backdrop-filter: blur(15px);
            display: flex; justify-content: center; border-bottom: 1px solid var(--card-border);"""
new_nav = """        background: rgba(255, 255, 255, 0.98); backdrop-filter: blur(15px);
            display: flex; justify-content: center; border-bottom: 1px solid rgba(0,0,0,0.1);"""
html = html.replace(old_nav, new_nav)

# tab-btn 스타일
old_tab_btn = """        padding: 15px 25px; cursor: pointer; border: none; background: none;
            font-weight: 700; color: var(--text-secondary); transition: 0.3s;
            border-bottom: 2px solid transparent; font-size: 12px; font-family: 'Orbitron', 'Noto Sans KR', sans-serif;"""
new_tab_btn = """        padding: 15px 25px; cursor: pointer; border: none; background: none;
            font-weight: 700; color: #64748b; transition: 0.3s;
            border-bottom: 2px solid transparent; font-size: 12px; font-family: 'Orbitron', 'Noto Sans KR', sans-serif;"""
html = html.replace(old_tab_btn, new_tab_btn)

# card 배경
old_card = """        background: var(--glass-bg); backdrop-filter: blur(40px); -webkit-backdrop-filter: blur(40px);
            border: 1px solid var(--glass-border); border-radius: 26px; padding: 35px; margin-bottom: 35px;
            box-shadow: 0 30px 60px rgba(0, 0, 0, 0.6), inset 0 1px 1px rgba(255, 255, 255, 0.05);"""
new_card = """        background: #ffffff; backdrop-filter: none; -webkit-backdrop-filter: none;
            border: 1px solid rgba(0,0,0,0.08); border-radius: 26px; padding: 35px; margin-bottom: 35px;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.07);"""
html = html.replace(old_card, new_card)

# form-control 배경
old_fc = """        background: rgba(0, 0, 0, 0.4); border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px; color: white !important; padding: 10px 18px; width: 100%; outline: none; transition: 0.3s;"""
new_fc = """        background: #f8fafc; border: 1px solid #e2e8f0;
            border-radius: 12px; color: #1a202c !important; padding: 10px 18px; width: 100%; outline: none; transition: 0.3s;"""
html = html.replace(old_fc, new_fc)

old_fc_focus = "        .form-control:focus { border-color: var(--neon-blue); box-shadow: 0 0 15px var(--primary-glow); background: rgba(0, 0, 0, 0.6); }"
new_fc_focus = "        .form-control:focus { border-color: var(--neon-blue); box-shadow: 0 0 0 3px rgba(0,153,204,0.15); background: #ffffff; }"
html = html.replace(old_fc_focus, new_fc_focus)

# select option 배경
old_sel_opt = """        select option {
            background-color: #080c18 !important;
            color: #ffffff !important;
            padding: 12px;
            font-size: 0.9rem;
        }"""
new_sel_opt = """        select option {
            background-color: #ffffff !important;
            color: #1a202c !important;
            padding: 12px;
            font-size: 0.9rem;
        }"""
html = html.replace(old_sel_opt, new_sel_opt)

# table td 배경
old_td = "        td { padding: 18px; background: rgba(0, 0, 0, 0.3); color: rgba(255,255,255,0.9);"
new_td = "        td { padding: 18px; background: #fafafa; color: #1a202c;"
html = html.replace(old_td, new_td)

old_tr_hover = "        tr:hover td { background: rgba(0, 245, 255, 0.05); border-color: var(--neon-blue); box-shadow: inset 0 0 10px rgba(0,245,255,0.05); }"
new_tr_hover = "        tr:hover td { background: #f0f7ff; border-color: var(--neon-blue); }"
html = html.replace(old_tr_hover, new_tr_hover)

# th 색상
old_th = "        th { padding: 18px; text-align: left; color: var(--text-secondary); font-family: 'Rajdhani', sans-serif;"
new_th = "        th { padding: 18px; text-align: left; color: #64748b; font-family: 'Rajdhani', sans-serif;"
html = html.replace(old_th, new_th)

# progress-card 배경
old_prog_card = '        .progress-card { background: rgba(2, 6, 23, 0.85); border: 1px solid var(--card-border); border-radius: 35px; padding: 60px; width: 550px; text-align: center; }'
new_prog_card = '        .progress-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 35px; padding: 60px; width: 550px; text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.15); }'
html = html.replace(old_prog_card, new_prog_card)

# modal-card 배경
old_modal_overlay = "        .modal-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.85); backdrop-filter: blur(20px); z-index: 2000; justify-content: center; align-items: center; }"
new_modal_overlay = "        .modal-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.5); backdrop-filter: blur(8px); z-index: 2000; justify-content: center; align-items: center; }"
html = html.replace(old_modal_overlay, new_modal_overlay)

old_modal_card = "        .modal-card { background: rgba(2, 6, 23, 0.95); border: 1px solid var(--neon-blue); width: 620px; border-radius: 35px; padding: 50px; box-shadow: 0 0 60px rgba(0, 212, 255, 0.2); }"
new_modal_card = "        .modal-card { background: #ffffff; border: 1px solid #e2e8f0; width: 620px; border-radius: 35px; padding: 50px; box-shadow: 0 20px 60px rgba(0,0,0,0.2); }"
html = html.replace(old_modal_card, new_modal_card)

# group-box 배경
old_gbox = """        .group-box {
            background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1);"""
new_gbox = """        .group-box {
            background: #f8fafc; border: 1px solid #e2e8f0;"""
html = html.replace(old_gbox, new_gbox)

old_gbox_hover = "        .group-box:hover { background: rgba(0, 212, 255, 0.08); border-color: var(--neon-blue); transform: translateY(-5px); }"
new_gbox_hover = "        .group-box:hover { background: #eff6ff; border-color: var(--neon-blue); transform: translateY(-5px); box-shadow: 0 8px 25px rgba(0,153,204,0.15); }"
html = html.replace(old_gbox_hover, new_gbox_hover)

old_gbox_sel = """        .group-box.selected {
            background: rgba(0, 212, 255, 0.15); border: 2px solid var(--neon-blue);
            box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
        }"""
new_gbox_sel = """        .group-box.selected {
            background: #eff6ff; border: 2px solid var(--neon-blue);
            box-shadow: 0 4px 20px rgba(0,153,204,0.2);
        }"""
html = html.replace(old_gbox_sel, new_gbox_sel)

# group-box title 색상
old_gbox_title = "        .group-box .title { font-family: 'Orbitron', sans-serif; font-size: 0.7rem; color: var(--neon-cyan); letter-spacing: 2px; margin-bottom: 10px; }"
new_gbox_title = "        .group-box .title { font-family: 'Orbitron', sans-serif; font-size: 0.7rem; color: var(--neon-blue); letter-spacing: 2px; margin-bottom: 10px; }"
html = html.replace(old_gbox_title, new_gbox_title)

# member-item 호버
old_member_item_hover = "        .member-item:hover { background: rgba(255,255,255,0.03); }"
new_member_item_hover = "        .member-item:hover { background: rgba(0,153,204,0.05); border-radius: 8px; }"
html = html.replace(old_member_item_hover, new_member_item_hover)

# bounce 패널 선택박스/인풋 배경
old_bounce_panel = """        #bounce-check-panel select,
        #bounce-check-panel input[type="date"] {
            color: #ffffff !important;
            background: rgba(10, 20, 50, 0.7) !important;
            border: 1px solid rgba(0, 212, 255, 0.3) !important;
        }"""
new_bounce_panel = """        #bounce-check-panel select,
        #bounce-check-panel input[type="date"] {
            color: #1a202c !important;
            background: #f8fafc !important;
            border: 1px solid #e2e8f0 !important;
        }"""
html = html.replace(old_bounce_panel, new_bounce_panel)

# 발송 현황 탭의 검색바 배경 (인라인 스타일)
html = html.replace(
    'style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: #fff; padding: 10px; width: 100%; font-size: 0.85rem;"',
    'style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; color: #1a202c; padding: 10px; width: 100%; font-size: 0.85rem;"'
)
html = html.replace(
    'style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: #fff; padding: 9px; width: 100%; font-size: 0.85rem;"',
    'style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; color: #1a202c; padding: 9px; width: 100%; font-size: 0.85rem;"'
)

# 발송 현황 검색 컨테이너 배경
html = html.replace(
    'style="display: flex; gap: 12px; padding: 20px; background: rgba(255,255,255,0.02); border-radius: 12px; margin-bottom: 20px; align-items: flex-end; flex-wrap: wrap;"',
    'style="display: flex; gap: 12px; padding: 20px; background: #f8fafc; border-radius: 12px; margin-bottom: 20px; align-items: flex-end; flex-wrap: wrap; border: 1px solid #e2e8f0;"'
)

# ─────────────────────────────────────────────
# 2. 발송 이력 탭 세부 로그 영역 개선
# ─────────────────────────────────────────────
old_batch_details_area = '''                <div id="batch-details-area" style="display:none; margin-top: 50px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 30px;">
                    <h3 style="font-size: 1.1rem; color: var(--neon-cyan); margin-bottom: 20px;">세부 발송 로그</h3>
                    <div style="overflow-x: auto;">
                        <table>
                            <thead>
                                <tr>
                                    <th>기업명</th>
                                    <th>이메일</th>
                                    <th>발송 상태</th>
                                    <th>오류 내용</th>
                                </tr>
                            </thead>
                            <tbody id="batch-details-list"></tbody>
                        </table>
                    </div>
                </div>'''

new_batch_details_area = '''                <div id="batch-details-area" style="display:none; margin-top: 50px; border-top: 2px solid #e2e8f0; padding-top: 30px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                        <h3 id="batch-details-title" style="font-size: 1.1rem; color: var(--neon-blue); font-weight:800;">
                            <i class="fas fa-list-ul" style="margin-right:8px;"></i>세부 발송 로그
                        </h3>
                        <div style="display:flex; gap:10px; align-items:center;">
                            <span id="batch-details-badge" style="font-size:0.8rem; color:#64748b; background:#f1f5f9; padding:4px 12px; border-radius:20px;"></span>
                            <button class="btn btn-outline" style="padding:5px 14px; font-size:0.75rem; border-color:#e2e8f0; color:#64748b;" onclick="document.getElementById('batch-details-area').style.display='none'">
                                <i class="fas fa-times"></i> 닫기
                            </button>
                        </div>
                    </div>
                    <!-- 통계 요약 -->
                    <div id="batch-details-stats" style="display:flex; gap:12px; margin-bottom:20px; flex-wrap:wrap;"></div>
                    <div style="overflow-x: auto; background: #ffffff; border-radius: 15px; border: 1px solid #e2e8f0;">
                        <table style="width:100%; min-width:700px;">
                            <thead>
                                <tr style="background: #f8fafc;">
                                    <th style="text-align:left; color:#475569;">기업명</th>
                                    <th style="text-align:left; color:#475569;">이메일</th>
                                    <th style="text-align:center; width:120px; color:#475569;">발송상태</th>
                                    <th style="text-align:left; color:#475569;">오류 내용</th>
                                </tr>
                            </thead>
                            <tbody id="batch-details-list"></tbody>
                        </table>
                    </div>
                </div>'''

html = html.replace(old_batch_details_area, new_batch_details_area)

# ─────────────────────────────────────────────
# 3. refreshGroupMembers: BOUNCE 해제 버튼 추가
# ─────────────────────────────────────────────
old_refresh_gm = """        async function refreshGroupMembers(groupId) {
            const listEl = document.getElementById(`members-${groupId}`);
            if (!listEl) return;
            
            const data = await fetchAPI(`/api/email/group-members/${groupId}`);
            if (data.success) {
                listEl.innerHTML = `
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px; padding:0 10px;">
                        <span style="font-size:0.75rem; color:var(--neon-cyan);">INNER NODES</span>
                        <button class="btn btn-outline" style="padding:4px 8px; font-size:0.6rem;" onclick="selectAllInGroup(event, ${groupId})">전체 선택</button>
                    </div>
                    ${data.members.map(m => {
                        const isBounce = m.email_usable === 0;
                        const bounceStyle = isBounce ? 'opacity: 0.6; background: rgba(255, 77, 77, 0.1);' : '';
                        const bounceLabel = isBounce ? ' 🔴 반송됨' : '';
                        return `
                        <div class="member-item" style="${bounceStyle}">
                            <input type="checkbox" class="member-checkbox" 
                                   ${selectedBizNos.has(m.biz_no) && !isBounce ? 'checked' : ''} 
                                   ${isBounce ? 'disabled' : ''}
                                   onchange="toggleMemberSelection('${m.biz_no}')">
                            <div style="flex:1;">
                                <div style="font-weight:700; color: ${isBounce ? '#ff6b6b' : '#fff'};">${m.company_name}${bounceLabel}</div>
                                <div style="font-size:0.7rem; color:${isBounce ? '#ff9999' : 'var(--text-secondary)'};">${formatBizNo(m.biz_no)} | ${m.email || '<span style="color:#ff4d4d;">N/A</span>'}</div>
                                ${isBounce ? `<div style="font-size:0.65rem; color:#ff6b6b; margin-top:3px;">최종상태: ${m.last_send_status}</div>` : ''}
                            </div>
                        </div>
                        `;
                    }).join('')}
                `;
            }
        }"""

new_refresh_gm = """        async function refreshGroupMembers(groupId) {
            const listEl = document.getElementById(`members-${groupId}`);
            if (!listEl) return;
            
            const data = await fetchAPI(`/api/email/group-members/${groupId}`);
            if (data.success) {
                listEl.innerHTML = `
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px; padding:0 10px;">
                        <span style="font-size:0.75rem; color:var(--neon-blue); font-weight:800; letter-spacing:1px;">INNER NODES</span>
                        <button class="btn btn-outline" style="padding:4px 8px; font-size:0.6rem; border-color:#e2e8f0; color:#64748b;" onclick="selectAllInGroup(event, ${groupId})">전체 선택</button>
                    </div>
                    ${data.members.map(m => {
                        const isBounce = m.email_usable === 0;
                        const bounceStyle = isBounce ? 'background: rgba(220,38,38,0.05); border-radius:10px;' : '';
                        const bounceLabel = isBounce ? ' <span style="color:#dc2626; font-size:0.7em;">🔴 반송됨</span>' : '';
                        return `
                        <div class="member-item" style="${bounceStyle} padding:8px;">
                            <input type="checkbox" class="member-checkbox" 
                                   ${selectedBizNos.has(m.biz_no) && !isBounce ? 'checked' : ''} 
                                   ${isBounce ? 'disabled' : ''}
                                   onchange="toggleMemberSelection('${m.biz_no}')">
                            <div style="flex:1; min-width:0;">
                                <div style="font-weight:700; color: ${isBounce ? '#dc2626' : '#1a202c'}; font-size:0.85rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${m.company_name}${bounceLabel}</div>
                                <div style="font-size:0.7rem; color:${isBounce ? '#ef4444' : '#64748b'}; margin-top:2px;">${formatBizNo(m.biz_no)} | ${m.email || '<span style="color:#ef4444;">N/A</span>'}</div>
                                ${isBounce ? `<div style="font-size:0.65rem; color:#ef4444; margin-top:2px;">최종상태: ${m.last_send_status || 'REJECTED'}</div>` : ''}
                            </div>
                            ${isBounce ? `
                            <button onclick="unblockEmail('${m.biz_no}', '${m.email || ''}', ${groupId})" 
                                    title="발송 차단 해제"
                                    style="background: #f0fdf4; border: 1px solid #86efac; color: #16a34a;
                                           padding: 5px 11px; border-radius: 8px; font-size: 0.7rem; cursor:pointer;
                                           font-weight:700; white-space:nowrap; transition:0.2s; flex-shrink:0;">
                                <i class="fas fa-lock-open" style="margin-right:3px;"></i>해제
                            </button>` : ''}
                        </div>
                        `;
                    }).join('')}
                `;
            }
        }"""

html = html.replace(old_refresh_gm, new_refresh_gm)

# ─────────────────────────────────────────────
# 4. viewBatchDetails 함수 개선
# ─────────────────────────────────────────────
old_view_batch = """        async function viewBatchDetails(batchId) {
            const data = await fetchAPI(`/api/email/batch-details/${batchId}`);
            if (data.success) {
                const area = document.getElementById('batch-details-area');
                area.style.display = 'block';
                if (data.details.length === 0) {
                    document.getElementById('batch-details-list').innerHTML = '<tr><td colspan="4" style="text-align:center; color:var(--text-secondary); padding:30px;">상세 로그가 없습니다.</td></tr>';
                } else {
                    document.getElementById('batch-details-list').innerHTML = data.details.map(d => {
                        const st = (d.status || '').toUpperCase();
                        const isSuccess = st === 'SUCCESS' || st === 'DELIVERED';
                        const isFail = st === 'FAIL' || st === 'ERROR' || st === 'FAILED';
                        return `
                        <tr>
                            <td>${d.company_name || '-'}</td>
                            <td style="color:var(--neon-blue); font-size:0.85rem;">${d.email || '-'}</td>
                            <td>${formatStatusBadge(d.status)}</td>
                            <td style="font-size:0.7rem; color:${isFail ? '#f87171' : 'var(--text-secondary)'}; max-width:300px;">${d.error_msg || d.error_message || (isSuccess ? '정상 발송' : '-')}</td>
                        </tr>`;
                    }).join('');
                }
                area.scrollIntoView({ behavior: 'smooth' });
            }
        }"""

new_view_batch = """        async function viewBatchDetails(batchId) {
            const data = await fetchAPI(`/api/email/batch-details/${batchId}`);
            if (data.success) {
                const area = document.getElementById('batch-details-area');
                area.style.display = 'block';
                
                // 타이틀 업데이트
                const titleEl = document.getElementById('batch-details-title');
                const subject = data.details?.subject || batchId.substring(0,8);
                if (titleEl) titleEl.innerHTML = `<i class="fas fa-list-ul" style="margin-right:8px;"></i>세부 발송 로그 — ${subject.length > 35 ? subject.substring(0,35)+'…' : subject}`;
                
                const logs = data.details?.logs || [];
                
                // 통계 배지
                const statsEl = document.getElementById('batch-details-stats');
                if (statsEl) {
                    const success = logs.filter(d => (d.status||'').toUpperCase() === 'SUCCESS').length;
                    const fail = logs.filter(d => ['FAIL','ERROR','BOUNCE','REJECTED'].includes((d.status||'').toUpperCase())).length;
                    const badge = document.getElementById('batch-details-badge');
                    if (badge) badge.textContent = `총 ${logs.length}건`;
                    statsEl.innerHTML = `
                        <div style="background:#f0fdf4; border:1px solid #86efac; padding:8px 18px; border-radius:10px; font-size:0.82rem;">
                            <span style="color:#16a34a; font-weight:800;">✓ 성공 ${success.toLocaleString()}건</span>
                        </div>
                        <div style="background:#fef2f2; border:1px solid #fca5a5; padding:8px 18px; border-radius:10px; font-size:0.82rem;">
                            <span style="color:#dc2626; font-weight:800;">✗ 실패 ${fail.toLocaleString()}건</span>
                        </div>
                        <div style="background:#f8fafc; border:1px solid #e2e8f0; padding:8px 18px; border-radius:10px; font-size:0.82rem;">
                            <span style="color:#64748b;">전체 ${logs.length.toLocaleString()}건</span>
                        </div>
                    `;
                }
                
                if (logs.length === 0) {
                    document.getElementById('batch-details-list').innerHTML = '<tr><td colspan="4" style="text-align:center; color:#94a3b8; padding:40px;">상세 로그가 없습니다.</td></tr>';
                } else {
                    document.getElementById('batch-details-list').innerHTML = logs.map(d => {
                        const st = (d.status || '').toUpperCase();
                        const isSuccess = st === 'SUCCESS' || st === 'DELIVERED';
                        const isFail = st === 'FAIL' || st === 'ERROR' || st === 'FAILED' || st === 'BOUNCE' || st === 'REJECTED';
                        const companyName = d.company_name || d.biz_no || '-';
                        const err = d.error_msg || d.error_message || (isSuccess ? '정상 발송 완료' : '-');
                        const rowBg = isSuccess ? '#f0fdf4' : isFail ? '#fef2f2' : '#fafafa';
                        return `
                        <tr style="background:${rowBg};">
                            <td style="font-weight:600; font-size:0.88rem; color:#1a202c;">${companyName}</td>
                            <td style="color:#0099cc; font-size:0.8rem;">${d.email || '-'}</td>
                            <td style="text-align:center;">${formatStatusBadge(d.status)}</td>
                            <td style="font-size:0.75rem; color:${isFail ? '#dc2626' : (isSuccess ? '#16a34a' : '#64748b')}; max-width:280px; word-break:break-word;">${err}</td>
                        </tr>`;
                    }).join('');
                }
                area.scrollIntoView({ behavior: 'smooth' });
            }
        }"""

html = html.replace(old_view_batch, new_view_batch)

# ─────────────────────────────────────────────
# 5. showAllBouncedAlert에 안내 문구 추가 + unblockEmail 함수 추가
# ─────────────────────────────────────────────
old_bounced_alert = """        function showAllBouncedAlert() {
            // 전체 반송 그룹 클릭시 안내
            const el = document.createElement('div');
            el.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);z-index:99999;background:rgba(10,14,30,0.97);border:2px solid #dc2626;border-radius:20px;padding:35px 45px;text-align:center;box-shadow:0 0 40px rgba(220,38,38,0.4);';
            el.innerHTML = `
                <i class="fas fa-ban" style="font-size:2.5rem;color:#f87171;margin-bottom:15px;display:block;"></i>
                <div style="color:#fff;font-size:1.1rem;font-weight:800;margin-bottom:10px;">전송 불가 그룹</div>
                <div style="color:rgba(255,255,255,0.7);font-size:0.85rem;margin-bottom:20px;">이 그룹의 모든 기업이 반송 처리되어<br>더 이상 메일을 전송할 수 없습니다.</div>
                <button onclick="this.parentElement.remove()" style="background:linear-gradient(135deg,#dc2626,#991b1b);border:none;color:#fff;padding:10px 25px;border-radius:10px;font-weight:700;cursor:pointer;font-size:0.9rem;">확인</button>
            `;
            document.body.appendChild(el);
            setTimeout(() => { if(el.parentElement) el.remove(); }, 4000);
        }"""

new_bounced_alert = """        function showAllBouncedAlert() {
            // 전체 반송 그룹 클릭시 안내
            const el = document.createElement('div');
            el.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);z-index:99999;background:#fff;border:2px solid #fca5a5;border-radius:20px;padding:35px 45px;text-align:center;box-shadow:0 20px 60px rgba(0,0,0,0.2);';
            el.innerHTML = `
                <i class="fas fa-ban" style="font-size:2.5rem;color:#dc2626;margin-bottom:15px;display:block;"></i>
                <div style="color:#1a202c;font-size:1.1rem;font-weight:800;margin-bottom:10px;">전송 불가 그룹</div>
                <div style="color:#64748b;font-size:0.85rem;margin-bottom:8px;">이 그룹의 모든 기업이 반송 처리되어<br>더 이상 메일을 전송할 수 없습니다.</div>
                <div style="color:#94a3b8;font-size:0.75rem;margin-bottom:20px;">그룹을 펼치기(▼)하여 개별 계정을 해제할 수 있습니다.</div>
                <button onclick="this.parentElement.remove()" style="background:#dc2626;border:none;color:#fff;padding:10px 25px;border-radius:10px;font-weight:700;cursor:pointer;font-size:0.9rem;">확인</button>
            `;
            document.body.appendChild(el);
            setTimeout(() => { if(el.parentElement) el.remove(); }, 5000);
        }

        // BOUNCE 계정 해제 함수
        async function unblockEmail(bizNo, email, groupId) {
            const confirmMsg = `다음 계정의 발송 차단을 해제하시겠습니까?\\n\\n사업자번호: ${bizNo}\\n이메일: ${email || '(없음)'}\\n\\n※ 송신 서버 문제로 인한 오류이거나, 이메일 주소를 수정한 경우에만 해제하세요.`;
            if (!confirm(confirmMsg)) return;
            
            try {
                const res = await fetchAPI('/api/email/recover-bounce', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ biz_no: bizNo })
                });
                
                if (res.success) {
                    // 성공 토스트 알림
                    const toast = document.createElement('div');
                    toast.style.cssText = 'position:fixed;top:85px;right:25px;z-index:99999;background:#f0fdf4;border:1px solid #86efac;border-radius:12px;padding:14px 22px;color:#16a34a;font-weight:700;font-size:0.85rem;box-shadow:0 4px 15px rgba(0,0,0,0.1);';
                    toast.innerHTML = `<i class="fas fa-lock-open" style="margin-right:8px;"></i>발송 차단 해제 완료: ${email || bizNo}`;
                    document.body.appendChild(toast);
                    setTimeout(() => toast.remove(), 3500);
                    
                    // 그룹 멤버 목록 새로고침
                    if (groupId) await refreshGroupMembers(groupId);
                    // 타겟 그룹 전체 다시 로드
                    await loadTargetGroups();
                } else {
                    alert('해제 실패: ' + res.message);
                }
            } catch(e) {
                alert('오류 발생: ' + e.message);
            }
        }"""

html = html.replace(old_bounced_alert, new_bounced_alert)

# ─────────────────────────────────────────────
# 6. formatStatusBadge에 REJECTED 추가
# ─────────────────────────────────────────────
old_badge = "            else if (s === 'ERROR' || s === 'FAIL' || s === 'FAILED' || s === 'BOUNCE') { color = '#f87171'; label = '오류'; }"
new_badge = "            else if (s === 'ERROR' || s === 'FAIL' || s === 'FAILED' || s === 'BOUNCE') { color = '#dc2626'; label = '실패'; }\n            else if (s === 'REJECTED') { color = '#ef4444'; label = '거부됨'; }\n            else if (s === 'RECOVERED') { color = '#16a34a'; label = '복구'; }"
html = html.replace(old_badge, new_badge)

# ─────────────────────────────────────────────
# 7. 발송 이력 탭의 테이블 배경 색상
# ─────────────────────────────────────────────
html = html.replace(
    'style="overflow-x: auto; background: rgba(0,0,0,0.2); border-radius: 15px; border: 1px solid rgba(255,255,255,0.05);"',
    'style="overflow-x: auto; background: #ffffff; border-radius: 15px; border: 1px solid #e2e8f0;"'
)

# 발송 이력 탭 테이블 헤더 배경
html = html.replace(
    'style="height: 50px; background: rgba(0, 212, 255, 0.03);"',
    'style="height: 50px; background: #f8fafc;"'
)

with open('templates/email_management.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('✅ 패치 완료! email_management.html 이 성공적으로 업데이트되었습니다.')

# 검증
with open('templates/email_management.html', 'r', encoding='utf-8') as f:
    content = f.read()

checks = [
    ('화이트 배경', '--deep-bg: #f0f4f8' in content),
    ('카드 화이트', 'background: #ffffff; backdrop-filter' in content),
    ('BOUNCE 해제버튼', 'unblockEmail' in content),
    ('viewBatchDetails 개선', 'batch-details-stats' in content),
    ('REJECTED 대응', 'REJECTED' in content and 'label = \'거부됨\'' in content),
]

for name, result in checks:
    print(f"{'✅' if result else '❌'} {name}: {'OK' if result else 'MISSING'}")
