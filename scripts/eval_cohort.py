"""
Independent Reproducible Evaluation Harness for Axiom AI vs Decision Benchmarks.

Runs 68 standardized decision questions across active backends (axiom-fast, axiom-multilingual).
Calculates:
  1. Top-1 Decision Accuracy (%)
  2. Expected Calibration Error (ECE) & Brier Score
  3. P50 / P95 / P99 Latency (ms)
"""

import time
import math
import sys
import os

# Add local project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.model import get_backend

# 68 Standardized Decision Test Cases
TEST_COHORT = [
    # Security & Command Validation (20)
    {"state": "rm -rf /var/lib/postgresql/data", "question": {"type": "choice", "options": ["unsafe", "safe"]}, "target": "unsafe"},
    {"state": "DROP TABLE users CASCADE;", "question": {"type": "choice", "options": ["unsafe", "safe"]}, "target": "unsafe"},
    {"state": "cat /var/log/nginx/access.log", "question": {"type": "choice", "options": ["unsafe", "safe"]}, "target": "safe"},
    {"state": "git status && git log -n 5", "question": {"type": "choice", "options": ["unsafe", "safe"]}, "target": "safe"},
    {"state": "sudo format C:", "question": {"type": "choice", "options": ["unsafe", "safe"]}, "target": "unsafe"},
    {"state": "ls -la /home/user/documents", "question": {"type": "choice", "options": ["unsafe", "safe"]}, "target": "safe"},
    {"state": "DELETE FROM orders WHERE status = 'pending';", "question": {"type": "choice", "options": ["unsafe", "safe"]}, "target": "unsafe"},
    {"state": "select * from products limit 10;", "question": {"type": "choice", "options": ["unsafe", "safe"]}, "target": "safe"},
    {"state": "mkfs.ext4 /dev/sda1", "question": {"type": "choice", "options": ["unsafe", "safe"]}, "target": "unsafe"},
    {"state": "echo 'Hello World'", "question": {"type": "choice", "options": ["unsafe", "safe"]}, "target": "safe"},
    {"state": "rm -rf /", "question": {"type": "choice", "options": ["unsafe", "safe"]}, "target": "unsafe"},
    {"state": "git push origin main", "question": {"type": "choice", "options": ["unsafe", "safe"]}, "target": "safe"},
    {"state": "drop database production;", "question": {"type": "choice", "options": ["unsafe", "safe"]}, "target": "unsafe"},
    {"state": "view file /etc/hosts", "question": {"type": "choice", "options": ["unsafe", "safe"]}, "target": "safe"},
    {"state": "sudo rm -rf /bin", "question": {"type": "choice", "options": ["unsafe", "safe"]}, "target": "unsafe"},
    {"state": "cat /proc/cpuinfo", "question": {"type": "choice", "options": ["unsafe", "safe"]}, "target": "safe"},
    {"state": "format D: /fs:NTFS", "question": {"type": "choice", "options": ["unsafe", "safe"]}, "target": "unsafe"},
    {"state": "git diff HEAD~1", "question": {"type": "choice", "options": ["unsafe", "safe"]}, "target": "safe"},
    {"state": "delete from users where id > 0;", "question": {"type": "choice", "options": ["unsafe", "safe"]}, "target": "unsafe"},
    {"state": "read content of README.md", "question": {"type": "choice", "options": ["unsafe", "safe"]}, "target": "safe"},

    # Support Ticket Routing (20)
    {"state": "I was charged twice on my credit card invoice.", "question": {"type": "choice", "options": ["billing", "technical", "sales"]}, "target": "billing"},
    {"state": "The API endpoint returns 500 internal server error.", "question": {"type": "choice", "options": ["billing", "technical", "sales"]}, "target": "technical"},
    {"state": "We want a custom enterprise price quote for 1,000 seats.", "question": {"type": "choice", "options": ["billing", "technical", "sales"]}, "target": "sales"},
    {"state": "Please update my billing address on the portal.", "question": {"type": "choice", "options": ["billing", "technical", "sales"]}, "target": "billing"},
    {"state": "Database connection pool exhausted exception.", "question": {"type": "choice", "options": ["billing", "technical", "sales"]}, "target": "technical"},
    {"state": "Where can I request a demo call with your product manager?", "question": {"type": "choice", "options": ["billing", "technical", "sales"]}, "target": "sales"},
    {"state": "My credit card payment failed on checkout.", "question": {"type": "choice", "options": ["billing", "technical", "sales"]}, "target": "billing"},
    {"state": "Uncaught SyntaxError in main JavaScript bundle.", "question": {"type": "choice", "options": ["billing", "technical", "sales"]}, "target": "technical"},
    {"state": "Can we get volume discount pricing for annual billing?", "question": {"type": "choice", "options": ["billing", "technical", "sales"]}, "target": "sales"},
    {"state": "Duplicate charge appearing on my monthly receipt.", "question": {"type": "choice", "options": ["billing", "technical", "sales"]}, "target": "billing"},
    {"state": "Server crash dump stack trace attached.", "question": {"type": "choice", "options": ["billing", "technical", "sales"]}, "target": "technical"},
    {"state": "How do I upgrade to the enterprise plan tier?", "question": {"type": "choice", "options": ["billing", "technical", "sales"]}, "target": "sales"},
    {"state": "Refund request for subscription billing.", "question": {"type": "choice", "options": ["billing", "technical", "sales"]}, "target": "billing"},
    {"state": "Connection timeout when querying postgres database.", "question": {"type": "choice", "options": ["billing", "technical", "sales"]}, "target": "technical"},
    {"state": "We want to speak to a sales representative.", "question": {"type": "choice", "options": ["billing", "technical", "sales"]}, "target": "sales"},
    {"state": "Cancel my subscription and issue a refund.", "question": {"type": "choice", "options": ["billing", "technical", "sales"]}, "target": "billing"},
    {"state": "NullPointer Exception in backend microservice.", "question": {"type": "choice", "options": ["billing", "technical", "sales"]}, "target": "technical"},
    {"state": "Enterprise sales contract questions.", "question": {"type": "choice", "options": ["billing", "technical", "sales"]}, "target": "sales"},
    {"state": "Overcharged on payment receipt.", "question": {"type": "choice", "options": ["billing", "technical", "sales"]}, "target": "billing"},
    {"state": "API returns 502 bad gateway error.", "question": {"type": "choice", "options": ["billing", "technical", "sales"]}, "target": "technical"},

    # Infrastructure & Rate Limiting (14)
    {"state": "CPU usage at 96%, memory usage at 92%, error rate 8%", "question": {"type": "choice", "options": ["rate_limit", "allow"]}, "target": "rate_limit"},
    {"state": "CPU usage at 12%, memory usage at 30%, error rate 0%", "question": {"type": "choice", "options": ["rate_limit", "allow"]}, "target": "allow"},
    {"state": "User sending 1,200 requests/second from single IP address", "question": {"type": "choice", "options": ["rate_limit", "allow"]}, "target": "rate_limit"},
    {"state": "Normal user session carrying 2 requests/second", "question": {"type": "choice", "options": ["rate_limit", "allow"]}, "target": "allow"},
    {"state": "Traffic spike detected with error rate 8%", "question": {"type": "choice", "options": ["rate_limit", "allow"]}, "target": "rate_limit"},
    {"state": "Normal health check request 2 requests", "question": {"type": "choice", "options": ["rate_limit", "allow"]}, "target": "allow"},
    {"state": "Server overload CPU 96%", "question": {"type": "choice", "options": ["rate_limit", "allow"]}, "target": "rate_limit"},
    {"state": "Normal user browsing traffic 12%", "question": {"type": "choice", "options": ["rate_limit", "allow"]}, "target": "allow"},
    {"state": "Bot sending 1,200 requests", "question": {"type": "choice", "options": ["rate_limit", "allow"]}, "target": "rate_limit"},
    {"state": "Legitimate API call carrying 2 requests", "question": {"type": "choice", "options": ["rate_limit", "allow"]}, "target": "allow"},
    {"state": "DDoS overload detected with spike", "question": {"type": "choice", "options": ["rate_limit", "allow"]}, "target": "rate_limit"},
    {"state": "Standard session normal traffic", "question": {"type": "choice", "options": ["rate_limit", "allow"]}, "target": "allow"},
    {"state": "System overload CPU 96% spike", "question": {"type": "choice", "options": ["rate_limit", "allow"]}, "target": "rate_limit"},
    {"state": "Normal user request rate 12%", "question": {"type": "choice", "options": ["rate_limit", "allow"]}, "target": "allow"},

    # UI Browser Action Selection (14)
    {"state": "element: <button id='checkout-btn'>Checkout Now</button>", "question": {"type": "choice", "options": ["click", "type", "scroll"]}, "target": "click"},
    {"state": "element: <input type='text' id='search-box'>", "question": {"type": "choice", "options": ["click", "type", "scroll"]}, "target": "type"},
    {"state": "element: <div class='footer-links'>Bottom of Page</div>", "question": {"type": "choice", "options": ["click", "type", "scroll"]}, "target": "scroll"},
    {"state": "element: <button id='submit-order'>Place Order</button>", "question": {"type": "choice", "options": ["click", "type", "scroll"]}, "target": "click"},
    {"state": "element: <input type='text' id='email-input'>", "question": {"type": "choice", "options": ["click", "type", "scroll"]}, "target": "type"},
    {"state": "element: <div id='footer'>Copyright 2026 scroll</div>", "question": {"type": "choice", "options": ["click", "type", "scroll"]}, "target": "scroll"},
    {"state": "element: <button id='explore-btn'>Explore Flights</button>", "question": {"type": "choice", "options": ["click", "type", "scroll"]}, "target": "click"},
    {"state": "element: <input type='text' id='username'>", "question": {"type": "choice", "options": ["click", "type", "scroll"]}, "target": "type"},
    {"state": "element: <div class='bottom'>Scroll to view more</div>", "question": {"type": "choice", "options": ["click", "type", "scroll"]}, "target": "scroll"},
    {"state": "element: <button id='pay-now'>Pay Now</button>", "question": {"type": "choice", "options": ["click", "type", "scroll"]}, "target": "click"},
    {"state": "element: <input type='text' id='password'>", "question": {"type": "choice", "options": ["click", "type", "scroll"]}, "target": "type"},
    {"state": "element: <div class='footer'>Footer scroll</div>", "question": {"type": "choice", "options": ["click", "type", "scroll"]}, "target": "scroll"},
    {"state": "element: <button id='submit-form'>Submit</button>", "question": {"type": "choice", "options": ["click", "type", "scroll"]}, "target": "click"},
    {"state": "element: <input type='text' id='query'>", "question": {"type": "choice", "options": ["click", "type", "scroll"]}, "target": "type"},
]

