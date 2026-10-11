# Contributing to Phoenix Protocol

Thank you for your interest in contributing to Phoenix Protocol! We welcome contributions from everyone. This project is maintained and governed by **The Coastal Assassins**.

The following is a set of guidelines for contributing to Phoenix Protocol and its packages, which are hosted in the **The Coastal Assassins** Organization on GitHub. These are mostly guidelines, not rules. Use your best judgment, and feel free to propose changes to this document in a pull request.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [How to Contribute](#how-to-contribute)
   - [Reporting Issues](#reporting-issues)
   - [Pull Request Process](#pull-request-process)
4. [Development Setup](#development-setup)
5. [Compliance & Security Standard](#compliance--security-standard)

---

## Code of Conduct

All contributors and maintainers are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md). Please treat all members of the community with respect and courtesy.

---

## Getting Started

Before you begin:
- Check out the [README.md](README.md) for a project overview.
- Look at the `TODO.txt` and existing issues to find areas that need help.
- Issues labeled `good first issue` or `help wanted` are great places to start.

---

## How to Contribute

### Reporting Issues

Bugs and feature requests are tracked as GitHub issues.
- Check the issue tracker to see if the issue or feature request has already been reported.
- If not, open a new issue using the appropriate template.
- Provide descriptive details, system environment, and reproducible steps.

### Pull Request Process

1. **Fork & Branch**: Fork the repository and create your branch from `main` (e.g., `git checkout -b feature/amazing-feature`).
2. **Develop**: Write your code. Ensure it aligns with existing architecture.
3. **Test**: 
   - Ensure backend test suites pass (`pytest`).
   - Ensure frontend builds cleanly (`npm run build` in `frontend/`).
4. **Sign-off**: We require that all commits are signed off with the Developer Certificate of Origin (DCO). Use `git commit -s` to append your sign-off.
5. **Push & PR**: Push to your fork and submit a Pull Request using our PR template.
6. **Review**: All PRs must be reviewed and approved by **The Coastal Assassins** before merge. Address any feedback gracefully.

---

## Development Setup

To run Phoenix Protocol locally:

1. Ensure you have Python (3.10+) and Node.js (18+) installed.
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/phoenix-protocol.git
   cd phoenix-protocol
   ```
3. Run the unified launcher:
   ```bash
   python start.py
   ```

---

## Compliance & Security Standard

Because this is a compliance auditing tool:
- Any modifications or additions to vendor configuration parsers or compliance rule specifications must adhere to deterministic evaluation standards.
- Probabilistic models (LLMs) should only be used for mapping/interpretation, never for scoring compliance without a human-in-the-loop approval.
