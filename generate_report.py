import subprocess
import json
import os
import sys
from datetime import datetime

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
    <style>
        :root {{
            --color-background: #0C0A09; 
            --color-surface: #1C1917;
            --color-primary: #FBBF24;
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

        .hero-pattern {
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
        }

        .gradient-orb {
            position: fixed;
            border-radius: 50%;
            filter: blur(100px);
            z-index: -2;
            pointer-events: none;
        }
        .orb-green {
            top: -200px;
            right: -200px;
            width: 800px;
            height: 800px;
            background: rgba(74, 222, 128, 0.15); /* #4ADE80 */
            mix-blend-mode: screen;
        }
        .orb-amber {
            bottom: -200px;
            left: -200px;
            width: 600px;
            height: 600px;
            background: rgba(251, 191, 36, 0.1); /* #FBBF24 */
            mix-blend-mode: screen;
        }

        .container { max-width: 1200px; margin: 0 auto; padding: 4rem 2rem; position: relative; z-index: 1; }
    </style>
</head>
<body>
    <div class="gradient-orb orb-green"></div>
    <div class="gradient-orb orb-amber"></div>
    <div class="hero-pattern"></div>
    
    <div class="container">
        <header class="nav-header">
            <div class="brand">
                <div class="brand-logo-bg">
                   <i data-lucide="flask-conical" style="color: #FBBF24; width: 20px;"></i>
                </div>
                <div class="brand-text">mcp<span>ch.ai</span></div>
            </div>
            <div class="report-meta">
                <div>Test Report Generated</div>
                <div style="color: white; margin-top: 4px;">{timestamp}</div>
            </div>
        </header>

        <div class="stats-grid">
            <div class="card" style="display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center;">
                <div class="metric" style="color: {'#4ADE80' if pass_rate == 100 else '#FBBF24'}">{pass_rate:.1f}%</div>
                <div class="metric-label">Pass Rate</div>
                <div style="margin-top: 2rem; display: flex; gap: 2rem;">
                    <div>
                        <div style="font-size: 1.5rem; font-weight: bold; color: white;">{total_tests}</div>
                        <div style="font-size: 0.75rem; color: var(--color-text-dim); text-transform: uppercase;">Total</div>
                    </div>
                    <div>
                        <div style="font-size: 1.5rem; font-weight: bold; color: #4ADE80;">{passed_tests}</div>
                        <div style="font-size: 0.75rem; color: var(--color-text-dim); text-transform: uppercase;">Passed</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h3>Test Distribution</h3>
                <div class="chart-container">
                    <canvas id="testChart"></canvas>
                </div>
            </div>

            <div class="card">
                <h3>Code Coverage</h3>
                <div class="chart-container">
                    <canvas id="coverageChart"></canvas>
                </div>
                <div style="text-align: center; margin-top: 1rem;">
                    <div style="font-size: 2rem; font-weight: bold; color: white;">{coverage_percent:.1f}%</div>
                    <div class="metric-label">Lines Covered</div>
                </div>
            </div>
        </div>

        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
                <h3>Detailed Results</h3>
                <div style="font-family: 'JetBrains Mono'; font-size: 0.8rem; color: var(--color-text-dim);">
                    took {test_results.get('duration', 0):.2f}s
                </div> 
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Test Case</th>
                        <th>Outcome</th>
                        <th>Duration</th>
                    </tr>
                </thead>
                <tbody>
"""
    for test in test_results['tests']:
        status_class = f"status-{test['outcome']}"
        outcome_icon = "check-circle" if test['outcome'] == 'passed' else "x-circle"
        nodeid = test['nodeid']
        name = nodeid.split("::")[-1]
        html_content += f"""
                    <tr>
                        <td style="color: #E5E7EB;">
                            {name}
                            <div style="color: #6B7280; font-size: 0.75em; margin-top: 4px;">{nodeid}</div>
                        </td>
                        <td>
                            <div class="{status_class}">
                                <i data-lucide="{outcome_icon}" style="width: 16px;"></i>
                                {test['outcome'].upper()}
                            </div>
                        </td>
                        <td style="color: #9CA3AF;">{test['setup'].get('duration', 0) + test['call'].get('duration', 0) + test['teardown'].get('duration', 0):.4f}s</td>
                    </tr>"""

    html_content += f"""
                </tbody>
            </table>
        </div>
    </div>

    <script>
        lucide.createIcons();
    
        new Chart(document.getElementById('testChart'), {{
            type: 'doughnut',
            data: {{
                labels: ['Passed', 'Failed', 'Skipped'],
                datasets: [{{
                    data: [{passed_tests}, {failed_tests}, {skipped_tests}],
                    backgroundColor: ['#4ADE80', '#F87171', '#9CA3AF'],
                    borderColor: '#1C1917',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {{
                    legend: {{ position: 'right', labels: {{ color: '#D6D3D1', font: {{ family: 'IBM Plex Sans' }} }} }}
                }}
            }}
        }});

        new Chart(document.getElementById('coverageChart'), {{
            type: 'bar',
            data: {{
                labels: ['Coverage'],
                datasets: [{{
                    label: 'Percentage',
                    data: [{coverage_percent}],
                    backgroundColor: ['#FBBF24'],
                    borderRadius: 8,
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
                    x: {{ display: false, grid: {{ display: false }} }}
                }},
                plugins: {{
                    legend: {{ display: false }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""

    with open('test_report.html', 'w') as f:
        f.write(html_content)
    print("Report generated: test_report.html")

def main():
    # 1. Run pytest with --json-report
    # We install pytest-json-report locally if needed, or parse junitxml
    # Actually, let's use pytest-json-report plugin if possible, but simplest is to parse junitxml or write a custom hook.
    # EASIER: Just use pytest --report-log (needs pytest-reportlog) OR simpler:
    # Use 'pytest --junitxml=report.xml' and parse XML?
    # BETTER: there is a plugin `pytest-json-report`. Let's assume we can pip install it.
    # If not, we can parse the output.
    
    # Let's try to install pytest-json-report dynamically
    subprocess.run([sys.executable, "-m", "pip", "install", "pytest-json-report"], check=False)
    
    print("Running tests...")
    # Run pytest with coverage and json reporting
    coverage_cmd = [
        sys.executable, "-m", "pytest", 
        "--json-report", "--json-report-file=report.json",
        "--cov=src", "--cov-report=json:coverage.json",
        "tests/"
    ]
    
    result = subprocess.run(coverage_cmd, env=os.environ.copy())
    
    if result.returncode != 0 and result.returncode != 1: # 1 means some tests failed, which is fine for reporting
        print(f"Tests execution failed (exit code {result.returncode})")
        # Ensure files exist to avoid crash
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
