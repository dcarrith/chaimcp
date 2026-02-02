import subprocess # nosec
import json
import os
import sys
import ast
from datetime import datetime

def get_test_info(nodeid):
    """
    Extracts docstring and source code for a test given its nodeid.
    """
    try:
        if "::" not in nodeid:
            return None, None
            
        file_path, *rest = nodeid.split("::")
        if not os.path.exists(file_path):
            return None, None
        
        with open(file_path, "r") as f:
            file_content = f.read()
            
        tree = ast.parse(file_content)
        
        # Find the test function
        target_name = rest[-1]
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == target_name:
                docstring = ast.get_docstring(node)
                
                # Extract source
                # ast in 3.10+ has lineno and end_lineno
                if hasattr(node, 'end_lineno'):
                    with open(file_path, "r") as f:
                        lines = f.readlines()
                        # 1-based indexing for AST, 0-based for list
                        # Indentation handling: dedent if needed, but simple slicing is okay for now
                        source_lines = lines[node.lineno-1 : node.end_lineno]
                        source_code = "".join(source_lines)
                else:
                    source_code = "Source extraction requires Python 3.10+"
                    
                return docstring, source_code
        return None, None
    except Exception as e:
        return None, f"Error extracting source: {e}"

def generate_html_report(test_results, coverage_results):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Calculate stats
    total_tests = test_results['summary']['total']
    passed_tests = test_results['summary']['passed']
    failed_tests = test_results['summary'].get('failed', 0) + test_results['summary'].get('error', 0)
    skipped_tests = test_results['summary'].get('skipped', 0)
    
    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    coverage_percent = coverage_results['totals']['percent_covered']
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChaiMCP Unit Test Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/themes/prism-tomorrow.min.css" rel="stylesheet" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/prism.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/components/prism-python.min.js"></script>
    <style>
        :root {{
            --color-background: #0C0A09; 
            --color-surface: #1C1917;
            --color-primary: #FBBF24;
            --color-secondary: #4ADE80;
            --color-cta: #F59E0B;
            --color-text: #F3F4F6;
            --color-text-dim: #A8A29E;
            --color-border: rgba(255, 255, 255, 0.1);
        }}
        
        body {{ 
            font-family: 'IBM Plex Sans', sans-serif; 
            background-color: #0C0A09; 
            color: var(--color-text); 
            margin: 0;
            padding: 0;
            min-height: 100vh;
        }}

        .hero-pattern {{
            position: fixed;
            top: 0; 
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            background-color: #0C0A09;
            background-image: radial-gradient(#44403C 0.5px, transparent 0.5px), radial-gradient(#44403C 0.5px, #0C0A09 0.5px);
            background-size: 20px 20px;
            background-position: 0 0, 10px 10px;
            opacity: 0.2;
        }}

        .gradient-orb {{
            position: fixed;
            border-radius: 50%;
            filter: blur(100px);
            z-index: -2;
            pointer-events: none;
        }}
        .orb-green {{
            top: -200px;
            right: -200px;
            width: 800px;
            height: 800px;
            background: rgba(74, 222, 128, 0.15); /* #4ADE80 */
            mix-blend-mode: screen;
        }}
        .orb-amber {{
            bottom: -200px;
            left: -200px;
            width: 600px;
            height: 600px;
            background: rgba(251, 191, 36, 0.1); /* #FBBF24 */
            mix-blend-mode: screen;
        }}

        /* Container with extra top padding for fixed header */
        .container {{ max-width: 1400px; margin: 0 auto; padding: 8rem 2rem 4rem 2rem; position: relative; z-index: 1; }}
        
        /* Fixed Navigation Header */
        .fixed-nav {{
            position: fixed;
            top: 1rem;
            left: 1rem;
            right: 1rem;
            max-width: 1600px;
            margin: 0 auto;
            z-index: 50;
            background-color: rgba(28, 25, 23, 0.8);
            backdrop-filter: blur(12px);
            border-radius: 0.75rem;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.05);
            padding: 1rem 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .brand {{
            display: flex;
            align-items: center;
            gap: 12px;
            text-decoration: none;
        }}
        
        .brand-logo-bg {{
            width: 32px; height: 32px;
            background: rgba(251, 191, 36, 0.2);
            border-radius: 4px;
            display: flex; align-items: center; justify-content: center;
        }}
        
        .brand-text {{
            font-family: 'JetBrains Mono', monospace;
            font-weight: 700;
            font-size: 1.25rem;
            letter-spacing: -0.025em;
            color: white;
        }}
        
        .brand-text span {{ color: var(--color-primary); }}
        
        .nav-links {{
            display: flex;
            gap: 2rem;
            align-items: center;
        }}
        
        .nav-link {{
            color: rgba(255,255,255,0.8);
            text-decoration: none;
            font-weight: 500;
            transition: color 0.15s;
        }}
        .nav-link:hover {{ color: var(--color-primary); }}
        
        .btn-primary {{
            background-color: var(--color-cta);
            color: black;
            font-weight: 600;
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            text-decoration: none;
            transition: all 0.2s;
            font-size: 0.875rem;
            display: inline-block;
        }}
        .btn-primary:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            opacity: 0.9;
        }}
        
        .report-meta {{ text-align: right; color: var(--color-text-dim); font-size: 0.875rem; margin-top: 1rem; margin-bottom: 2rem; display: flex; justify-content: space-between; align-items: center; }}

        /* 3-Column Grid Layout */
        .stats-grid {{ 
            display: grid; 
            grid-template-columns: repeat(3, 1fr); 
            gap: 2rem; 
            margin-bottom: 3rem; 
        }}
        
        @media (max-width: 1024px) {{
            .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .stats-grid > div:last-child {{ grid-column: span 2; }}
            .nav-links-desktop {{ display: none; }}
        }}
        @media (max-width: 768px) {{
            .stats-grid {{ grid-template-columns: 1fr; }}
            .stats-grid > div:last-child {{ grid-column: span 1; }}
        }}
        
        .card {{ 
            background: rgba(28, 25, 23, 0.6);
            backdrop-filter: blur(12px);
            padding: 2rem; 
            border-radius: 16px; 
            border: 1px solid var(--color-border);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            transition: all 0.3s ease;
        }}
        .card:hover {{
            background: rgba(28, 25, 23, 0.8);
            border-color: rgba(255, 255, 255, 0.2);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }}
        
        h3 {{ margin-top: 0; font-size: 1.25rem; color: white; margin-bottom: 1.5rem; font-weight: 600; letter-spacing: -0.01em; }}

        .chart-container {{ position: relative; height: 200px; display: flex; justify-content: center; }}
        
        /* Table Styles */
        .test-table {{ width: 100%; border-collapse: separate; border-spacing: 0; margin-top: 0; }}
        .test-table th {{ 
            text-align: left; 
            padding: 1rem 1.5rem; 
            border-bottom: 1px solid var(--color-border); 
            color: var(--color-text-dim); 
            font-weight: 500; 
            font-size: 0.75rem; 
            text-transform: uppercase; 
            letter-spacing: 0.05em; 
        }}
        .test-table td {{ 
            padding: 1.25rem 1.5rem; 
            border-bottom: 1px solid rgba(255,255,255,0.05); 
            vertical-align: top;
        }}
        .test-table tr:hover td {{
            background: rgba(255,255,255,0.02);
        }}
        
        /* Expandable Rows */
        details > summary {{
            list-style: none;
            cursor: pointer;
            outline: none;
        }}
        details > summary::-webkit-details-marker {{ display: none; }}
        
        .test-details {{
            margin-top: 1rem;
            padding: 1rem;
            background: rgba(0,0,0,0.3);
            border-radius: 8px;
            border: 1px solid var(--color-border);
        }}
        
        .timeline-bar {{
            display: flex;
            height: 8px;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 8px;
            background: #333;
        }}
        .segment {{ height: 100%; }}
        
        .code-block {{
            margin-top: 1rem;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--color-border);
            font-size: 0.85rem;
        }}
        
        .status-passed {{ color: #4ADE80; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; }}
        .status-failed {{ color: #F87171; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; }}
        
        .metric {{ font-size: 3rem; font-weight: 700; margin: 0.5rem 0; color: white; line-height: 1; }}
        .metric-label {{ color: var(--color-text-dim); text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.05em; font-weight: 600; margin-top: 0.5rem; }}
    </style>
</head>
<body>
    <div class="gradient-orb orb-green"></div>
    <div class="gradient-orb orb-amber"></div>
    <div class="hero-pattern"></div>
    
    <!-- Fixed Navigation -->
    <nav class="fixed-nav">
        <div style="display: flex; items-center; gap: 1rem;">
            <a href="https://mcpch.ai/" class="brand">
                <div class="brand-logo-bg">
                   <i data-lucide="flask-conical" style="color: #FBBF24; width: 20px;"></i>
                </div>
                <div class="brand-text">mcp<span>ch.ai</span></div>
            </a>
        </div>
        
        <div class="nav-links nav-links-desktop">
            <a href="https://mcpch.ai/#features" class="nav-link">Features</a>
            <a href="https://mcpch.ai/#install" class="nav-link">Install</a>
            <a href="https://mcpch.ai/docs.html" class="nav-link">Docs</a>
            <a href="https://mcpch.ai/testing.html" class="nav-link">Testing</a>
            <a href="https://mcpch.ai/security.html" class="nav-link">Security</a>
        </div>
        
        <a href="https://mcpch.ai/#install" class="btn-primary">Get Started</a>
    </nav>
    
    <div class="container">
        <div class="report-meta">
            <h1 style="font-size: 1.5rem; font-weight: 600; color: white; margin: 0;">Unit Test Report</h1>
            <div style="display: flex; flex-direction: column; align-items: flex-end;">
                <div style="color: var(--color-text-dim); font-size: 0.75rem; text-transform: uppercase;">Generated</div>
                <div style="color: white; margin-top: 2px;">{timestamp}</div>
            </div>
        </div>

        <div class="stats-grid">
            <!-- Col 1: Pass Rate -->
            <div class="card" style="display: flex; flex-direction: column; align-items: center; justify-content: center;">
                <h3>Pass Rate</h3>
                <div style="position: relative; width: 160px; height: 160px;">
                    <canvas id="passChart"></canvas>
                    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center;">
                         <div style="font-size: 2rem; font-weight: bold; color: {'#4ADE80' if pass_rate == 100 else '#FBBF24'}">{pass_rate:.0f}%</div>
                    </div>
                </div>
            </div>

            <!-- Col 2: Distribution -->
            <div class="card">
                <h3>Results Distribution</h3>
                <div class="chart-container">
                     <canvas id="barChart"></canvas>
                </div>
                <div style="display: flex; justify-content: center; gap: 2rem; margin-top: 1rem;">
                    <div style="text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: bold; color: white;">{total_tests}</div>
                        <div class="metric-label">Total</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: bold; color: #4ADE80;">{passed_tests}</div>
                        <div class="metric-label">Passed</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 1.5rem; font-weight: bold; color: #F87171;">{failed_tests}</div>
                        <div class="metric-label">Failed</div>
                    </div>
                </div>
            </div>

            <!-- Col 3: Code Coverage -->
            <div class="card">
                <h3>Code Coverage</h3>
                <div class="chart-container">
                    <canvas id="coverageChart"></canvas>
                </div>
                <div style="text-align: center; margin-top: 1rem;">
                    <div class="metric">{coverage_percent:.1f}%</div>
                    <div class="metric-label">Lines Covered</div>
                </div>
            </div>
        </div>

        <div class="card" style="padding: 0; overflow: hidden;">
            <div style="padding: 2rem; border-bottom: 1px solid var(--color-border); display: flex; justify-content: space-between; align-items: center;">
                <h3 style="margin: 0;">Detailed Results</h3>
                <div style="font-family: 'JetBrains Mono'; font-size: 0.8rem; color: var(--color-text-dim);">
                    Total Duration: {test_results.get('duration', 0):.2f}s
                </div> 
            </div>
            <table class="test-table">
                <thead>
                    <tr>
                        <th style="width: 60%;">Test Case</th>
                        <th style="width: 20%;">Outcome</th>
                        <th style="width: 20%;">Duration</th>
                    </tr>
                </thead>
                <tbody>
"""
    for test in test_results['tests']:
        status_class = f"status-{test['outcome']}"
        outcome_icon = "check-circle" if test['outcome'] == 'passed' else "x-circle"
        nodeid = test['nodeid']
        name = nodeid.split("::")[-1]
        
        # Extract durations
        d_setup = test['setup'].get('duration', 0)
        d_call = test['call'].get('duration', 0)
        d_teardown = test['teardown'].get('duration', 0)
        d_total = d_setup + d_call + d_teardown
        
        # Calculate percentages for bar
        p_setup = (d_setup / d_total * 100) if d_total > 0 else 0
        p_call = (d_call / d_total * 100) if d_total > 0 else 0
        p_teardown = (d_teardown / d_total * 100) if d_total > 0 else 0
        
        # Get source and docstring
        doc, source = get_test_info(nodeid)
        # Escape source code for HTML
        safe_source = source.replace("<", "&lt;").replace(">", "&gt;") if source else ""
        doc_html = f'<div style="margin-bottom: 1rem; color: #D6D3D1; font-style: italic;">{doc}</div>' if doc else ''
        
        html_content += f"""
                    <tr>
                        <td colspan="3" style="padding: 0;">
                            <details style="width: 100%;">
                                <summary style="padding: 1.25rem 1.5rem; display: flex; align-items: flex-start; justify-content: space-between;">
                                    <div style="flex: 1;">
                                        <div style="font-family: 'JetBrains Mono', monospace; font-weight: 600; font-size: 0.95rem; color: #E5E7EB; display: flex; align-items: center; gap: 8px;">
                                            <i data-lucide="chevron-right" style="width: 16px; height: 16px; color: var(--color-text-dim);"></i>
                                            {name}
                                        </div>
                                        <div style="color: #6B7280; font-size: 0.75em; margin-top: 4px; padding-left: 24px;">{nodeid}</div>
                                    </div>
                                    
                                    <div style="flex: 0 0 15%;" class="{status_class}">
                                        <i data-lucide="{outcome_icon}" style="width: 16px;"></i>
                                        {test['outcome'].upper()}
                                    </div>
                                    
                                    <div style="flex: 0 0 15%; color: #9CA3AF; text-align: right; font-family: 'JetBrains Mono';">
                                        {d_total:.4f}s
                                    </div>
                                </summary>
                                
                                <div style="padding: 0 1.5rem 1.5rem 3rem;">
                                    <div class="test-details">
                                        {doc_html}
                                        
                                        <div style="font-size: 0.75rem; text-transform: uppercase; color: var(--color-text-dim); font-weight: 600; display: flex; justify-content: space-between;">
                                            <span>Execution Timeline</span>
                                            <span>Total: {d_total:.4f}s</span>
                                        </div>
                                        <div class="timeline-bar">
                                            <div class="segment" style="width: {p_setup}%; background: #60A5FA;" title="Setup: {d_setup:.4f}s"></div>
                                            <div class="segment" style="width: {p_call}%; background: #4ADE80;" title="Call: {d_call:.4f}s"></div>
                                            <div class="segment" style="width: {p_teardown}%; background: #F472B6;" title="Teardown: {d_teardown:.4f}s"></div>
                                        </div>
                                        <div style="display: flex; gap: 1rem; margin-top: 0.5rem; font-size: 0.75rem; color: var(--color-text-dim);">
                                            <div style="display: flex; align-items: center; gap: 4px;"><div style="width: 8px; height: 8px; background: #60A5FA; border-radius: 50%;"></div> Setup</div>
                                            <div style="display: flex; align-items: center; gap: 4px;"><div style="width: 8px; height: 8px; background: #4ADE80; border-radius: 50%;"></div> Call</div>
                                            <div style="display: flex; align-items: center; gap: 4px;"><div style="width: 8px; height: 8px; background: #F472B6; border-radius: 50%;"></div> Teardown</div>
                                        </div>

                                        <div class="code-block">
                                            <pre><code class="language-python">{safe_source}</code></pre>
                                        </div>
                                    </div>
                                </div>
                            </details>
                        </td>
                    </tr>"""

    html_content += f"""
                </tbody>
            </table>
        </div>
    </div>

    <script>
        lucide.createIcons();
        
        // Pass Rate Donut
        new Chart(document.getElementById('passChart'), {{
            type: 'doughnut',
            data: {{
                labels: ['Passed', 'Failed/Skipped'],
                datasets: [{{
                    data: [{passed_tests}, {total_tests - passed_tests}],
                    backgroundColor: ['#4ADE80', 'rgba(255,255,255,0.05)'],
                    borderWidth: 0,
                    cutout: '85%'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }}, tooltip: {{ enabled: false }} }}
            }}
        }});
    
        // Distribution Bar
        new Chart(document.getElementById('barChart'), {{
            type: 'bar',
            data: {{
                labels: ['Passed', 'Failed', 'Skipped'],
                datasets: [{{
                    data: [{passed_tests}, {failed_tests}, {skipped_tests}],
                    backgroundColor: ['#4ADE80', '#F87171', '#9CA3AF'],
                    borderRadius: 4,
                    barThickness: 20
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{ display: false }},
                    x: {{ grid: {{ display: false }}, ticks: {{ color: '#A8A29E' }} }}
                }},
                plugins: {{ legend: {{ display: false }} }}
            }}
        }});

        // Coverage Bar
        new Chart(document.getElementById('coverageChart'), {{
            type: 'bar',
            data: {{
                labels: ['Coverage'],
                datasets: [{{
                    label: 'Percentage',
                    data: [{coverage_percent}],
                    backgroundColor: ['#FBBF24'],
                    borderRadius: 4,
                    barThickness: 40
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{ 
                        beginAtZero: true, 
                        max: 100,
                        grid: {{ color: 'rgba(255,255,255,0.05)' }},
                        ticks: {{ color: '#A8A29E', font: {{ family: 'JetBrains Mono' }} }},
                        border: {{ display: false }}
                    }},
                    x: {{ display: false }}
                }},
                plugins: {{ legend: {{ display: false }} }}
            }}
        }});
    </script>
</body>
</html>
"""

    with open("testing.html", "w") as f:
        f.write(html_content)
    
    print(f"Report generated: testing.html")

def main():
    # 1. Run pytest with --json-report
    subprocess.run([sys.executable, "-m", "pip", "install", "pytest-json-report"], check=False) # nosec
    
    print("Running tests...")
    coverage_cmd = [
        sys.executable, "-m", "pytest", 
        "--json-report", "--json-report-file=report.json",
        "--cov=src", "--cov=scan_security.py", "--cov=local_bridge.py", "--cov-report=json:coverage.json",
        "tests/"
    ]
    
    result = subprocess.run(coverage_cmd, env=os.environ.copy()) # nosec
    
    if result.returncode != 0 and result.returncode != 1:
        print(f"Tests execution failed (exit code {result.returncode})")
        if not os.path.exists("report.json"):
             print("Critical: report.json not generated.")
             return

    # 2. Parse Results
    try:
        with open('report.json', 'r') as f:
            test_results = json.load(f)
        
        with open('coverage.json', 'r') as f:
            coverage_results = json.load(f)
            
        # 3. Generate HTML
        generate_html_report(test_results, coverage_results)
        
    except Exception as e:
        print(f"Error generating report: {e}")

if __name__ == "__main__":
    main()
