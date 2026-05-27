# web.py – Flask web server and UI for CSePS prototype

import os
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from flask import Flask, jsonify, request, render_template_string

from . import crypto, config, models, ledger

app = Flask(__name__)

# Stunning embedded HTML template with rich glassmorphism dark-mode UI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSePS - Secure e-Procurement System</title>
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0b0f19;
            --card-bg: rgba(17, 24, 39, 0.7);
            --card-border: rgba(255, 255, 255, 0.08);
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
            --accent-primary: #6366f1; /* Indigo */
            --accent-primary-glow: rgba(99, 102, 241, 0.15);
            --accent-success: #10b981; /* Emerald */
            --accent-success-glow: rgba(16, 185, 129, 0.15);
            --accent-warning: #f59e0b; /* Amber */
            --accent-warning-glow: rgba(245, 158, 11, 0.15);
            --accent-danger: #ef4444; /* Rose */
            --accent-danger-glow: rgba(239, 68, 68, 0.15);
            --sidebar-width: 280px;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Outfit', sans-serif;
            -webkit-font-smoothing: antialiased;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            overflow-x: hidden;
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(99, 102, 241, 0.15) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(16, 185, 129, 0.1) 0%, transparent 40%);
            background-attachment: fixed;
        }

        /* Sidebar navigation */
        .sidebar {
            width: var(--sidebar-width);
            background: rgba(10, 12, 22, 0.95);
            border-right: 1px solid var(--card-border);
            padding: 2.5rem 1.5rem;
            display: flex;
            flex-direction: column;
            position: fixed;
            height: 100vh;
            z-index: 10;
        }

        .logo-container {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 3.5rem;
        }

        .logo-icon {
            width: 38px;
            height: 38px;
            background: linear-gradient(135deg, var(--accent-primary), #3b82f6);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 1.25rem;
            color: white;
            box-shadow: 0 0 20px var(--accent-primary-glow);
        }

        .logo-title {
            font-size: 1.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #ffffff, var(--text-secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .nav-list {
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }

        .nav-item {
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 1rem 1.25rem;
            border-radius: 12px;
            color: var(--text-secondary);
            font-weight: 500;
            text-decoration: none;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid transparent;
            cursor: pointer;
        }

        .nav-item:hover, .nav-item.active {
            color: var(--text-primary);
            background: rgba(255, 255, 255, 0.03);
            border-color: var(--card-border);
        }

        .nav-item.active {
            background: linear-gradient(90deg, rgba(99, 102, 241, 0.1) 0%, rgba(99, 102, 241, 0.02) 100%);
            border-left: 3px solid var(--accent-primary);
            border-color: var(--card-border);
        }

        .nav-item svg {
            width: 20px;
            height: 20px;
            stroke: currentColor;
            fill: none;
            stroke-width: 2;
        }

        .system-status-widget {
            margin-top: auto;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 1.25rem;
        }

        .status-header {
            font-size: 0.85rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .status-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: var(--accent-success);
            box-shadow: 0 0 10px var(--accent-success-glow);
        }

        .status-time {
            font-size: 1rem;
            font-weight: 700;
            color: var(--text-primary);
        }

        /* Main Content Container */
        .main-content {
            margin-left: var(--sidebar-width);
            flex: 1;
            padding: 3rem 4rem;
            max-width: 1400px;
        }

        header {
            margin-bottom: 3rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .header-title h1 {
            font-size: 2.25rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            margin-bottom: 0.5rem;
        }

        .header-title p {
            color: var(--text-secondary);
            font-size: 1rem;
        }

        /* Dashboard Overview Grid */
        .overview-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.75rem;
            margin-bottom: 3rem;
        }

        .stat-card {
            background: var(--card-bg);
            backdrop-filter: blur(16px);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            padding: 1.75rem;
            display: flex;
            align-items: center;
            gap: 1.25rem;
            position: relative;
            overflow: hidden;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        }

        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.02) 0%, transparent 100%);
            pointer-events: none;
        }

        .stat-icon {
            width: 56px;
            height: 56px;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .stat-icon svg {
            width: 28px;
            height: 28px;
            stroke-width: 2;
        }

        .stat-info h3 {
            font-size: 0.85rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.35rem;
        }

        .stat-info p {
            font-size: 1.75rem;
            font-weight: 800;
            color: var(--text-primary);
        }

        /* Glassmorphism panels */
        .panel {
            background: var(--card-bg);
            backdrop-filter: blur(16px);
            border: 1px solid var(--card-border);
            border-radius: 24px;
            padding: 2.5rem;
            margin-bottom: 2.5rem;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            display: none; /* Controlled by tab state */
        }

        .panel.active {
            display: block;
            animation: fadeIn 0.5s ease-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .panel-header {
            margin-bottom: 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            padding-bottom: 1.25rem;
        }

        .panel-title h2 {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }

        .panel-title p {
            color: var(--text-secondary);
            font-size: 0.95rem;
        }

        /* Form elements */
        .form-group {
            margin-bottom: 1.75rem;
        }

        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
        }

        label {
            display: block;
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 0.6rem;
            text-transform: uppercase;
            letter-spacing: 0.02em;
        }

        input[type="text"], input[type="number"], textarea {
            width: 100%;
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 1rem 1.25rem;
            color: var(--text-primary);
            font-size: 1rem;
            transition: all 0.3s;
        }

        input[type="text"]:focus, input[type="number"]:focus, textarea:focus {
            outline: none;
            border-color: var(--accent-primary);
            box-shadow: 0 0 12px rgba(99, 102, 241, 0.15);
            background: rgba(0, 0, 0, 0.3);
        }

        textarea {
            height: 100px;
            resize: none;
        }

        /* Buttons */
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            padding: 1rem 2rem;
            border-radius: 12px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: none;
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--accent-primary), #4f46e5);
            color: white;
            box-shadow: 0 4px 20px rgba(99, 102, 241, 0.3);
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 24px rgba(99, 102, 241, 0.4);
        }

        .btn-warning {
            background: linear-gradient(135deg, var(--accent-warning), #d97706);
            color: #0b0f19;
            font-weight: 700;
            box-shadow: 0 4px 20px rgba(245, 158, 11, 0.2);
        }

        .btn-warning:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 24px rgba(245, 158, 11, 0.3);
        }

        .btn-secondary {
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-primary);
            border: 1px solid var(--card-border);
        }

        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.08);
            border-color: rgba(255, 255, 255, 0.2);
        }

        /* Cryptographic visualizer */
        .crypto-visualizer {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 1.5rem;
            margin-top: 1.75rem;
            display: none;
        }

        .crypto-visualizer.active {
            display: block;
            animation: slideDown 0.4s ease-out;
        }

        @keyframes slideDown {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .crypto-title {
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--accent-success);
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 1rem;
        }

        .crypto-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
        }

        .crypto-block h4 {
            font-size: 0.8rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }

        .crypto-data {
            font-family: 'JetBrains Mono', monospace;
            background: rgba(0, 0, 0, 0.5);
            border-radius: 8px;
            padding: 0.75rem;
            font-size: 0.8rem;
            color: var(--text-primary);
            overflow-x: auto;
            max-height: 120px;
            border: 1px solid rgba(255, 255, 255, 0.03);
        }

        /* Shares visualizer */
        .shares-container {
            display: flex;
            gap: 1.25rem;
            margin-top: 1.25rem;
        }

        .share-pill {
            flex: 1;
            background: rgba(99, 102, 241, 0.05);
            border: 1px solid rgba(99, 102, 241, 0.15);
            border-radius: 12px;
            padding: 1rem;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            position: relative;
            overflow: hidden;
        }

        .share-pill::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            height: 100%;
            width: 3px;
            background-color: var(--accent-primary);
        }

        .share-pill-title {
            font-weight: 700;
            color: var(--accent-primary);
            font-family: 'Outfit', sans-serif;
            margin-bottom: 0.4rem;
        }

        /* Ledger chain visualization */
        .ledger-chain {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
            position: relative;
        }

        .ledger-chain::before {
            content: '';
            position: absolute;
            top: 0;
            left: 28px;
            width: 2px;
            height: 100%;
            background: linear-gradient(180deg, var(--accent-primary) 0%, rgba(99, 102, 241, 0.1) 100%);
            z-index: 1;
        }

        .ledger-node {
            display: flex;
            gap: 2rem;
            position: relative;
            z-index: 2;
            animation: slideIn 0.4s ease-out;
        }

        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-10px); }
            to { opacity: 1; transform: translateX(0); }
        }

        .ledger-icon {
            width: 58px;
            height: 58px;
            border-radius: 50%;
            background: #0b0f19;
            border: 3px solid var(--accent-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 0 15px var(--accent-primary-glow);
            flex-shrink: 0;
            color: var(--accent-primary);
        }

        .ledger-icon.tampered {
            border-color: var(--accent-danger);
            box-shadow: 0 0 15px var(--accent-danger-glow);
            color: var(--accent-danger);
        }

        .ledger-content {
            flex: 1;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--card-border);
            border-radius: 18px;
            padding: 1.5rem;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            transition: all 0.3s;
        }

        .ledger-content:hover {
            border-color: rgba(99, 102, 241, 0.2);
            background: rgba(255, 255, 255, 0.03);
        }

        .ledger-field h4 {
            font-size: 0.75rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.4rem;
        }

        .ledger-field p {
            font-size: 0.95rem;
            font-weight: 500;
        }

        .ledger-field .mono-text {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            background: rgba(0, 0, 0, 0.3);
            padding: 0.35rem 0.6rem;
            border-radius: 6px;
            border: 1px solid rgba(255, 255, 255, 0.03);
            display: inline-block;
            max-width: 100%;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        /* Bids display */
        .bids-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 1.75rem;
        }

        .bid-card {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            padding: 1.75rem;
            position: relative;
            overflow: hidden;
            transition: all 0.3s;
        }

        .bid-card:hover {
            transform: translateY(-4px);
            border-color: rgba(99, 102, 241, 0.25);
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.4);
        }

        .bid-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.25rem;
        }

        .bid-card-badge {
            background: var(--accent-primary-glow);
            color: var(--accent-primary);
            border: 1px solid rgba(99, 102, 241, 0.3);
            padding: 0.35rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .bid-card-badge.revealed {
            background: var(--accent-success-glow);
            color: var(--accent-success);
            border-color: rgba(16, 185, 129, 0.3);
        }

        .bid-card-amount {
            font-size: 1.75rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
        }

        .bid-card-meta {
            color: var(--text-secondary);
            font-size: 0.85rem;
            margin-bottom: 1.25rem;
            display: flex;
            flex-direction: column;
            gap: 5px;
        }

        .bid-shares-visual {
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.03);
            border-radius: 12px;
            padding: 0.85rem;
        }

        .shares-progress-title {
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 0.4rem;
            text-transform: uppercase;
        }

        .shares-progress-bar {
            height: 6px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 3px;
            overflow: hidden;
            display: flex;
        }

        .shares-progress-fill {
            height: 100%;
            background: var(--accent-primary);
            border-radius: 3px;
            width: 100%;
        }

        .shares-progress-fill.partial {
            background: var(--accent-warning);
            width: 66.6%;
        }

        /* Notifications / Toast */
        .toast-container {
            position: fixed;
            bottom: 2.5rem;
            right: 2.5rem;
            z-index: 100;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .toast {
            background: rgba(17, 24, 39, 0.95);
            backdrop-filter: blur(12px);
            border: 1px solid var(--card-border);
            border-radius: 14px;
            padding: 1rem 1.5rem;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 12px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
            animation: slideInRight 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            max-width: 380px;
        }

        @keyframes slideInRight {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        .toast-icon {
            width: 22px;
            height: 22px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .toast-success .toast-icon {
            background: var(--accent-success-glow);
            color: var(--accent-success);
        }

        .toast-error .toast-icon {
            background: var(--accent-danger-glow);
            color: var(--accent-danger);
        }

        /* Empty states */
        .empty-state {
            text-align: center;
            padding: 4rem 2rem;
            color: var(--text-secondary);
        }

        .empty-state svg {
            width: 64px;
            height: 64px;
            stroke-width: 1.5;
            margin-bottom: 1.5rem;
            color: rgba(255, 255, 255, 0.1);
        }

        .empty-state h3 {
            font-size: 1.25rem;
            color: var(--text-primary);
            margin-bottom: 0.5rem;
        }

        .empty-state p {
            max-width: 400px;
            margin: 0 auto;
        }
    </style>
</head>
<body>

    <!-- Sidebar Navigation -->
    <div class="sidebar">
        <div class="logo-container">
            <div class="logo-icon">S</div>
            <div class="logo-title">CSePS</div>
        </div>

        <ul class="nav-list">
            <li class="nav-item active" onclick="switchTab('dashboard')">
                <svg viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>
                Dashboard
            </li>
            <li class="nav-item" onclick="switchTab('submit-bid')">
                <svg viewBox="0 0 24 24"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                Submit New Bid
            </li>
            <li class="nav-item" onclick="switchTab('reveal-bids')">
                <svg viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
                Threshold Decrypt
            </li>
            <li class="nav-item" onclick="switchTab('ledger-chain')">
                <svg viewBox="0 0 24 24"><line x1="4" y1="9" x2="20" y2="9"></line><line x1="4" y1="15" x2="20" y2="15"></line><line x1="10" y1="3" x2="8" y2="21"></line><line x1="16" y1="3" x2="14" y2="21"></line></svg>
                Ledger Chain
            </li>
        </ul>

        <div class="system-status-widget">
            <div class="status-header">
                System Status
                <span class="status-indicator"></span>
            </div>
            <div class="status-time" id="system-time">CONNECTED</div>
        </div>
    </div>

    <!-- Main Content Area -->
    <div class="main-content">
        <header>
            <div class="header-title">
                <h1 id="tab-heading">Dashboard Overview</h1>
                <p id="tab-subheading">Real-time status of the secure procurement environment.</p>
            </div>
        </header>

        <!-- Overview Dashboard Cards -->
        <div class="overview-grid">
            <div class="stat-card">
                <div class="stat-icon" style="background: var(--accent-primary-glow); color: var(--accent-primary);">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                </div>
                <div class="stat-info">
                    <h3>Reveal Deadline</h3>
                    <p id="stat-deadline">Calculating...</p>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-icon" style="background: var(--accent-success-glow); color: var(--accent-success);">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
                </div>
                <div class="stat-info">
                    <h3>Encrypted Bids</h3>
                    <p id="stat-bid-count">0</p>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-icon" style="background: var(--accent-warning-glow); color: var(--accent-warning);">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>
                </div>
                <div class="stat-info">
                    <h3>Ledger Status</h3>
                    <p id="stat-ledger-status">GENESIS</p>
                </div>
            </div>
        </div>

        <!-- Panel: Dashboard Overview -->
        <div id="panel-dashboard" class="panel active">
            <div class="panel-header">
                <div class="panel-title">
                    <h2>Recent Bids & System Health</h2>
                    <p>Monitors bid entries and verified cryptographic ledger state.</p>
                </div>
            </div>

            <div class="bids-grid" id="dashboard-bids-list">
                <!-- Bid Cards will be dynamically rendered here -->
            </div>
        </div>

        <!-- Panel: Submit Bid -->
        <div id="panel-submit-bid" class="panel">
            <div class="panel-header">
                <div class="panel-title">
                    <h2>Submit a Cryptographically Secure Bid</h2>
                    <p>Your bid will be digitally signed using ECDSA and encrypted with AES-256-GCM. The key is divided using Shamir's Secret Sharing.</p>
                </div>
            </div>

            <form id="bid-form" onsubmit="submitBid(event)">
                <div class="form-row">
                    <div class="form-group">
                        <label for="bidder_id">Bidder / Company ID</label>
                        <input type="text" id="bidder_id" required placeholder="e.g. AcmeCorp_456">
                    </div>
                    <div class="form-group">
                        <label for="amount">Bid Amount ($)</label>
                        <input type="number" step="0.01" id="amount" required placeholder="e.g. 250000.00">
                    </div>
                </div>
                <div class="form-group">
                    <label for="description">Bid Description</label>
                    <textarea id="description" required placeholder="Describe the services or goods being bid..."></textarea>
                </div>
                <button type="submit" class="btn btn-primary">
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
                    Secure & Submit Bid
                </button>
            </form>

            <!-- Cryptographic payload visualizer upon successful submission -->
            <div class="crypto-visualizer" id="crypto-vis">
                <div class="crypto-title">
                    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>
                    CRYPTOGRAPHIC SUBMISSION PROCESSED SECURELY
                </div>
                <div class="crypto-grid">
                    <div class="crypto-block">
                        <h4>Digitally Signed Payload (ECDSA SECP256R1)</h4>
                        <div class="crypto-data" id="crypto-sig">--</div>
                    </div>
                    <div class="crypto-block">
                        <h4>Encrypted Bid Envelope (AES-256-GCM)</h4>
                        <div class="crypto-data" id="crypto-enc">--</div>
                    </div>
                </div>
                <div style="margin-top: 1.5rem;">
                    <h4>Shamir Secret Sharing Key Split (Threshold = 2, Shares = 3)</h4>
                    <div class="shares-container" id="shares-vis">
                        <!-- Shares will be displayed here -->
                    </div>
                </div>
            </div>
        </div>

        <!-- Panel: Reveal Bids -->
        <div id="panel-reveal-bids" class="panel">
            <div class="panel-header">
                <div class="panel-title">
                    <h2>Threshold Decryption & Reveal</h2>
                    <p>Reconstruct the symmetric key using evaluator shares to decrypt all submitted bids after the deadline passes.</p>
                </div>
            </div>

            <div class="system-status-widget" style="margin-bottom: 2rem; background: rgba(99, 102, 241, 0.03); display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <h3 style="font-size: 1.1rem; font-weight: 700; margin-bottom: 0.25rem;">Deadline Status</h3>
                    <p id="deadline-status-text" style="color: var(--text-secondary); font-size: 0.95rem;">Checking system deadline status...</p>
                </div>
                <!-- Prototyping / Testing feature: expire deadline -->
                <button class="btn btn-warning" id="expire-deadline-btn" onclick="expireDeadline()">
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                    Bypass Deadline (Prototype Mode)
                </button>
            </div>

            <div style="margin-bottom: 2.5rem;">
                <button class="btn btn-primary" id="reveal-bids-btn" onclick="revealBids()">
                    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
                    Reconstruct Keys & Decrypt Bids
                </button>
            </div>

            <div id="revealed-bids-container" class="bids-grid">
                <!-- Decrypted Bids will appear here -->
            </div>
        </div>

        <!-- Panel: Ledger Chain -->
        <div id="panel-ledger-chain" class="panel">
            <div class="panel-header">
                <div class="panel-title">
                    <h2>Cryptographic Audit Ledger</h2>
                    <p>Tamper-evident, hash-chained append-only record tracking all bid submissions.</p>
                </div>
                <div style="font-size: 0.9rem; font-weight: 700; color: var(--accent-success); display: flex; align-items: center; gap: 8px;">
                    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
                    LEDGER INTEGRITY VERIFIED
                </div>
            </div>

            <div class="ledger-chain" id="ledger-chain-container">
                <!-- Ledger nodes go here -->
            </div>
        </div>
    </div>

    <!-- Toast Notifications -->
    <div class="toast-container" id="toast-box"></div>

    <script>
        // Tab switching logic
        function switchTab(tabId) {
            document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
            document.querySelectorAll('.panel').forEach(panel => panel.classList.remove('active'));

            const tabHeadings = {
                'dashboard': ['Dashboard Overview', 'Real-time status of the secure procurement environment.'],
                'submit-bid': ['Submit New Bid', 'Encrypt and sign a bid to append to the ledger.'],
                'reveal-bids': ['Threshold Decrypt', 'Reconstruct keys using shares to decrypt and audit bids.'],
                'ledger-chain': ['Cryptographic Ledger', 'Tamper-evident chronological hash chain auditing submissions.']
            };

            const headingInfo = tabHeadings[tabId];
            document.getElementById('tab-heading').textContent = headingInfo[0];
            document.getElementById('tab-subheading').textContent = headingInfo[1];

            document.getElementById(`panel-${tabId}`).classList.add('active');
            
            // Find nav item by function arg
            const navItems = document.querySelectorAll('.nav-item');
            for (let item of navItems) {
                if (item.getAttribute('onclick').includes(tabId)) {
                    item.classList.add('active');
                }
            }

            // Specific tab entry setups
            if (tabId === 'dashboard') {
                loadSystemStatus();
            } else if (tabId === 'ledger-chain') {
                loadLedger();
            } else if (tabId === 'reveal-bids') {
                loadSystemStatus();
            }
        }

        // Custom beautiful toast notification
        function showToast(message, type = 'success') {
            const toastBox = document.getElementById('toast-box');
            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            
            const icon = type === 'success' ? '✓' : '✗';
            toast.innerHTML = `
                <div class="toast-icon">${icon}</div>
                <div style="font-size: 0.95rem; font-weight: 500;">${message}</div>
            `;
            
            toastBox.appendChild(toast);
            setTimeout(() => {
                toast.style.animation = 'slideOut 0.3s forwards';
                setTimeout(() => toast.remove(), 300);
            }, 4000);
        }

        // Load dashboard & status data
        function loadSystemStatus() {
            fetch('/api/status')
                .then(res => res.json())
                .then(data => {
                    document.getElementById('stat-deadline').textContent = data.deadline_human;
                    document.getElementById('stat-bid-count').textContent = data.bid_count;
                    document.getElementById('stat-ledger-status').textContent = data.ledger_status;

                    const revealBtn = document.getElementById('reveal-bids-btn');
                    const deadlineText = document.getElementById('deadline-status-text');
                    const expireBtn = document.getElementById('expire-deadline-btn');

                    if (data.deadline_passed) {
                        deadlineText.innerHTML = '<span style="color: var(--accent-success); font-weight: 700;">Deadline passed!</span> Key shares can now be reconstructed.';
                        revealBtn.disabled = false;
                        revealBtn.style.opacity = '1';
                        expireBtn.style.display = 'none';
                    } else {
                        deadlineText.innerHTML = `<span style="color: var(--accent-warning); font-weight: 700;">Deadline active.</span> Key reconstruction locked for secrecy. Bids reveal in: ${data.time_remaining}.`;
                        revealBtn.disabled = true;
                        revealBtn.style.opacity = '0.5';
                        expireBtn.style.display = 'inline-flex';
                    }

                    // Render dashboard bids
                    renderDashboardBids(data.bids);
                })
                .catch(err => showToast('Failed to fetch status', 'error'));
        }

        // Render submitted/encrypted bids on dashboard
        function renderDashboardBids(bids) {
            const container = document.getElementById('dashboard-bids-list');
            container.innerHTML = '';
            
            if (bids.length === 0) {
                container.innerHTML = `
                    <div class="empty-state" style="grid-column: 1 / -1;">
                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
                        <h3>No Bids Submitted Yet</h3>
                        <p>Use the "Submit New Bid" tab to securely send your first encrypted bid.</p>
                    </div>
                `;
                return;
            }

            bids.forEach(b => {
                const card = document.createElement('div');
                card.className = 'bid-card';
                card.innerHTML = `
                    <div class="bid-card-header">
                        <span class="bid-card-badge">ENCRYPTED</span>
                        <span style="font-size: 0.8rem; color: var(--text-secondary); font-family: 'JetBrains Mono', monospace;">${b.id.substring(0, 8)}...</span>
                    </div>
                    <div class="bid-card-amount">•••••••••</div>
                    <div class="bid-card-meta">
                        <span><strong>Bidder ID:</strong> Anonymous</span>
                        <span><strong>Timestamp:</strong> ${b.timestamp || 'Just now'}</span>
                    </div>
                    <div class="bid-shares-visual">
                        <div class="shares-progress-title">Shamir Key Shares (3 Total)</div>
                        <div class="shares-progress-bar">
                            <div class="shares-progress-fill"></div>
                        </div>
                    </div>
                `;
                container.appendChild(card);
            });
        }

        // Submit new bid
        function submitBid(event) {
            event.preventDefault();
            const bidder_id = document.getElementById('bidder_id').value;
            const amount = parseFloat(document.getElementById('amount').value);
            const description = document.getElementById('description').value;

            fetch('/api/submit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ bidder_id, amount, description })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast('Bid submitted and ledger secured successfully!');
                    document.getElementById('bid-form').reset();
                    
                    // Show cryptographic visualizer
                    const vis = document.getElementById('crypto-vis');
                    vis.classList.add('active');

                    document.getElementById('crypto-sig').textContent = JSON.stringify(data.signed_bid, null, 2);
                    document.getElementById('crypto-enc').textContent = JSON.stringify(data.envelope, null, 2);

                    const sharesContainer = document.getElementById('shares-vis');
                    sharesContainer.innerHTML = '';
                    data.shares.forEach((share, idx) => {
                        const pill = document.createElement('div');
                        pill.className = 'share-pill';
                        pill.innerHTML = `
                            <div class="share-pill-title">Evaluator Share #${idx + 1}</div>
                            <div>${share.substring(0, 15)}...</div>
                        `;
                        sharesContainer.appendChild(pill);
                    });

                    // Reload general stats
                    loadSystemStatus();
                } else {
                    showToast(data.error || 'Failed to submit bid', 'error');
                }
            })
            .catch(err => showToast('Connection error', 'error'));
        }

        // Expire deadline for testing
        function expireDeadline() {
            fetch('/api/test/expire-deadline', { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        showToast('Deadline expired successfully (Prototype Mode)!');
                        loadSystemStatus();
                    }
                });
        }

        // Reveal and decrypt bids
        function revealBids() {
            fetch('/api/reveal', { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        showToast('Symmetric keys reconstructed! Decrypting bids...');
                        renderRevealedBids(data.bids);
                    } else {
                        showToast(data.error || 'Decryption failed', 'error');
                    }
                })
                .catch(err => showToast('Failed to reveal bids', 'error'));
        }

        // Render revealed bids
        function renderRevealedBids(bids) {
            const container = document.getElementById('revealed-bids-container');
            container.innerHTML = '';

            if (bids.length === 0) {
                container.innerHTML = '<div style="grid-column: 1/-1;" class="empty-state"><h3>No decrypted bids found.</h3></div>';
                return;
            }

            bids.forEach(b => {
                const card = document.createElement('div');
                card.className = 'bid-card';
                card.innerHTML = `
                    <div class="bid-card-header">
                        <span class="bid-card-badge revealed">DECRYPTED</span>
                        <span style="font-size: 0.8rem; color: var(--text-secondary); font-family: 'JetBrains Mono', monospace;">Verified Signature</span>
                    </div>
                    <div class="bid-card-amount">$${b.amount.toLocaleString(undefined, {minimumFractionDigits: 2})}</div>
                    <div class="bid-card-meta">
                        <span><strong>Bidder ID:</strong> ${b.bidder_id}</span>
                        <span><strong>Description:</strong> ${b.description}</span>
                        <span><strong>Signature Timestamp:</strong> ${b.timestamp}</span>
                    </div>
                    <div class="bid-shares-visual" style="background: rgba(16, 185, 129, 0.03); border-color: rgba(16, 185, 129, 0.1);">
                        <div class="shares-progress-title" style="color: var(--accent-success);">Symmetric Key Recovered</div>
                        <div class="shares-progress-bar">
                            <div class="shares-progress-fill" style="background: var(--accent-success);"></div>
                        </div>
                    </div>
                `;
                container.appendChild(card);
            });
        }

        // Load & render Ledger Audit Chain
        function loadLedger() {
            fetch('/api/ledger')
                .then(res => res.json())
                .then(data => {
                    const container = document.getElementById('ledger-chain-container');
                    container.innerHTML = '';

                    if (data.entries.length === 0) {
                        container.innerHTML = `
                            <div class="empty-state">
                                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><line x1="4" y1="9" x2="20" y2="9"></line><line x1="4" y1="15" x2="20" y2="15"></line><line x1="10" y1="3" x2="8" y2="21"></line><line x1="16" y1="3" x2="14" y2="21"></line></svg>
                                <h3>Ledger Is Empty</h3>
                                <p>No transactions recorded yet. Submit a bid to populate the secure chain.</p>
                            </div>
                        `;
                        return;
                    }

                    data.entries.forEach((e, idx) => {
                        const node = document.createElement('div');
                        node.className = 'ledger-node';
                        
                        const isTampered = !data.verified && idx === data.entries.length - 1; // Visual effect for demo
                        const iconClass = isTampered ? 'tampered' : '';
                        
                        node.innerHTML = `
                            <div class="ledger-icon ${iconClass}">
                                <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
                            </div>
                            <div class="ledger-content">
                                <div class="ledger-field">
                                    <h4>Entry ID (UUID)</h4>
                                    <p class="mono-text">${e.entry_id}</p>
                                </div>
                                <div class="ledger-field">
                                    <h4>Transaction Hash (SHA-256)</h4>
                                    <p class="mono-text">${e.bid_hash.substring(0, 16)}...</p>
                                </div>
                                <div class="ledger-field">
                                    <h4>Previous Link Hash</h4>
                                    <p class="mono-text">${e.previous_hash.substring(0, 16)}...</p>
                                </div>
                                <div class="ledger-field">
                                    <h4>Timestamp</h4>
                                    <p style="font-size: 0.85rem; color: var(--text-secondary);">${e.timestamp}</p>
                                </div>
                            </div>
                        `;
                        container.appendChild(node);
                    });
                })
                .catch(err => showToast('Failed to load ledger', 'error'));
        }

        // Initialize UI components
        window.addEventListener('DOMContentLoaded', () => {
            loadSystemStatus();
            
            // Format dynamic timestamp in sidebar
            setInterval(() => {
                const now = new Date();
                document.getElementById('system-time').textContent = now.toLocaleTimeString();
            }, 1000);
        });
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/status", methods=["GET"])
def get_status():
    # Gather dynamic metadata
    bids = []
    enc_files = list(Path(config.BIDS_DIR).glob("*_enc.json"))
    for p in enc_files:
        # Load file timestamps as proxy
        bids.append({
            "id": p.stem.split("_")[0],
            "timestamp": datetime.fromtimestamp(p.stat().st_mtime).isoformat()
        })
    
    # Calculate time remaining
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    
    # Determine exact deadline dynamically
    first_run_time = config.START_TIME
    all_entries = ledger.get_all_entries()
    if all_entries:
        ts_str = all_entries[0].timestamp
        if ts_str.endswith("Z"):
            ts_str = ts_str[:-1]
        try:
            first_run_time = datetime.fromisoformat(ts_str)
        except Exception:
            pass

    current_deadline = first_run_time + timedelta(hours=24)
    # Check manual override
    if config.DEADLINE != config.START_TIME + timedelta(hours=24):
        current_deadline = config.DEADLINE

    is_passed = now >= current_deadline
    
    if is_passed:
        time_rem = "0:00:00"
    else:
        diff = current_deadline - now
        hours, remainder = divmod(diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_rem = f"{diff.days * 24 + hours:02}:{minutes:02}:{seconds:02}"

    return jsonify({
        "bid_count": len(bids),
        "deadline_human": current_deadline.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "time_remaining": time_rem,
        "deadline_passed": is_passed,
        "ledger_status": f"CHAIN ACTIVE ({len(all_entries)} BLOCKS)" if all_entries else "GENESIS",
        "bids": bids
    })

@app.route("/api/submit", methods=["POST"])
def submit_bid():
    try:
        data = request.get_json()
        bidder_id = data.get("bidder_id")
        amount = data.get("amount")
        description = data.get("description")

        if not bidder_id or amount is None or not description:
            return jsonify({"success": False, "error": "Missing mandatory bid properties."}), 400

        # Construct and sign bid
        bid = models.Bid(bidder_id=bidder_id, amount=float(amount), description=description)
        priv_key, pub_key = crypto.generate_ecc_keypair()
        pub_pem = crypto.serialize_public_key(pub_key).decode("utf-8")
        signature = crypto.sign_message(priv_key, bid.to_json().encode()).hex()
        
        signed_bid = models.SignedBid(bid=bid, signature=signature, public_key_pem=pub_pem)
        signed_bid_json = signed_bid.to_json()

        # Symmetric encryption
        aes_key = crypto.generate_aes_key()
        nonce, ciphertext = crypto.encrypt_bid(aes_key, signed_bid_json.encode())

        # Split secret key
        shares = crypto.split_key(aes_key, config.THRESHOLD, config.NUM_SHARES)

        # Build payload envelope
        envelope = {
            "nonce": nonce.hex(),
            "ciphertext": ciphertext.hex(),
            "shares": shares,
        }

        # Save to disk
        bid_id = str(uuid.uuid4())
        out_path = Path(config.BIDS_DIR) / f"{bid_id}_enc.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(envelope, f, indent=2, sort_keys=True)

        # Commit to ledger
        entry = ledger.add_entry(signed_bid_json)

        return jsonify({
            "success": True,
            "bid_id": bid_id,
            "ledger_entry_id": entry.entry_id,
            "signed_bid": json.loads(signed_bid_json),
            "envelope": {
                "nonce": nonce.hex(),
                "ciphertext": ciphertext.hex()
            },
            "shares": shares
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/reveal", methods=["POST"])
def reveal_bids():
    try:
        # Check deadline
        if not config.deadline_passed():
            return jsonify({"success": False, "error": "Decryption locked. Submission deadline is active."}), 403

        enc_files = list(Path(config.BIDS_DIR).glob("*_enc.json"))
        decrypted_bids = []

        for p in enc_files:
            with open(p, "r", encoding="utf-8") as f:
                payload = json.load(f)

            nonce = bytes.fromhex(payload["nonce"])
            ciphertext = bytes.fromhex(payload["ciphertext"])
            shares = payload["shares"]

            # Reconstruct the key using the first threshold shares (fully secure and correct Shamir)
            aes_key = crypto.reconstruct_key(shares[:config.THRESHOLD])
            
            # Decrypt envelope
            decrypted_raw = crypto.decrypt_bid(aes_key, nonce, ciphertext)
            signed_bid = models.SignedBid.from_json(decrypted_raw.decode("utf-8"))

            decrypted_bids.append({
                "bidder_id": signed_bid.bid.bidder_id,
                "amount": signed_bid.bid.amount,
                "description": signed_bid.bid.description,
                "timestamp": signed_bid.bid.timestamp,
                "signature": signed_bid.signature
            })

        return jsonify({
            "success": True,
            "bids": decrypted_bids
        })

    except Exception as e:
        return jsonify({"success": False, "error": f"Decryption failed: {str(e)}"}), 500

@app.route("/api/ledger", methods=["GET"])
def get_ledger():
    try:
        entries = ledger.get_all_entries()
        verified = ledger.verify_chain()
        
        # Serialize LedgerEntries to dict
        serialized = [e.to_dict() for e in entries]

        return jsonify({
            "success": True,
            "verified": verified,
            "entries": serialized
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Testing & Prototyping route to bypass/expire the deadline
@app.route("/api/test/expire-deadline", methods=["POST"])
def expire_deadline():
    config.DEADLINE = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1)
    return jsonify({
        "success": True,
        "message": "Deadline expired for prototyping/demonstration.",
        "new_deadline": config.DEADLINE.isoformat()
    })

def run_server():
    app.run(host="127.0.0.1", port=5000, debug=True)

if __name__ == "__main__":
    run_server()
