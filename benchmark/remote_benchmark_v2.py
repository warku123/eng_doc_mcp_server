#!/usr/bin/env python3
"""
Remote MCP Server Benchmark with Report Generation
Generates HTML report with charts and raw data logs

Usage:
    python benchmark/remote_benchmark_v2.py --url http://your-server:8001/mcp
    python benchmark/remote_benchmark_v2.py --url http://localhost:8001/mcp --report-dir ./reports
"""

import asyncio
import argparse
import json
import time
import statistics
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import httpx


@dataclass
class TestResult:
    scenario: str
    concurrency: int
    total_requests: int
    successful: int
    failed: int
    total_time_sec: float
    latencies: List[float]
    errors: List[str]
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    @property
    def rps(self) -> float:
        return self.total_requests / self.total_time_sec if self.total_time_sec > 0 else 0
    
    @property
    def error_rate(self) -> float:
        return (self.failed / self.total_requests * 100) if self.total_requests > 0 else 0
    
    @property
    def latency_stats(self) -> Dict:
        if not self.latencies:
            return {}
        sorted_lat = sorted(self.latencies)
        n = len(sorted_lat)
        return {
            "min_ms": round(min(sorted_lat), 2),
            "max_ms": round(max(sorted_lat), 2),
            "avg_ms": round(statistics.mean(sorted_lat), 2),
            "median_ms": round(statistics.median(sorted_lat), 2),
            "p50_ms": round(sorted_lat[n // 2], 2),
            "p95_ms": round(sorted_lat[int(n * 0.95)] if n > 1 else sorted_lat[0], 2),
            "p99_ms": round(sorted_lat[int(n * 0.99)] if n > 1 else sorted_lat[0], 2),
            "stdev_ms": round(statistics.stdev(sorted_lat), 2) if n > 1 else 0,
        }


class ReportGenerator:
    """Generate HTML and JSON reports from benchmark results"""
    
    @staticmethod
    def generate_html_report(results: List[TestResult], target_url: str, output_path: str):
        """Generate interactive HTML report with charts"""
        
        # Group results by scenario for multi-concurrency view
        scenario_groups: Dict[str, List[TestResult]] = {}
        for r in results:
            # Extract base scenario name (remove _c{N} suffix if exists)
            base_name = r.scenario.split('_c')[0] if '_c' in r.scenario else r.scenario
            if base_name not in scenario_groups:
                scenario_groups[base_name] = []
            scenario_groups[base_name].append(r)
        
        # Prepare data for charts - aggregate by scenario with multiple concurrency levels
        chart_labels = []
        chart_datasets = {}
        
        for scenario_name, scenario_results in scenario_groups.items():
            # Sort by concurrency
            scenario_results.sort(key=lambda x: x.concurrency)
            
            for r in scenario_results:
                label = f"{scenario_name} (c={r.concurrency})"
                chart_labels.append(label)
        
        # All results flattened for charts
        all_results = results.copy()
        
        rps_data = [r.rps for r in all_results]
        avg_latency = [r.latency_stats.get('avg_ms', 0) for r in all_results]
        p95_latency = [r.latency_stats.get('p95_ms', 0) for r in all_results]
        error_rates = [r.error_rate for r in all_results]
        labels = [f"{r.scenario}\n(c={r.concurrency})" for r in all_results]
        
        # Generate concurrency curve data for search scenarios
        concurrency_curve_data = {}
        for scenario_name, scenario_results in scenario_groups.items():
            if len(scenario_results) > 1:  # Only for scenarios with multiple concurrency levels
                scenario_results.sort(key=lambda x: x.concurrency)
                concurrency_curve_data[scenario_name] = {
                    'concurrency': [r.concurrency for r in scenario_results],
                    'rps': [r.rps for r in scenario_results],
                    'avg_latency': [r.latency_stats.get('avg_ms', 0) for r in scenario_results],
                    'p95_latency': [r.latency_stats.get('p95_ms', 0) for r in scenario_results],
                }
        
        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Server Benchmark Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5; 
            color: #333;
            line-height: 1.6;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        .header {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 30px;
        }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .header .meta {{ opacity: 0.9; font-size: 1.1em; }}
        
        .summary-cards {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{ 
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .card .label {{ color: #666; font-size: 0.9em; text-transform: uppercase; }}
        .card .value {{ 
            font-size: 2em; 
            font-weight: bold; 
            color: #667eea;
            margin-top: 5px;
        }}
        
        .chart-container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        .chart-container h2 {{ margin-bottom: 20px; color: #333; }}
        .chart-wrapper {{ position: relative; height: 350px; }}
        
        .two-col {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }}
        
        .results-table {{
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
            margin-bottom: 30px;
        }}
        .results-table h2 {{ padding: 25px 25px 0; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 0.9em; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; font-weight: 600; color: #555; }}
        tr:hover {{ background: #f8f9fa; }}
        .status-ok {{ color: #28a745; font-weight: bold; }}
        .status-warn {{ color: #ffc107; font-weight: bold; }}
        .status-error {{ color: #dc3545; font-weight: bold; }}
        
        .scenario-section {{
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            overflow: hidden;
        }}
        .scenario-header {{
            background: #f8f9fa;
            padding: 15px 25px;
            font-weight: 600;
            font-size: 1.1em;
            border-bottom: 1px solid #eee;
        }}
        .scenario-content {{
            padding: 0;
        }}
        
        .footer {{
            text-align: center;
            padding: 30px;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 MCP Server Benchmark Report</h1>
            <div class="meta">
                <p><strong>Target:</strong> {target_url}</p>
                <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Total Test Runs:</strong> {len(results)}</p>
            </div>
        </div>
        
        <div class="summary-cards">
            <div class="card">
                <div class="label">Best RPS</div>
                <div class="value">{max(rps_data):.1f}</div>
            </div>
            <div class="card">
                <div class="label">Avg Latency</div>
                <div class="value">{statistics.mean(avg_latency):.1f}ms</div>
            </div>
            <div class="card">
                <div class="label">Total Requests</div>
                <div class="value">{sum(r.total_requests for r in results)}</div>
            </div>
            <div class="card">
                <div class="label">Max Error Rate</div>
                <div class="value">{max(error_rates):.2f}%</div>
            </div>
        </div>
'''
        
        # Add concurrency curves for multi-level scenarios
        if concurrency_curve_data:
            html_content += '''
        <div class="chart-container">
            <h2>📈 RPS vs Concurrency Curve</h2>
            <div class="chart-wrapper">
                <canvas id="concurrencyCurveChart"></canvas>
            </div>
        </div>
        
        <div class="chart-container">
            <h2>⏱️ Latency vs Concurrency Curve</h2>
            <div class="chart-wrapper">
                <canvas id="latencyCurveChart"></canvas>
            </div>
        </div>
'''
        
        html_content += f'''
        <div class="two-col">
            <div class="chart-container">
                <h2>📊 RPS by Test Run</h2>
                <div class="chart-wrapper">
                    <canvas id="rpsChart"></canvas>
                </div>
            </div>
            
            <div class="chart-container">
                <h2>⏱️ Latency Distribution</h2>
                <div class="chart-wrapper">
                    <canvas id="latencyChart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="results-table">
            <h2>📋 Detailed Results</h2>
            <table>
                <thead>
                    <tr>
                        <th>Scenario</th>
                        <th>Concurrency</th>
                        <th>Requests</th>
                        <th>RPS</th>
                        <th>Avg Latency</th>
                        <th>P50</th>
                        <th>P95</th>
                        <th>P99</th>
                        <th>Error Rate</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(f'''
                    <tr>
                        <td>{r.scenario}</td>
                        <td>{r.concurrency}</td>
                        <td>{r.total_requests}</td>
                        <td>{r.rps:.2f}</td>
                        <td>{r.latency_stats.get('avg_ms', 0):.2f}ms</td>
                        <td>{r.latency_stats.get('p50_ms', 0):.2f}ms</td>
                        <td>{r.latency_stats.get('p95_ms', 0):.2f}ms</td>
                        <td>{r.latency_stats.get('p99_ms', 0):.2f}ms</td>
                        <td class="{'status-ok' if r.error_rate < 1 else 'status-warn' if r.error_rate < 5 else 'status-error'}">
                            {r.error_rate:.2f}%
                        </td>
                    </tr>
                    ''' for r in all_results)}
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p>Generated by MCP Server Benchmark Tool</p>
        </div>
    </div>
    
    <script>
'''
        
        # Add concurrency curve chart if data exists
        if concurrency_curve_data:
            curve_datasets_rps = []
            curve_datasets_latency = []
            colors = ['#667eea', '#f093fb', '#4facfe', '#43e97b', '#fa709a']
            
            for i, (scenario_name, data) in enumerate(concurrency_curve_data.items()):
                color = colors[i % len(colors)]
                curve_datasets_rps.append(f'''
                    {{
                        label: '{scenario_name}',
                        data: {data['rps']},
                        borderColor: '{color}',
                        backgroundColor: '{color}20',
                        tension: 0.4,
                        fill: false
                    }}''')
                curve_datasets_latency.append(f'''
                    {{
                        label: '{scenario_name} (Avg)',
                        data: {data['avg_latency']},
                        borderColor: '{color}',
                        backgroundColor: '{color}20',
                        tension: 0.4,
                        fill: false
                    }},
                    {{
                        label: '{scenario_name} (P95)',
                        data: {data['p95_latency']},
                        borderColor: '{color}',
                        borderDash: [5, 5],
                        backgroundColor: 'transparent',
                        tension: 0.4,
                        fill: false
                    }}''')
            
            # Get concurrency labels from first scenario
            first_data = list(concurrency_curve_data.values())[0]
            html_content += f'''
        // Concurrency Curve - RPS
        new Chart(document.getElementById('concurrencyCurveChart'), {{
            type: 'line',
            data: {{
                labels: {first_data['concurrency']},
                datasets: [{','.join(curve_datasets_rps)}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{ title: {{ display: true, text: 'Concurrency' }} }},
                    y: {{ title: {{ display: true, text: 'Requests/sec' }}, beginAtZero: true }}
                }}
            }}
        }});
        
        // Concurrency Curve - Latency
        new Chart(document.getElementById('latencyCurveChart'), {{
            type: 'line',
            data: {{
                labels: {first_data['concurrency']},
                datasets: [{','.join(curve_datasets_latency)}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{ title: {{ display: true, text: 'Concurrency' }} }},
                    y: {{ title: {{ display: true, text: 'Milliseconds' }}, beginAtZero: true }}
                }}
            }}
        }});
'''
        
        html_content += f'''
        // RPS Chart
        new Chart(document.getElementById('rpsChart'), {{
            type: 'bar',
            data: {{
                labels: {labels},
                datasets: [{{
                    label: 'RPS',
                    data: {rps_data},
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{ beginAtZero: true, title: {{ display: true, text: 'Requests/sec' }} }}
                }}
            }}
        }});
        
        // Latency Chart
        new Chart(document.getElementById('latencyChart'), {{
            type: 'bar',
            data: {{
                labels: {labels},
                datasets: [
                    {{
                        label: 'Avg Latency',
                        data: {avg_latency},
                        backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    }},
                    {{
                        label: 'P95 Latency',
                        data: {p95_latency},
                        backgroundColor: 'rgba(255, 99, 132, 0.8)',
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{ beginAtZero: true, title: {{ display: true, text: 'Milliseconds' }} }}
                }}
            }}
        }});
    </script>
</body>
</html>'''
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"\n📊 HTML Report saved: {output_path}")
    
    @staticmethod
    def generate_json_report(results: List[TestResult], target_url: str, output_path: str):
        """Generate JSON report for programmatic analysis"""
        report = {
            "metadata": {
                "target_url": target_url,
                "generated_at": datetime.now().isoformat(),
                "total_runs": len(results),
                "summary": {
                    "total_requests": sum(r.total_requests for r in results),
                    "total_success": sum(r.successful for r in results),
                    "total_failed": sum(r.failed for r in results),
                    "max_rps": max([r.rps for r in results]) if results else 0,
                    "avg_rps": statistics.mean([r.rps for r in results]) if results else 0,
                    "avg_latency_ms": statistics.mean([r.latency_stats.get('avg_ms', 0) for r in results]) if results else 0,
                }
            },
            "results": [
                {
                    "scenario": r.scenario,
                    "concurrency": r.concurrency,
                    "total_requests": r.total_requests,
                    "successful": r.successful,
                    "failed": r.failed,
                    "error_rate_percent": r.error_rate,
                    "rps": r.rps,
                    "total_time_sec": r.total_time_sec,
                    "latency_stats": r.latency_stats,
                    "timestamp": r.timestamp,
                    "errors": r.errors[:5]  # Only first 5 errors
                }
                for r in results
            ]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        print(f"💾 JSON Report saved: {output_path}")


class RemoteMCPBenchmark:
    def __init__(self, base_url: str, timeout: float = 30.0, report_dir: str = "./reports"):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[TestResult] = []
        self.session_start = datetime.now()
        
    async def _make_request(
        self, 
        client: httpx.AsyncClient, 
        method: str, 
        payload: Optional[Dict] = None
    ) -> Tuple[float, bool, str]:
        """Make single request, return (latency_ms, success, error_msg)"""
        start = time.perf_counter()
        error_msg = ""
        
        try:
            if method == "GET":
                response = await client.get(self.base_url, timeout=self.timeout)
            else:
                response = await client.post(
                    self.base_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=self.timeout
                )
            
            latency = (time.perf_counter() - start) * 1000
            success = response.status_code == 200
            
            if not success:
                error_msg = f"HTTP {response.status_code}: {response.text[:100]}"
                
            return latency, success, error_msg
            
        except httpx.TimeoutException:
            return (time.perf_counter() - start) * 1000, False, "Timeout"
        except Exception as e:
            return (time.perf_counter() - start) * 1000, False, str(e)[:100]

    async def run_load_test(
        self, 
        scenario_name: str,
        method: str,
        payload: Optional[Dict],
        concurrency: int,
        total_requests: int
    ) -> TestResult:
        """Run load test with fixed concurrency"""
        print(f"\n🚀 Testing: {scenario_name} @ concurrency={concurrency}")
        print(f"   Total requests: {total_requests}")
        
        latencies: List[float] = []
        errors: List[str] = []
        success_count = 0
        fail_count = 0
        
        semaphore = asyncio.Semaphore(concurrency)
        
        async def bounded_request(client: httpx.AsyncClient):
            async with semaphore:
                return await self._make_request(client, method, payload)
        
        limits = httpx.Limits(max_connections=concurrency * 2, max_keepalive_connections=concurrency)
        
        async with httpx.AsyncClient(limits=limits) as client:
            start_time = time.time()
            tasks = [bounded_request(client) for _ in range(total_requests)]
            
            for coro in asyncio.as_completed(tasks):
                latency, success, error = await coro
                latencies.append(latency)
                
                if success:
                    success_count += 1
                else:
                    fail_count += 1
                    if error and len(errors) < 10:
                        errors.append(error)
            
            total_time = time.time() - start_time
        
        result = TestResult(
            scenario=scenario_name,
            concurrency=concurrency,
            total_requests=total_requests,
            successful=success_count,
            failed=fail_count,
            total_time_sec=total_time,
            latencies=latencies,
            errors=errors
        )
        
        self.results.append(result)
        self._print_result(result)
        return result

    def _print_result(self, result: TestResult):
        """Print formatted result"""
        stats = result.latency_stats
        
        print(f"   ✅ Done: {result.successful}/{result.total_requests} OK, RPS={result.rps:.2f}")
        print(f"      Latency: avg={stats.get('avg_ms', 0):.1f}ms, p95={stats.get('p95_ms', 0):.1f}ms, errors={result.error_rate:.2f}%")

    def generate_reports(self):
        """Generate all reports"""
        if not self.results:
            print("No results to report")
            return
            
        timestamp = self.session_start.strftime("%Y%m%d_%H%M%S")
        
        # Generate HTML report
        html_path = self.report_dir / f"benchmark_report_{timestamp}.html"
        ReportGenerator.generate_html_report(self.results, self.base_url, str(html_path))
        
        # Generate JSON report
        json_path = self.report_dir / f"benchmark_data_{timestamp}.json"
        ReportGenerator.generate_json_report(self.results, self.base_url, str(json_path))
        
        # Print summary
        self._print_summary()
        
        print(f"\n📁 All reports saved to: {self.report_dir.absolute()}")
        print(f"   - HTML Report: {html_path.name}")
        print(f"   - JSON Data:   {json_path.name}")

    def _print_summary(self):
        """Print summary of all tests"""
        print("\n" + "=" * 80)
        print("  BENCHMARK SUMMARY")
        print("=" * 80)
        print(f"{'Scenario':<35} {'C':>5} {'RPS':>10} {'Avg(ms)':>10} {'P95(ms)':>10} {'Error%':>8}")
        print("-" * 80)
        
        for r in self.results:
            stats = r.latency_stats
            scenario_short = r.scenario[:32] + '...' if len(r.scenario) > 35 else r.scenario
            print(f"{scenario_short:<35} {r.concurrency:>5} {r.rps:>10.2f} {stats.get('avg_ms', 0):>10.1f} "
                  f"{stats.get('p95_ms', 0):>10.1f} {r.error_rate:>7.2f}%")
        
        print("=" * 80)
        
        if self.results:
            best = max(self.results, key=lambda x: x.rps)
            print(f"\n🏆 Best RPS: {best.scenario} (c={best.concurrency}) with {best.rps:.2f} req/s")


# Test scenario configurations
SCENARIOS = {
    "health_check": {
        "name": "Health Check (GET)",
        "method": "GET",
        "payload": None,
        "concurrency_levels": [10, 30, 50, 100]
    },
    "initialize": {
        "name": "MCP Initialize",
        "method": "POST",
        "payload": {
            "jsonrpc": "2.0",
            "id": "init",
            "method": "initialize"
        },
        "concurrency_levels": [10, 30, 50, 100]
    },
    "tools_list": {
        "name": "Tools List",
        "method": "POST",
        "payload": {
            "jsonrpc": "2.0",
            "id": "list",
            "method": "tools/list"
        },
        "concurrency_levels": [10, 30, 50, 100]
    },
    "search": {
        "name": "Search",
        "method": "POST",
        "payload": {
            "jsonrpc": "2.0",
            "id": "search",
            "method": "tools/call",
            "params": {
                "name": "SearchJavaTron",
                "arguments": {"query": "java-tron api node network deployment smart contract"}
            }
        },
        "concurrency_levels": [10, 30, 50, 100]
    },
    "get_now_block": {
        "name": "Get Now Block (TRON)",
        "method": "POST",
        "payload": {
            "jsonrpc": "2.0",
            "id": "block",
            "method": "tools/call",
            "params": {
                "name": "GetNowBlock",
                "arguments": {}
            }
        },
        "concurrency_levels": [10, 30, 50, 100]
    },
    "get_account": {
        "name": "Get Account (TRON)",
        "method": "POST",
        "payload": {
            "jsonrpc": "2.0",
            "id": "account",
            "method": "tools/call",
            "params": {
                "name": "GetAccount",
                "arguments": {"address": "TNP2XwQ8f2wjk7vQmh3f8jW8f2wjk7vQmh"}
            }
        },
        "concurrency_levels": [10, 30, 50, 100]
    }
}


async def main():
    parser = argparse.ArgumentParser(description="Remote MCP Server Benchmark with Reports")
    parser.add_argument("--url", default="http://localhost:8001/mcp", 
                       help="MCP server URL")
    parser.add_argument("--scenario", choices=list(SCENARIOS.keys()) + ["all"],
                       default="all", help="Test scenario")
    parser.add_argument("-n", "--requests", type=int, default=500,
                       help="Requests per concurrency level")
    parser.add_argument("--timeout", type=float, default=30.0,
                       help="Request timeout in seconds")
    parser.add_argument("--report-dir", type=str, default="./reports",
                       help="Directory to save reports")
    parser.add_argument("--safe", action="store_true",
                       help="Safe mode: lower concurrency, fewer requests, interactive prompts")
    parser.add_argument("--max-concurrency", type=int, default=None,
                       help="Override max concurrency limit")
    args = parser.parse_args()
    
    # Safe mode adjustments
    if args.safe:
        print("\n🛡️  SAFE MODE ENABLED")
        print("   - Reduced concurrency levels")
        print("   - Reduced request count")
        print("   - Interactive prompts between tests")
        if args.max_concurrency is None:
            args.max_concurrency = 50  # Cap at 50 in safe mode
    
    print(f"\n{'='*60}")
    print(f"  Remote MCP Server Benchmark")
    print(f"  Target: {args.url}")
    print(f"  Reports: {args.report_dir}")
    print(f"{'='*60}")
    
    benchmark = RemoteMCPBenchmark(args.url, timeout=args.timeout, report_dir=args.report_dir)
    
    # Run tests with multiple concurrency levels
    if args.scenario == "all":
        for key, config in SCENARIOS.items():
            levels = config["concurrency_levels"]
            # Apply max concurrency limit if specified
            if args.max_concurrency:
                levels = [c for c in levels if c <= args.max_concurrency]
            
            for concurrency in levels:
                await benchmark.run_load_test(
                    f"{config['name']}_c{concurrency}",
                    config["method"],
                    config["payload"],
                    concurrency,
                    args.requests
                )
                
                # Safe mode: interactive pause
                if args.safe:
                    print(f"\n⏸️  Test completed: {config['name']} @ {concurrency} concurrency")
                    response = input("   Continue? [Enter=yes, n=no, q=quit]: ").strip().lower()
                    if response == 'q':
                        print("   Stopping benchmark...")
                        break
                    elif response == 'n':
                        print("   Skipping to next scenario...")
                        continue
                else:
                    await asyncio.sleep(0.5)  # Brief pause between runs
    else:
        config = SCENARIOS[args.scenario]
        levels = config["concurrency_levels"]
        if args.max_concurrency:
            levels = [c for c in levels if c <= args.max_concurrency]
        
        for concurrency in levels:
            await benchmark.run_load_test(
                f"{config['name']}_c{concurrency}",
                config["method"],
                config["payload"],
                concurrency,
                args.requests
            )
            
            if args.safe:
                print(f"\n⏸️  Test completed @ {concurrency} concurrency")
                response = input("   Continue to next level? [Enter=yes, q=quit]: ").strip().lower()
                if response == 'q':
                    print("   Stopping benchmark...")
                    break
            else:
                await asyncio.sleep(0.5)
    
    # Generate reports
    benchmark.generate_reports()


if __name__ == "__main__":
    asyncio.run(main())
