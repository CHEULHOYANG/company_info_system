# -*- coding: utf-8 -*-
"""CMS main.html - 미래지향적 파티클 애니메이션 디자인으로 재작성"""
import os

main_html = '''<!DOCTYPE html>
<html lang="ko">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CMS - 기업 관리 시스템</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@100;200;300;400;500;600;700&family=Orbitron:wght@400;500;700;900&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --neon-blue: #00d4ff;
            --neon-purple: #7b2fff;
            --neon-cyan: #00ffcc;
            --deep-bg: #020817;
            --card-bg: rgba(255, 255, 255, 0.04);
            --card-border: rgba(255, 255, 255, 0.08);
            --text-primary: rgba(255, 255, 255, 0.95);
            --text-secondary: rgba(255, 255, 255, 0.55);
        }

        body {
            font-family: 'Inter', sans-serif;
            background: var(--deep-bg);
            min-height: 100vh;
            overflow-x: hidden;
            overflow-y: auto;
            color: var(--text-primary);
        }

        /* ===== CANVAS PARTICLE BG ===== */
        #particle-canvas {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 0;
            pointer-events: none;
        }

        /* ===== GRADIENT OVERLAY ===== */
        .bg-overlay {
            position: fixed;
            inset: 0;
            z-index: 1;
            background:
                radial-gradient(ellipse at 20% 20%, rgba(123, 47, 255, 0.15) 0%, transparent 60%),
                radial-gradient(ellipse at 80% 80%, rgba(0, 212, 255, 0.12) 0%, transparent 60%),
                radial-gradient(ellipse at 50% 50%, rgba(0, 255, 204, 0.05) 0%, transparent 70%);
            pointer-events: none;
        }

        /* ===== SCANLINE EFFECT ===== */
        .scanlines {
            position: fixed;
            inset: 0;
            z-index: 2;
            background: repeating-linear-gradient(
                0deg,
                transparent,
                transparent 2px,
                rgba(0, 0, 0, 0.03) 2px,
                rgba(0, 0, 0, 0.03) 4px
            );
            pointer-events: none;
        }

        /* ===== MAIN CONTENT ===== */
        .main-wrapper {
            position: relative;
            z-index: 10;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            padding: 0 24px 40px;
        }

        /* ===== TOP BAR ===== */
        .topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 20px 0;
            border-bottom: 1px solid rgba(0, 212, 255, 0.15);
            position: sticky;
            top: 0;
            backdrop-filter: blur(20px);
            background: rgba(2, 8, 23, 0.8);
            z-index: 100;
            margin: 0 -24px;
            padding-left: 24px;
            padding-right: 24px;
        }

        .logo-group {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .logo-icon {
            width: 42px;
            height: 42px;
            background: linear-gradient(135deg, var(--neon-blue), var(--neon-purple));
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Orbitron', sans-serif;
            font-weight: 900;
            font-size: 14px;
            color: white;
            box-shadow: 0 0 20px rgba(0, 212, 255, 0.4), inset 0 0 20px rgba(255,255,255,0.1);
            animation: logoPulse 3s ease-in-out infinite;
        }

        @keyframes logoPulse {
            0%, 100% { box-shadow: 0 0 20px rgba(0, 212, 255, 0.4), inset 0 0 20px rgba(255,255,255,0.1); }
            50% { box-shadow: 0 0 40px rgba(0, 212, 255, 0.7), 0 0 60px rgba(123, 47, 255, 0.3), inset 0 0 20px rgba(255,255,255,0.15); }
        }

        .logo-text {
            display: flex;
            flex-direction: column;
        }

        .logo-name {
            font-family: 'Orbitron', sans-serif;
            font-size: 20px;
            font-weight: 700;
            background: linear-gradient(90deg, var(--neon-blue), var(--neon-cyan));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: 3px;
        }

        .logo-sub {
            font-size: 10px;
            color: var(--text-secondary);
            letter-spacing: 2px;
            margin-top: 2px;
        }

        /* Status bar */
        .status-bar {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            background: var(--neon-cyan);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--neon-cyan);
            animation: blink 2s ease-in-out infinite;
        }

        @keyframes blink {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(0.8); }
        }

        .status-text {
            font-size: 11px;
            color: var(--neon-cyan);
            letter-spacing: 1.5px;
        }

        /* User panel */
        .user-panel {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .user-info {
            text-align: right;
        }

        .user-name {
            font-size: 14px;
            font-weight: 600;
            color: white;
        }

        .user-level {
            font-size: 11px;
            color: var(--neon-blue);
            letter-spacing: 1px;
        }

        .subscription-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
        }

        .subscription-badge.normal {
            background: rgba(0, 255, 204, 0.15);
            border: 1px solid rgba(0, 255, 204, 0.3);
            color: var(--neon-cyan);
        }

        .subscription-badge.warning {
            background: rgba(255, 193, 7, 0.15);
            border: 1px solid rgba(255, 193, 7, 0.3);
            color: #ffc107;
        }

        .subscription-badge.expired {
            background: rgba(220, 53, 69, 0.15);
            border: 1px solid rgba(220, 53, 69, 0.3);
            color: #dc3545;
        }

        .action-btns {
            display: flex;
            gap: 8px;
        }

        .btn-topbar {
            padding: 8px 18px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            letter-spacing: 0.5px;
            border: 1px solid;
        }

        .btn-db {
            background: rgba(123, 47, 255, 0.2);
            border-color: rgba(123, 47, 255, 0.5);
            color: #c084fc;
        }

        .btn-db:hover {
            background: rgba(123, 47, 255, 0.4);
            box-shadow: 0 0 20px rgba(123, 47, 255, 0.3);
            transform: translateY(-1px);
        }

        .btn-logout {
            background: rgba(255, 255, 255, 0.05);
            border-color: rgba(255, 255, 255, 0.15);
            color: var(--text-secondary);
            text-decoration: none;
        }

        .btn-logout:hover {
            background: rgba(255, 255, 255, 0.1);
            color: white;
            transform: translateY(-1px);
        }

        /* ===== HERO SECTION ===== */
        .hero {
            text-align: center;
            padding: 50px 0 40px;
            position: relative;
        }

        .hero-label {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 20px;
            background: rgba(0, 212, 255, 0.08);
            border: 1px solid rgba(0, 212, 255, 0.2);
            border-radius: 30px;
            font-size: 11px;
            color: var(--neon-blue);
            letter-spacing: 3px;
            margin-bottom: 24px;
            animation: fadeInDown 0.8s ease forwards;
        }

        .hero-label::before {
            content: '';
            width: 6px;
            height: 6px;
            background: var(--neon-blue);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--neon-blue);
            animation: blink 1.5s ease-in-out infinite;
        }

        @keyframes fadeInDown {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .hero-title {
            font-family: 'Orbitron', sans-serif;
            font-size: clamp(36px, 5vw, 60px);
            font-weight: 900;
            line-height: 1;
            margin-bottom: 16px;
            background: linear-gradient(135deg, #ffffff 0%, var(--neon-blue) 50%, var(--neon-cyan) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: fadeInUp 0.8s ease 0.2s both;
            text-shadow: none;
            position: relative;
        }

        .hero-title::after {
            content: 'CMS';
            position: absolute;
            inset: 0;
            background: linear-gradient(135deg, #ffffff 0%, var(--neon-blue) 50%, var(--neon-cyan) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            filter: blur(20px);
            opacity: 0.4;
            z-index: -1;
        }

        .hero-subtitle {
            font-size: 14px;
            color: var(--text-secondary);
            letter-spacing: 4px;
            animation: fadeInUp 0.8s ease 0.3s both;
        }

        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* ===== DIVIDER ===== */
        .neon-divider {
            width: 100%;
            max-width: 800px;
            margin: 0 auto 40px;
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--neon-blue), var(--neon-cyan), transparent);
            position: relative;
            overflow: visible;
        }

        .neon-divider::after {
            content: '';
            position: absolute;
            left: 50%;
            top: -3px;
            transform: translateX(-50%);
            width: 6px;
            height: 6px;
            background: var(--neon-cyan);
            border-radius: 50%;
            box-shadow: 0 0 12px var(--neon-cyan);
        }

        /* ===== MENU GRID ===== */
        .menu-section-title {
            font-size: 10px;
            letter-spacing: 4px;
            color: var(--text-secondary);
            text-align: center;
            margin-bottom: 24px;
            animation: fadeInUp 0.8s ease 0.4s both;
        }

        .menu-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            max-width: 1200px;
            margin: 0 auto 20px;
            width: 100%;
            animation: fadeInUp 0.8s ease 0.5s both;
        }

        .menu-card {
            position: relative;
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 28px 24px;
            text-decoration: none;
            color: white;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            gap: 10px;
            cursor: pointer;
            backdrop-filter: blur(10px);
        }

        .menu-card::before {
            content: '';
            position: absolute;
            inset: 0;
            background: linear-gradient(135deg, rgba(255,255,255,0.06) 0%, transparent 100%);
            pointer-events: none;
        }

        .menu-card::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 2px;
            background: var(--card-accent, linear-gradient(90deg, var(--neon-blue), var(--neon-cyan)));
            transform: scaleX(0);
            transform-origin: left;
            transition: transform 0.4s ease;
        }

        .menu-card:hover {
            transform: translateY(-8px) scale(1.02);
            border-color: rgba(0, 212, 255, 0.3);
            box-shadow:
                0 20px 60px rgba(0, 0, 0, 0.4),
                0 0 30px rgba(0, 212, 255, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
            background: rgba(255, 255, 255, 0.07);
        }

        .menu-card:hover::after {
            transform: scaleX(1);
        }

        /* Card accent colors */
        .card-db { --card-accent: linear-gradient(90deg, var(--neon-blue), #0099ff); }
        .card-history { --card-accent: linear-gradient(90deg, var(--neon-purple), #a855f7); }
        .card-pipeline { --card-accent: linear-gradient(90deg, var(--neon-cyan), #00ff88); }
        .card-sales { --card-accent: linear-gradient(90deg, #ff6b35, #f7c59f); }
        .card-biz { --card-accent: linear-gradient(90deg, #a855f7, #ec4899); }
        .card-admin { --card-accent: linear-gradient(90deg, #fbbf24, #f59e0b); }

        .card-db:hover { box-shadow: 0 20px 60px rgba(0,0,0,0.4), 0 0 40px rgba(0, 153, 255, 0.15); }
        .card-history:hover { box-shadow: 0 20px 60px rgba(0,0,0,0.4), 0 0 40px rgba(123, 47, 255, 0.15); }
        .card-pipeline:hover { box-shadow: 0 20px 60px rgba(0,0,0,0.4), 0 0 40px rgba(0, 255, 204, 0.15); }
        .card-sales:hover { box-shadow: 0 20px 60px rgba(0,0,0,0.4), 0 0 40px rgba(255, 107, 53, 0.15); }
        .card-biz:hover { box-shadow: 0 20px 60px rgba(0,0,0,0.4), 0 0 40px rgba(168, 85, 247, 0.15); }
        .card-admin:hover { box-shadow: 0 20px 60px rgba(0,0,0,0.4), 0 0 40px rgba(251, 191, 36, 0.15); }

        .card-icon {
            width: 44px;
            height: 44px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            margin-bottom: 4px;
            position: relative;
        }

        .card-db .card-icon { background: rgba(0, 153, 255, 0.15); border: 1px solid rgba(0, 153, 255, 0.3); }
        .card-history .card-icon { background: rgba(123, 47, 255, 0.15); border: 1px solid rgba(123, 47, 255, 0.3); }
        .card-pipeline .card-icon { background: rgba(0, 255, 204, 0.1); border: 1px solid rgba(0, 255, 204, 0.3); }
        .card-sales .card-icon { background: rgba(255, 107, 53, 0.15); border: 1px solid rgba(255, 107, 53, 0.3); }
        .card-biz .card-icon { background: rgba(168, 85, 247, 0.15); border: 1px solid rgba(168, 85, 247, 0.3); }
        .card-admin .card-icon { background: rgba(251, 191, 36, 0.15); border: 1px solid rgba(251, 191, 36, 0.3); }

        .card-code {
            font-family: 'Orbitron', sans-serif;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 3px;
        }

        .card-db .card-code { color: var(--neon-blue); }
        .card-history .card-code { color: #a855f7; }
        .card-pipeline .card-code { color: var(--neon-cyan); }
        .card-sales .card-code { color: #ff6b35; }
        .card-biz .card-code { color: #d8b4fe; }
        .card-admin .card-code { color: #fbbf24; }

        .card-title {
            font-size: 17px;
            font-weight: 700;
            line-height: 1.2;
        }

        .card-desc {
            font-size: 12px;
            color: var(--text-secondary);
            line-height: 1.4;
        }

        .card-arrow {
            margin-top: auto;
            font-size: 18px;
            opacity: 0;
            transform: translateX(-8px);
            transition: all 0.3s ease;
        }

        .menu-card:hover .card-arrow {
            opacity: 0.7;
            transform: translateX(0);
        }

        /* ===== TAX SECTION ===== */
        .section-wrapper {
            max-width: 1200px;
            width: 100%;
            margin: 0 auto;
            animation: fadeInUp 0.8s ease 0.7s both;
        }

        .section-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 16px;
        }

        .section-label {
            font-size: 10px;
            letter-spacing: 4px;
            color: var(--text-secondary);
        }

        .section-line {
            flex: 1;
            height: 1px;
            background: linear-gradient(90deg, rgba(255,255,255,0.1), transparent);
        }

        .tax-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }

        .tax-btn {
            padding: 10px 22px;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 30px;
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.3s ease;
            letter-spacing: 0.5px;
            position: relative;
            overflow: hidden;
        }

        .tax-btn::before {
            content: '';
            position: absolute;
            inset: 0;
            background: linear-gradient(135deg, var(--neon-blue), var(--neon-purple));
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .tax-btn span {
            position: relative;
            z-index: 1;
        }

        .tax-btn:hover {
            border-color: rgba(0, 212, 255, 0.4);
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3), 0 0 15px rgba(0, 212, 255, 0.1);
        }

        .tax-btn:hover::before {
            opacity: 0.15;
        }

        /* ===== FOOTER ===== */
        .footer {
            margin-top: 40px;
            padding-top: 24px;
            border-top: 1px solid rgba(255, 255, 255, 0.06);
            text-align: center;
        }

        .ys-footer-link {
            display: inline-flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
            text-decoration: none;
            opacity: 0.5;
            transition: all 0.3s ease;
        }

        .ys-footer-link:hover {
            opacity: 1;
            transform: translateY(-3px);
        }

        .ys-footer-link img {
            height: 24px;
            filter: brightness(0) invert(1) drop-shadow(0 0 6px rgba(0, 212, 255, 0.5));
        }

        .ys-footer-text {
            font-size: 10px;
            letter-spacing: 3px;
            color: var(--text-secondary);
        }

        /* ===== CORNER DECORATIONS ===== */
        .corner-deco {
            position: fixed;
            width: 80px;
            height: 80px;
            z-index: 5;
            pointer-events: none;
        }

        .corner-deco.tl {
            top: 20px;
            left: 20px;
            border-top: 1px solid rgba(0, 212, 255, 0.3);
            border-left: 1px solid rgba(0, 212, 255, 0.3);
        }

        .corner-deco.tr {
            top: 20px;
            right: 20px;
            border-top: 1px solid rgba(0, 212, 255, 0.3);
            border-right: 1px solid rgba(0, 212, 255, 0.3);
        }

        .corner-deco.bl {
            bottom: 20px;
            left: 20px;
            border-bottom: 1px solid rgba(0, 212, 255, 0.3);
            border-left: 1px solid rgba(0, 212, 255, 0.3);
        }

        .corner-deco.br {
            bottom: 20px;
            right: 20px;
            border-bottom: 1px solid rgba(0, 212, 255, 0.3);
            border-right: 1px solid rgba(0, 212, 255, 0.3);
        }

        /* ===== FLOATING ORBS ===== */
        .orb {
            position: fixed;
            border-radius: 50%;
            filter: blur(80px);
            pointer-events: none;
            z-index: 1;
            animation: orbFloat 8s ease-in-out infinite;
        }

        .orb-1 {
            width: 400px;
            height: 400px;
            background: rgba(0, 212, 255, 0.06);
            top: -100px;
            right: -100px;
            animation-delay: 0s;
        }

        .orb-2 {
            width: 300px;
            height: 300px;
            background: rgba(123, 47, 255, 0.08);
            bottom: -80px;
            left: -80px;
            animation-delay: -4s;
        }

        .orb-3 {
            width: 200px;
            height: 200px;
            background: rgba(0, 255, 204, 0.05);
            top: 40%;
            left: 30%;
            animation-delay: -2s;
        }

        @keyframes orbFloat {
            0%, 100% { transform: translate(0, 0) scale(1); }
            33% { transform: translate(30px, -20px) scale(1.05); }
            66% { transform: translate(-20px, 30px) scale(0.95); }
        }

        /* ===== PARTICLE COUNT DISPLAY ===== */
        .hud-element {
            position: fixed;
            font-family: 'Orbitron', sans-serif;
            font-size: 9px;
            color: rgba(0, 212, 255, 0.25);
            letter-spacing: 1px;
            pointer-events: none;
            z-index: 5;
        }

        .hud-tl { top: 110px; left: 28px; }
        .hud-tr { top: 110px; right: 28px; text-align: right; }

        @media (max-width: 768px) {
            .menu-grid { grid-template-columns: repeat(2, 1fr); }
            .hero-title { font-size: 32px; }
            .topbar { flex-wrap: wrap; gap: 12px; }
            .corner-deco, .hud-element { display: none; }
        }

        @media (max-width: 480px) {
            .menu-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>

<body>

    <!-- Particle Canvas -->
    <canvas id="particle-canvas"></canvas>

    <!-- Overlays -->
    <div class="bg-overlay"></div>
    <div class="scanlines"></div>

    <!-- Floating Orbs -->
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    <div class="orb orb-3"></div>

    <!-- Corner Decorations -->
    <div class="corner-deco tl"></div>
    <div class="corner-deco tr"></div>
    <div class="corner-deco bl"></div>
    <div class="corner-deco br"></div>

    <!-- HUD Elements -->
    <div class="hud-element hud-tl">SYS // CMS v2.0<br>QUANTUM CORE ONLINE</div>
    <div class="hud-element hud-tr">STATUS // SECURE<br>NODE 127.0.0.1</div>

    <!-- Main Content -->
    <div class="main-wrapper">

        <!-- Top Bar -->
        <div class="topbar">
            <div class="logo-group">
                <div class="logo-icon">CMS</div>
                <div class="logo-text">
                    <div class="logo-name">CMS</div>
                    <div class="logo-sub">기업 관리 시스템</div>
                </div>
            </div>

            <div class="status-bar">
                <div class="status-dot"></div>
                <span class="status-text">SYSTEM ONLINE</span>
            </div>

            <div class="user-panel">
                <div class="user-info">
                    <div class="user-name">{{ user_name }}님</div>
                    <div class="user-level">{{ user_level_name }}</div>
                </div>

                {% if subscription_info %}
                    {% if subscription_info.days_remaining > 0 %}
                        {% if subscription_info.days_remaining <= 7 %}
                        <span class="subscription-badge warning">D-{{ subscription_info.days_remaining }}</span>
                        {% else %}
                        <span class="subscription-badge normal">{{ subscription_info.days_remaining }}일</span>
                        {% endif %}
                    {% else %}
                    <span class="subscription-badge expired">만료</span>
                    {% endif %}
                {% else %}
                <span class="subscription-badge normal">FREE</span>
                {% endif %}

                <div class="action-btns">
                    {% if can_manage_users %}
                    <button onclick="openDbManagementPopup()" class="btn-topbar btn-db">DB 관리</button>
                    {% endif %}
                    <a href="{{ url_for('logout') }}" class="btn-topbar btn-logout">로그아웃</a>
                </div>
            </div>
        </div>

        <!-- Hero Section -->
        <div class="hero">
            <div class="hero-label">CORPORATE MANAGEMENT SYSTEM</div>
            <h1 class="hero-title">CMS</h1>
            <p class="hero-subtitle">기업 관리 시스템 · 데이터 기반 경영 플랫폼</p>
        </div>

        <div class="neon-divider"></div>

        <!-- Main Menu -->
        <p class="menu-section-title">MAIN MODULES</p>
        <div class="menu-grid">

            <a href="/" class="menu-card card-db">
                <div class="card-icon">🗄️</div>
                <div class="card-code">DATABASE</div>
                <div class="card-title">기업정보 조회</div>
                <div class="card-desc">기업 데이터베이스 검색 및 분석</div>
                <div class="card-arrow">→</div>
            </a>

            <a href="/history" class="menu-card card-history">
                <div class="card-icon">📋</div>
                <div class="card-code">HISTORY</div>
                <div class="card-title">접촉이력 조회</div>
                <div class="card-desc">접촉 이력 검색 및 관리</div>
                <div class="card-arrow">→</div>
            </a>

            <a href="/pipeline" class="menu-card card-pipeline">
                <div class="card-icon">📈</div>
                <div class="card-code">PIPELINE</div>
                <div class="card-title">영업 파이프라인</div>
                <div class="card-desc">관심 기업 관리 및 현황</div>
                <div class="card-arrow">→</div>
            </a>

            <a href="/sales_management" class="menu-card card-sales">
                <div class="card-icon">💼</div>
                <div class="card-code">SALES</div>
                <div class="card-title">영업관리</div>
                <div class="card-desc">개척 등록 및 비용 관리</div>
                <div class="card-arrow">→</div>
            </a>

            <a href="/individual_businesses" class="menu-card card-biz">
                <div class="card-icon">🔄</div>
                <div class="card-code">BIZ TRANS</div>
                <div class="card-title">개인사업자<br>법인전환 관리</div>
                <div class="card-desc">1월~3월 대상 법인전환</div>
                <div class="card-arrow">→</div>
            </a>

            {% if can_manage_users %}
            <a href="/user_management" class="menu-card card-admin">
                <div class="card-icon">⚙️</div>
                <div class="card-code">ADMIN</div>
                <div class="card-title">사용자 관리</div>
                <div class="card-desc">사용자 및 구독 관리</div>
                <div class="card-arrow">→</div>
            </a>
            {% endif %}

        </div>

        <!-- Tax Calculator Section -->
        <div class="section-wrapper">
            <div class="section-header">
                <span class="section-label">TAX CALCULATOR</span>
                <div class="section-line"></div>
                <span class="section-label">세금 계산기</span>
            </div>
            <div class="tax-grid">
                <a href="/inheritance_tax" class="tax-btn"><span>상속세</span></a>
                <a href="/gift_tax" class="tax-btn"><span>증여세</span></a>
                <a href="/transfer_tax" class="tax-btn"><span>양도세</span></a>
                <a href="/income_tax" class="tax-btn"><span>종합소득세</span></a>
                <a href="/social_ins_tax" class="tax-btn"><span>4대보험</span></a>
                <a href="/acquisition_tax" class="tax-btn"><span>취득세</span></a>
                <a href="/retirement_pay" class="tax-btn"><span>퇴직금</span></a>
                <a href="/industrial_accident" class="tax-btn"><span>산재보상</span></a>
            </div>
        </div>

        <!-- Footer -->
        <div class="footer">
            <a href="/lys" class="ys-footer-link">
                <img src="/static/images/logo.png" alt="YS Honers">
                <span class="ys-footer-text">YS Honers</span>
            </a>
        </div>

    </div>

    <script>
    // ===== PARTICLE SYSTEM =====
    (function() {
        const canvas = document.getElementById('particle-canvas');
        const ctx = canvas.getContext('2d');

        let W, H, particles = [], mouse = { x: -9999, y: -9999 };
        const PARTICLE_COUNT = 120;
        const CONNECTION_DIST = 150;
        const MOUSE_REPEL_DIST = 120;

        function resize() {
            W = canvas.width = window.innerWidth;
            H = canvas.height = window.innerHeight;
        }

        class Particle {
            constructor() { this.reset(true); }

            reset(initial) {
                this.x = Math.random() * W;
                this.y = initial ? Math.random() * H : -10;
                this.vx = (Math.random() - 0.5) * 0.4;
                this.vy = (Math.random() - 0.5) * 0.4;
                this.r = Math.random() * 1.8 + 0.5;
                this.alpha = Math.random() * 0.6 + 0.2;
                this.pulse = Math.random() * Math.PI * 2;
                this.pulseSpeed = Math.random() * 0.02 + 0.005;

                // Color variety
                const types = [
                    [0, 212, 255],    // neon blue
                    [123, 47, 255],   // neon purple
                    [0, 255, 204],    // neon cyan
                    [255, 255, 255],  // white
                ];
                this.color = types[Math.floor(Math.random() * types.length)];
            }

            update() {
                this.pulse += this.pulseSpeed;

                // Mouse repulsion
                const dx = this.x - mouse.x;
                const dy = this.y - mouse.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < MOUSE_REPEL_DIST && dist > 0) {
                    const force = (MOUSE_REPEL_DIST - dist) / MOUSE_REPEL_DIST;
                    this.vx += (dx / dist) * force * 0.8;
                    this.vy += (dy / dist) * force * 0.8;
                }

                // Damping
                this.vx *= 0.98;
                this.vy *= 0.98;

                // Base drift
                this.x += this.vx + Math.sin(this.pulse * 0.3) * 0.2;
                this.y += this.vy + Math.cos(this.pulse * 0.2) * 0.15;

                // Wrap around
                if (this.x < -10) this.x = W + 10;
                if (this.x > W + 10) this.x = -10;
                if (this.y < -10) this.y = H + 10;
                if (this.y > H + 10) this.y = -10;
            }

            draw() {
                const [r, g, b] = this.color;
                const pAlpha = this.alpha * (0.7 + 0.3 * Math.sin(this.pulse));

                ctx.beginPath();
                ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);

                // Glow
                const gradient = ctx.createRadialGradient(this.x, this.y, 0, this.x, this.y, this.r * 3);
                gradient.addColorStop(0, `rgba(${r},${g},${b},${pAlpha})`);
                gradient.addColorStop(1, `rgba(${r},${g},${b},0)`);

                ctx.fillStyle = gradient;
                ctx.fill();

                // Core dot
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.r * 0.5, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(${r},${g},${b},${pAlpha * 1.5})`;
                ctx.fill();
            }
        }

        function drawConnections() {
            for (let i = 0; i < particles.length; i++) {
                for (let j = i + 1; j < particles.length; j++) {
                    const dx = particles[i].x - particles[j].x;
                    const dy = particles[i].y - particles[j].y;
                    const dist = Math.sqrt(dx * dx + dy * dy);

                    if (dist < CONNECTION_DIST) {
                        const alpha = (1 - dist / CONNECTION_DIST) * 0.25;
                        const [r1, g1, b1] = particles[i].color;
                        const [r2, g2, b2] = particles[j].color;

                        const gradient = ctx.createLinearGradient(
                            particles[i].x, particles[i].y,
                            particles[j].x, particles[j].y
                        );
                        gradient.addColorStop(0, `rgba(${r1},${g1},${b1},${alpha})`);
                        gradient.addColorStop(1, `rgba(${r2},${g2},${b2},${alpha})`);

                        ctx.beginPath();
                        ctx.moveTo(particles[i].x, particles[i].y);
                        ctx.lineTo(particles[j].x, particles[j].y);
                        ctx.strokeStyle = gradient;
                        ctx.lineWidth = 0.5;
                        ctx.stroke();
                    }
                }
            }
        }

        // Mouse connection lines
        function drawMouseConnections() {
            particles.forEach(p => {
                const dx = p.x - mouse.x;
                const dy = p.y - mouse.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 200) {
                    const alpha = (1 - dist / 200) * 0.5;
                    const [r, g, b] = p.color;

                    ctx.beginPath();
                    ctx.moveTo(mouse.x, mouse.y);
                    ctx.lineTo(p.x, p.y);
                    ctx.strokeStyle = `rgba(${r},${g},${b},${alpha})`;
                    ctx.lineWidth = 0.8;
                    ctx.stroke();
                }
            });
        }

        function animate() {
            ctx.clearRect(0, 0, W, H);
            drawConnections();
            drawMouseConnections();
            particles.forEach(p => { p.update(); p.draw(); });
            requestAnimationFrame(animate);
        }

        function init() {
            resize();
            particles = Array.from({ length: PARTICLE_COUNT }, () => new Particle());
            animate();
        }

        window.addEventListener('resize', resize);
        window.addEventListener('mousemove', e => {
            mouse.x = e.clientX;
            mouse.y = e.clientY;
        });
        window.addEventListener('mouseleave', () => {
            mouse.x = -9999;
            mouse.y = -9999;
        });

        init();
    })();

    // ===== CARD ENTRANCE ANIMATION =====
    const cards = document.querySelectorAll('.menu-card');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry, i) => {
            if (entry.isIntersecting) {
                setTimeout(() => {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }, i * 80);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    cards.forEach((card, i) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 0.4s ease, border-color 0.4s ease, background 0.4s ease, scale 0.4s ease';
        observer.observe(card);
    });

    // ===== DB POPUP =====
    function openDbManagementPopup() {
        window.open('/db_management', 'dbManagement', 'width=900,height=700,scrollbars=yes,resizable=yes');
    }

    // ===== TYPEWRITER EFFECT for HUD =====
    (function() {
        const dateEl = document.querySelector('.hud-tr');
        if (dateEl) {
            const now = new Date();
            const dateStr = now.toISOString().slice(0, 10).replace(/-/g, '.');
            dateEl.innerHTML = 'STATUS // SECURE<br>DATE // ' + dateStr;
        }
    })();
    </script>

</body>
</html>
'''

output_path = r"g:\\company_project_system\\templates\\main.html"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(main_html)

print(f"완료: main.html 저장됨 ({os.path.getsize(output_path):,} bytes)")