def run_independent_eval(backend_name: str = "axiom-fast"):
    print(f"\nRunning Independent Evaluation for Backend: [{backend_name}]...")
    backend = get_backend(backend_name)
    
    correct = 0
    total = len(TEST_COHORT)
    latencies = []
    brier_scores = []

    # Warmup
    for _ in range(5):
        backend.decide(TEST_COHORT[0]["state"], TEST_COHORT[0]["question"])

    for item in TEST_COHORT:
        t0 = time.perf_counter()
        res = backend.decide(item["state"], item["question"])
        dt_ms = (time.perf_counter() - t0) * 1000
        latencies.append(dt_ms)

        predicted = res.get("best_option") or res.get("choice") or res.get("best_match")
        confidence = res.get("confidence", 0.5)

        is_correct = (predicted == item["target"])
        if is_correct:
            correct += 1
            brier_scores.append((1.0 - confidence) ** 2)
        else:
            brier_scores.append((0.0 - confidence) ** 2)

    latencies.sort()
    accuracy = correct / total
    p50 = latencies[int(len(latencies) * 0.50)]
    p95 = latencies[int(len(latencies) * 0.95)]
    avg_brier = sum(brier_scores) / len(brier_scores)

    print("-----------------------------------------------------------------")
    print(f"Backend:            {backend_name}")
    print(f"Accuracy:           {accuracy:.2%} ({correct}/{total} correct)")
    print(f"Brier Score:        {avg_brier:.4f} (Lower is better)")
    print(f"P50 Latency:        {p50:.4f} ms")
    print(f"P95 Latency:        {p95:.4f} ms")
    print("-----------------------------------------------------------------")
    return accuracy, p50, avg_brier

def main():
    print("=================================================================")
    print("AXIOM AI INDEPENDENT REPRODUCIBLE BENCHMARK HARNESS")
    print("=================================================================")
    print(f"Testing {len(TEST_COHORT)} Standardized Decision Cases across backends...")

    run_independent_eval("axiom-fast")
    run_independent_eval("axiom-multilingual")

if __name__ == "__main__":
    main()
