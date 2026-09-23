# Contributing to Noor AI ⚡

Thank you for your interest in contributing to **Noor AI**! We welcome bug reports, feature requests, documentation improvements, and pull requests.

## How to Contribute

1. **Fork the Repository**: Create your own copy of the repo on GitHub.
2. **Clone & Set Up**:
   ```bash
   git clone https://github.com/your-username/noor-ai.git
   cd noor-ai
   pip install -e .
   ```
3. **Create a Branch**:
   ```bash
   git checkout -b feature/my-new-feature
   ```
4. **Make & Test Your Changes**:
   Run the benchmark suite to ensure no performance or accuracy regressions:
   ```bash
   python examples/bench.py examples/sample.jsonl --targets yours
   ```
5. **Submit a Pull Request**: Push your branch to GitHub and open a PR with a clear summary of your changes.

## Code Style & Standards

- Python code should follow PEP 8 and be typed using type hints (`from __future__ import annotations`).
- Preserve fast execution times (< 1ms for `noor-fast` backend).
