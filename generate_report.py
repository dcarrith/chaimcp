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
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #1C1917; color: #F3F4F6; padding: 2rem; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; border-bottom: 1px solid #333; padding-bottom: 1rem; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; margin-bottom: 3rem; }}
        .card {{ background: #292524; padding: 1.5rem; border-radius: 12px; border: 1px solid #44403C; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }}
        .chart-container {{ position: relative; height: 250px; display: flex; justify-content: center; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
        th, td {{ text-align: left; padding: 12px; border-bottom: 1px solid #444; }}
        th {{ background: #1C1917; }}
        .status-passed {{ color: #4ADE80; font-weight: bold; }}
        .status-failed {{ color: #F87171; font-weight: bold; }}
        .metric {{ font-size: 2.5rem; font-weight: bold; margin: 0.5rem 0; }}
        .metric-label {{ color: #A8A29E; text-transform: uppercase; font-size: 0.875rem; letter-spacing: 0.05em; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1 style="color: #FBBF24; margin: 0;">ChaiMCP Test Report</h1>
                <p style="color: #A8A29E; margin-top: 0.5rem;">Generated: {timestamp}</p>
            </div>
            <div style="text-align: right;">
                <div class="metric" style="color: {'#4ADE80' if pass_rate == 100 else '#FBBF24'}">{pass_rate:.1f}%</div>
                <div class="metric-label">Pass Rate</div>
            </div>
        </div>

        <div class="stats-grid">
            <div class="card">
                <h3>Test Results</h3>
                <div class="chart-container">
                    <canvas id="testChart"></canvas>
                </div>
                <div style="display: flex; justify-content: space-around; margin-top: 1rem; text-align: center;">
                    <div><div class="metric">{total_tests}</div><div class="metric-label">Total</div></div>
                    <div><div class="metric" style="color: #4ADE80">{passed_tests}</div><div class="metric-label">Passed</div></div>
                    <div><div class="metric" style="color: #F87171">{failed_tests}</div><div class="metric-label">Failed</div></div>
                </div>
            </div>

            <div class="card">
                <h3>Code Coverage</h3>
                <div class="chart-container">
                    <canvas id="coverageChart"></canvas>
                </div>
                <div style="text-align: center; margin-top: 1rem;">
                    <div class="metric">{coverage_percent:.1f}%</div>
                    <div class="metric-label">Total Coverage</div>
                </div>
            </div>
        </div>

        <div class="card">
            <h3>Detailed Results</h3>
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
        nodeid = test['nodeid']
        name = nodeid.split("::")[-1]
        html_content += f"""
                    <tr>
                        <td style="font-family: monospace;">{name}<br><span style="color: #666; font-size: 0.8em">{nodeid}</span></td>
                        <td class="{status_class}">{test['outcome'].upper()}</td>
                        <td>{test['setup']['duration'] + test['call']['duration'] + test['teardown']['duration']:.4f}s</td>
                    </tr>"""

    html_content += """
                </tbody>
            </table>
        </div>
    </div>

    <script>
        // Test Results Chart
        new Chart(document.getElementById('testChart'), {
            type: 'doughnut',
            data: {
                labels: ['Passed', 'Failed', 'Skipped'],
                datasets: [{
                    data: [%d, %d, %d],
                    backgroundColor: ['#4ADE80', '#F87171', '#9CA3AF'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom', labels: { color: '#D6D3D1' } }
                }
            }
        });

        // Coverage Chart
        new Chart(document.getElementById('coverageChart'), {
            type: 'bar',
            data: {
                labels: ['Coverage'],
                datasets: [{
                    label: 'Percentage',
                    data: [%f],
                    backgroundColor: ['#FBBF24'],
                    borderRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { 
                        beginAtZero: true, 
                        max: 100,
                        grid: { color: '#444' },
                        ticks: { color: '#D6D3D1' }
                    },
                    x: { display: false }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    </script>
</body>
</html>
""" % (passed_tests, failed_tests, skipped_tests, coverage_percent)

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
