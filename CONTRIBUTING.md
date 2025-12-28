# Contributing & Analysis Guide

Thank you for your interest in analyzing "Calcular_tiempos_fabricacion". As mentioned in the README, this project was built entirely through AI prompting by a non-technical founder. 

We are looking for expert eyes to review the codebase.

## 🎯 Focus Areas for Analysis

If you are auditing this code, please focus on:

1.  **Architecture Sanity**: Is the MVC pattern correctly implemented, or are there "god classes" hidden in the controllers?
2.  **Security**: Are there file handling vulnerabilities? SQL injection risks (despite using ORM)?
3.  **Performance**: The simulation engine (`simulation_engine.py`) uses `heapq`. Can it be optimized for hundreds of concurrent tasks?
4.  **Refactoring Opportunities**: Identify dead code or redundant logic left behind by previous AI generations.

## 🛠 Setup for Contributors

1.  **Fork & Clone** the repository.
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: Validated on Python 3.12+* sOn macOS usually requires `brew install pyqt@6`.
3.  **Run Tests**:
    ```bash
    python run_tests.py
    ```
    Ensure all ~1136 tests pass before proposing changes.

## 🐛 Reporting Issues

Please use the GitHub Issues tab. Tag issues as `Audit`, `Bug`, or `Enhancement`. 

## ⚖️ A Note on Code Style

You might find inconsistent variable naming (Spanglish) or weird docstrings. This is a artifact of the AI generation process. Stick to **PEP 8** for new contributions, but don't feel obligated to fix every existing style naming issue unless it affects functionality.

---
*Thank you for helping validate this experiment!*
