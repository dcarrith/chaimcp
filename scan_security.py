import subprocess # nosec
import json
import os
import sys
import datetime
from datetime import datetime as dt

def run_bandit():
    """Runs bandit security scan on Python code."""
    print("running bandit...")
    try:
        # -f json: Output JSON
        # -x: Exclude paths (venv, tests)
        result = subprocess.run(
            ['bandit', '-f', 'json', '-r', '.', '-x', './.venv,./tests,./skills', '--exit-zero', '-q'],
            capture_output=True,
            text=True
        ) # nosec
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Error running bandit: {e}")
        return {}

def run_safety():
    """Runs safety check on Python dependencies."""
    print("running safety...")
    try:
        # --json: Output JSON
        # Run with timeout to prevent hanging
        result = subprocess.run(
            ['safety', 'check', '--json'], # Note: 'check' is often the command for older versions, 'scan' for newer. Using check based on typical CI usage, or we can try 'scan' if check fails. Let's stick to what was commented out but check flags.
            # Actually, standard safety is `safety check --json`. If the user has a newer version it might be `safety scan`.
            # Let's try `safety check --json` as a primary attempt.
            capture_output=True,
            text=True,
            timeout=30 
        ) # nosec
        
        output = result.stdout
        # Safety might output text before JSON (deprecation warnings)
        json_start = output.find('{')
        if json_start != -1:
            output = output[json_start:]
        
        # Use raw_decode to handle trailing garbage (deprecation warnings etc)
        try:
            obj, _ = json.JSONDecoder().raw_decode(output)
            return obj
        except Exception:
             # Fallback to loads if raw_decode fails or just to try standard parsing
            return json.loads(output)
    except subprocess.TimeoutExpired:
        print("Error: safety scan timed out")
        return None # Return None to indicate failure/timeout
    except Exception as e:
        print(f"Error running safety: {e}")
        return None

def run_npm_audit():
    """Runs npm audit on Node.js dependencies."""
    print("running npm audit...")
    try:
        # --json: Output JSON
        result = subprocess.run(
            ['npm', 'audit', '--json'],
            capture_output=True,
            text=True
        ) # nosec
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Error running npm audit: {e}")
        return {}

