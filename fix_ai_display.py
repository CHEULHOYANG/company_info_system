#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick script to fix AI button display in detail.html
"""

import re

# Read file
with open('g:/company_project_system/templates/detail.html', 'rb') as f:
    content = f.read().decode('utf-8', 'ignore')

# Find and replace the section after displayEnhancedResults call
# We need to add: resultsDiv.style.display = 'block'; if (statusDiv) statusDiv.style.display = 'none';

# Pattern: find the .then block with displayEnhancedResults
pattern = r"(displayEnhancedResults\(result\.analysisData, result\.aiResult\.analysis, resultsDiv\);)"
replacement = r"\1\n                // FIX: Ensure results are visible\n                resultsDiv.style.display = 'block';\n                if (statusDiv) statusDiv.style.display = 'none';"

content_fixed = re.sub(pattern, replacement, content)

# Also fix the error case
pattern2 = r"(resultsDiv\.innerHTML = '<div style=\"text-align:center;padding:30px;background:#fff5f5;border-radius:10px;\">' \+\s*'<p style=\"color:#dc3545;font-weight:bold;\">Error: ' \+ err\.message \+ '</p>' \+\s*'<button onclick=\"startAIAnalysis\(\)\"[^;]+;)"
replacement2 = r"\1\n                resultsDiv.style.display = 'block';"

content_fixed = re.sub(pattern2, replacement2, content_fixed)

# Also ensure statusDiv is defined at the start of startAIAnalysis
pattern3 = r"(function startAIAnalysis\(\) \{[^}]*var resultsDiv = document\.getElementById\('aiAnalysisResults'\);)"
replacement3 = r"\1\n        var statusDiv = document.querySelector('.analysis-status');"

content_fixed = re.sub(pattern3, replacement3, content_fixed, flags=re.DOTALL)

# Write back
with open('g:/company_project_system/templates/detail.html', 'wb') as f:
    f.write(content_fixed.encode('utf-8'))

print("AI button display fix applied to detail.html")
print("Changes:")
print("1. Added resultsDiv.style.display = 'block' after displayEnhancedResults")
print("2. Added statusDiv.style.display = 'none' to hide loading")
print("3. Added resultsDiv.style.display = 'block' in error handler")