def generate_html_report(bandit_results, safety_results, npm_results):
    timestamp = dt.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # --- Process Bandit Data ---
    bandit_metrics = bandit_results.get('metrics', {}).get('_totals', {})
    bandit_issues = bandit_results.get('results', [])
    bandit_high = sum(1 for i in bandit_issues if i['issue_severity'] == 'HIGH')
    bandit_medium = sum(1 for i in bandit_issues if i['issue_severity'] == 'MEDIUM')
    bandit_low = sum(1 for i in bandit_issues if i['issue_severity'] == 'LOW')

    # --- Process Safety Data ---
    # Safety returns a list of issues or a dict with "vulnerabilities" key depending on version
    # Adjust based on installed version output structure
    safety_issues = []
    safety_failed = False
    
    if safety_results is None:
        safety_failed = True
        safety_count = 0 # Don't add to score penalty directly, but handle logic below
    elif isinstance(safety_results, list):
        safety_issues = safety_results
        safety_count = len(safety_issues)
    elif isinstance(safety_results, dict):
        safety_issues = safety_results.get('vulnerabilities', [])
        safety_count = len(safety_issues)
    else:
        safety_count = 0
    
    # --- Process NPM Data ---
    npm_failed = False
    if npm_results is None:
        npm_failed = True
        npm_total = 0
    else:
        npm_advisories = npm_results.get('advisories', {})
        # Modern npm audit returns 'vulnerabilities' dict usually
        if 'vulnerabilities' in npm_results:
            # Count based on severity
            npm_vulns = npm_results['vulnerabilities']
            npm_critical = npm_vulns.get('critical', 0)
            npm_high = npm_vulns.get('high', 0)
            npm_moderate = npm_vulns.get('moderate', 0)
            npm_low = npm_vulns.get('low', 0)
            npm_total = npm_critical + npm_high + npm_moderate + npm_low
        else:
            npm_total = len(npm_advisories)
        
    # --- Aggregate Metrics ---
    total_high = bandit_high
    total_medium = bandit_medium
    total_low = bandit_low
    
    # Calculate simplistic security score
    # Start at 100
    # Current simplistic model: High/Critical deduction
    # If a scanner failed, we impose a max score penalty or cap the score
    security_score = 100 - (total_high * 10) - (total_medium * 3) - (total_low * 1) - (safety_count * 5) - (npm_total * 2) 
    
    if safety_failed or npm_failed:
        # Penalize for missing scanners to prevent "Perfect" score on failure
        # Or just cap it. Let's deduct 20 points per failed scanner to be visible.
        if safety_failed: security_score -= 20
        if npm_failed: security_score -= 20
        
    if security_score < 0: security_score = 0
    
    score_color = "#4ADE80" # Green
    if security_score < 80: score_color = "#FBBF24" # Yellow
    if security_score < 50: score_color = "#F87171" # Red

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChaiMCP Security Report</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/prism.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/components/prism-python.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/themes/prism-tomorrow.min.css" rel="stylesheet" />
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --color-primary: #D4A373;   /* Chai/Latte tint */
            --color-secondary: #CCD5AE; /* Soft Green */
            --color-bg: #0C0A09;        /* Dark Warm Black */
            --color-card: #1C1917;      /* Darker Card */
            --color-text: #E7E5E4;      /* Warm Grey */
            --color-text-dim: #A8A29E;
            --color-border: rgba(255,255,255,0.08);
            
            /* Severity Colors */
            --sev-critical: #EF4444;
            --sev-high: #F97316;
            --sev-medium: #F59E0B; 
            --sev-low: #3B82F6;
        }}
        
        body {{
            font-family: 'Outfit', sans-serif;
            background-color: var(--color-bg);
            color: var(--color-text);
            margin: 0;
            padding-bottom: 4rem;
        }}
        
        .hero-pattern {{
            background-image: 
                radial-gradient(at 100% 0%, rgba(204, 213, 174, 0.15) 0px, transparent 50%),
                radial-gradient(at 0% 100%, rgba(212, 163, 115, 0.1) 0px, transparent 50%);
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            z-index: -1;
            pointer-events: none;
        }}

        .nav-link {{
            position: relative;
            color: rgba(255,255,255,0.8);
            text-decoration: none;
            font-weight: 500;
            transition: color 0.2s;
        }}
        
        .nav-link:hover {{
            color: var(--color-primary);
        }}
        
        .btn-primary {{
            background: var(--color-primary);
            color: #1c1917;
            font-weight: 600;
            border-radius: 8px;
            padding: 8px 16px;
            text-decoration: none;
            transition: all 0.2s;
        }}
        
        .btn-primary:hover {{
            filter: brightness(1.1);
            box-shadow: 0 4px 12px rgba(212, 163, 115, 0.3);
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 1.5rem;
            margin-top: 100px;
        }}
        
        .card {{
            background: rgba(28, 25, 23, 0.6);
            backdrop-filter: blur(12px);
            border: 1px solid var(--color-border);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
            transition: transform 0.2s, border-color 0.2s;
        }}
        
        .card:hover {{
            border-color: rgba(255,255,255,0.15);
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}

        .report-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            margin-bottom: 2rem;
            border-bottom: 1px solid var(--color-border);
            padding-bottom: 1rem;
        }}
        
        .severity-badge {{
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            font-family: 'JetBrains Mono', monospace;
        }}
        
        .bg-critical {{ background: rgba(239, 68, 68, 0.2); color: #FCA5A5; border: 1px solid rgba(239, 68, 68, 0.3); }}
        .bg-high {{ background: rgba(249, 115, 22, 0.2); color: #FDBA74; border: 1px solid rgba(249, 115, 22, 0.3); }}
        .bg-medium {{ background: rgba(245, 158, 11, 0.2); color: #FCD34D; border: 1px solid rgba(245, 158, 11, 0.3); }}
        .bg-low {{ background: rgba(59, 130, 246, 0.2); color: #93C5FD; border: 1px solid rgba(59, 130, 246, 0.3); }}

        details > summary {{
            list-style: none;
            cursor: pointer;
            transition: background 0.15s;
        }}
        details > summary::-webkit-details-marker {{ display: none; }}
        details > summary:hover {{ background: rgba(255,255,255,0.03); }}
        
        .code-block {{
            margin-top: 1rem;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--color-border);
            font-size: 0.85rem;
        }}
        
        /* Chart container override */
        .chart-container {{
            position: relative; 
            height: 160px; 
            width: 100%; 
            display: flex; 
            justify-content: center;
        }}
    </style>
</head>
<body class="bg-background">
    <div class="hero-pattern"></div>
    
    <!-- Navigation -->
    <nav class="fixed top-4 left-4 right-4 max-w-[1600px] mx-auto z-50 bg-[#1C1917]/80 backdrop-blur-md rounded-xl shadow-sm border border-white/5 px-8 py-4 flex items-center justify-between">
        <a href="https://mcpch.ai/" class="flex items-center gap-3 hover:opacity-90 transition-opacity">
            <div class="w-8 h-8 rounded bg-primary/20 flex items-center justify-center">
                <img src="./assets/chai_logo.svg" alt="Chai Logo" class="w-6 h-6">
            </div>
            <span class="font-mono font-bold text-xl tracking-tight text-white">mcp<span class="text-secondary">ch.ai</span></span>
        </a>
        <div class="hidden md:flex items-center gap-8">
            <a href="https://mcpch.ai/#features" class="nav-link">Features</a>
            <a href="https://mcpch.ai/#install" class="nav-link">Install</a>
            <a href="https://mcpch.ai/docs.html" class="nav-link">Docs</a>
            <a href="https://mcpch.ai/testing.html" class="nav-link">Testing</a>
            <a href="https://mcpch.ai/security.html" class="nav-link" style="color: var(--color-primary);">Security</a>
        </div>
        <a href="https://mcpch.ai/#install" class="btn-primary">Get Started</a>
    </nav>

    <div class="container">
        <div class="report-header">
            <div>
                <h1 style="font-size: 2rem; font-weight: 700; color: white; margin: 0;">Security Scan Report</h1>
                <p style="color: var(--color-text-dim); margin-top: 0.5rem;">Automated Analysis Pipeline</p>
            </div>
            <div style="text-align: right;">
                <div style="color: var(--color-text-dim); font-size: 0.75rem; text-transform: uppercase;">Generated</div>
                <div style="color: white; font-family: 'JetBrains Mono';">{timestamp}</div>
            </div>
        </div>

        <div class="stats-grid">
            <!-- Score Card -->
            <div class="card" style="display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center;">
                <h3 style="color: var(--color-text-dim); font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 1rem;">Security Score</h3>
                <div style="font-size: 4rem; font-weight: 800; color: {score_color}; line-height: 1;">{security_score}</div>
                <div style="font-size: 0.9rem; color: var(--color-text-dim); margin-top: 0.5rem;">Pipeline Health</div>
            </div>

            <!-- Vulnerabilities Chart -->
            <div class="card">
                <h3 style="color: var(--color-text-dim); font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 1rem;">Vulnerabilities</h3>
                <div class="chart-container">
                    <canvas id="vulnChart"></canvas>
                </div>
            </div>

            <!-- Scanner Status -->
            <div class="card">
                <h3 style="color: var(--color-text-dim); font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 1rem;">Scanners Run</h3>
                <div style="display: flex; flex-direction: column; gap: 0.75rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem; background: rgba(255,255,255,0.03); border-radius: 6px;">
                        <span style="font-weight: 500;">Bandit (SAST)</span>
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <span style="font-family: 'JetBrains Mono'; font-size: 0.8rem; color: var(--color-text-dim);">{len(bandit_issues)} Issues</span>
                            <i data-lucide="check-circle" style="color: #4ADE80; width: 16px;"></i>
                        </div>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem; background: rgba(255,255,255,0.03); border-radius: 6px;">
                        <span style="font-weight: 500;">Safety (Deps)</span>
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <span style="font-family: 'JetBrains Mono'; font-size: 0.8rem; color: var(--color-text-dim);">
                                { "Failed / Timeout" if safety_failed else f"{safety_count} Issues" }
                            </span>
                            <i data-lucide="{ 'alert-triangle' if safety_failed else 'check-circle' }" style="color: { '#EF4444' if safety_failed else '#4ADE80' }; width: 16px;"></i>
                        </div>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem; background: rgba(255,255,255,0.03); border-radius: 6px;">
                        <span style="font-weight: 500;">NPM Audit</span>
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <span style="font-family: 'JetBrains Mono'; font-size: 0.8rem; color: var(--color-text-dim);">
                                { "Failed" if npm_failed else f"{npm_total} Issues" }
                            </span>
                            <i data-lucide="{ 'alert-triangle' if npm_failed else 'check-circle' }" style="color: { '#EF4444' if npm_failed else '#4ADE80' }; width: 16px;"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Bandit Findings -->
        <h2 style="font-size: 1.25rem; font-weight: 600; margin-bottom: 1rem; border-left: 4px solid var(--color-primary); padding-left: 1rem;">Code Analysis Findings</h2>
        <div style="display: flex; flex-direction: column; gap: 1rem; margin-bottom: 3rem;">
    """
    
    if not bandit_issues:
        html_content += '<div class="card" style="text-align: center; color: var(--color-text-dim);">No code vulnerabilities issues found. Great job! 🎉</div>'
    
    for issue in bandit_issues:
        sev = issue.get('issue_severity', 'LOW')
        conf = issue.get('issue_confidence', 'LOW')
        filename = issue.get('filename', '')
        line = issue.get('line_number', 0)
        code = issue.get('code', '')
        text = issue.get('issue_text', '')
        
        bg_class = f"bg-{sev.lower()}"
        
        html_content += f"""
        <div class="card" style="padding: 0; overflow: hidden;">
            <details>
                <summary style="padding: 1rem 1.5rem; display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <span class="severity-badge {bg_class}">{sev}</span>
                        <span style="font-weight: 500;">{text}</span>
                    </div>
                    <div style="color: var(--color-text-dim); font-family: 'JetBrains Mono'; font-size: 0.8rem;">
                        {filename}:{line}
                        <i data-lucide="chevron-down" style="display: inline-block; vertical-align: middle; margin-left: 8px; width: 16px;"></i>
                    </div>
                </summary>
                <div style="padding: 0 1.5rem 1.5rem 1.5rem; border-top: 1px solid var(--color-border);">
                    <p style="color: var(--color-text-dim); font-size: 0.9rem; margin-bottom: 0.5rem;">Confidence: <strong>{conf}</strong></p>
                    <div class="code-block">
                        <pre><code class="language-python">{code}</code></pre>
                    </div>
                </div>
            </details>
        </div>
        """

    html_content += """
        </div>

        <!-- Safety Findings -->
        <h2 style="font-size: 1.25rem; font-weight: 600; margin-bottom: 1rem; border-left: 4px solid var(--color-secondary); padding-left: 1rem;">Dependency Findings</h2>
        <div style="display: flex; flex-direction: column; gap: 1rem; margin-bottom: 3rem;">
    """
    
    if safety_failed:
        html_content += '<div class="card" style="text-align: center; color: var(--sev-high);">Safety scan failed or timed out. Please check connectivity.</div>'
    elif not safety_issues:
        html_content += '<div class="card" style="text-align: center; color: var(--color-text-dim);">No dependency vulnerabilities found. 🎉</div>'
        
    for issue in safety_issues:
        # Structure of issue depends on safety version, handling generic dict access
        pkg = issue[0] if isinstance(issue, list) else issue.get('package_name', 'Unknown')
        version = issue[2] if isinstance(issue, list) else issue.get('installed_version', '?')
        desc = issue[3] if isinstance(issue, list) else issue.get('vulnerability_id', 'Unknown')
        
        html_content += f"""
        <div class="card" style="padding: 1rem 1.5rem; display: flex; justify-content: space-between; align-items: center;">
            <div style="display: flex; align-items: center; gap: 1rem;">
                <i data-lucide="package" style="color: var(--color-secondary);"></i>
                <div>
                    <div style="font-weight: 600;">{pkg} <span style="font-weight: 400; color: var(--color-text-dim);">v{version}</span></div>
                    <div style="font-size: 0.8rem; color: var(--color-text-dim);">{desc}</div>
                </div>
            </div>
            <span class="severity-badge bg-medium">WARN</span>
        </div>
        """

    html_content += f"""
        </div>
        </div>
    </div>

    <!-- Footer -->
    <footer class="bg-black border-t border-white/10 py-16 px-8">
        <div class="max-w-[1600px] mx-auto flex flex-col md:flex-row justify-between items-center gap-8">
            <div class="flex items-center gap-3 opacity-60 hover:opacity-100 transition-opacity">
                <img src="./assets/chai_logo.svg" alt="Chai Logo" class="w-8 h-8 opacity-90">
                <span class="font-mono font-bold text-xl text-white">mcp<span class="text-secondary">ch.ai</span></span>
            </div>

            <div class="flex gap-12 text-base font-medium text-stone-500">
                <a href="./docs.html" class="hover:text-white transition-colors">Documentation</a>
                <a href="#" class="hover:text-white transition-colors">GitHub</a>
                <a href="#" class="hover:text-white transition-colors">License</a>
            </div>

            <div class="text-sm text-stone-600">
                &copy; 2026 ChaiMCP. Brewed for 🌱.
            </div>
        </div>
    </footer>

    <script>
        lucide.createIcons();
        Prism.highlightAll();
        
        // Vuln Chart
        new Chart(document.getElementById('vulnChart'), {{
            type: 'doughnut',
            data: {{
                labels: ['High', 'Medium', 'Low', 'Dependencies'],
                datasets: [{{
                    data: [{bandit_high}, {bandit_medium}, {bandit_low}, {safety_count + npm_total}],
                    backgroundColor: ['#F97316', '#F59E0B', '#3B82F6', '#A8A29E'],
                    borderWidth: 0,
                    cutout: '75%'
                }}]
            }},
            options: {{ 
                responsive: true, 
                maintainAspectRatio: false, 
                plugins: {{ legend: {{ position: 'right', labels: {{ color: '#A8A29E', font: {{ size: 10 }} }} }} }} 
            }}
        }});
    </script>
</body>
</html>
"""
    return html_content

def main():
    print("🛡️  Starting Security Scan Pipeline...")
    
    bandit_res = run_bandit()
    safety_res = run_safety()
    npm_res = run_npm_audit()
    
    html = generate_html_report(bandit_res, safety_res, npm_res)
    
    with open('security.html', 'w') as f:
        f.write(html)
        
    print("✅ Security report generated: security.html")

if __name__ == "__main__":
    main()
