# Contributing to OpenGaia

Thank you for your interest in OpenGaia — the open-source planetary simulator for humanity's foresight. This is an ambitious, high-stakes project. We welcome contributors who bring rigor, humility, and a genuine desire to build tools that help humanity navigate complexity more wisely.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md). We are committed to a welcoming, harassment-free environment for everyone.

## How to Contribute

### 1. Start Small and Focused
- Look for issues labeled `good first issue`, `help wanted`, or `documentation`.
- Read the architecture and roadmap docs before proposing large changes.
- For new features or modules, open a discussion or issue first to align on scope and design.

### 2. Development Setup
```bash
git clone https://github.com/opengaia/opengaia.git
cd opengaia
python -m venv .venv
source .venv/bin/activate
pip install -e ".[full,dev]"
pre-commit install  # highly recommended
```

Run tests and linting:
```bash
pytest
ruff check .
ruff format .
mypy opengaia
```

### 3. Pull Request Process
- Fork the repo and create a feature branch from `main`.
- Write clear commit messages and update relevant documentation.
- Include tests for new functionality (even simple ones for stubs).
- Ensure the MVP demo and existing examples still run.
- Reference any related issues.
- Be patient — reviews may take time because we prioritize correctness and alignment with the mission.

### 4. Areas Where We Especially Need Help
- **Climate / Earth System Integration**: Wrapping or extending ACE, Earth2Studio, adding carbon cycle or ecosystem components.
- **Agent-Based Socio-Economic Modeling**: Designing grounded agents, calibration pipelines, validation against historical data.
- **Coupling Engine**: Latent space techniques, multi-fidelity orchestration, WorldState schema design.
- **External Digital Twin Adapters**: Building adapters for DestinE, NASA ESDT, ESA DTE, Earth2Studio — see `adapters/README.md` and `docs/architecture.md`.
- **Safety Sandbox**: Frameworks for inserting and analyzing advanced AI agents in societal context.
- **Visualization & Interfaces**: Interactive dashboards, globe rendering, natural language query parsing, uncertainty visualization.
- **Data & Validation**: Ingestion pipelines, synthetic data generators, historical backtesting suites, uncertainty quantification.
- **Documentation & Communication**: Tutorials, scenario examples, governance docs, outreach.
- **Infrastructure**: CI/CD, compute scaling patterns, packaging.

### 5. Intellectual Honesty
This project deals with high-stakes topics (climate, AI risk, societal futures). 
- Be explicit about assumptions, limitations, and uncertainty.
- Never overclaim predictive power.
- Credit prior work generously.
- When in doubt, prioritize transparency and contestability over polish.

### 6. Governance Note
Early contributions shape the culture. We are starting lightweight but intend to evolve toward a transparent foundation-style governance. Major design decisions will be discussed publicly.

## Questions?

Open a GitHub Discussion or issue. We are happy to help onboard contributors who share the mission.

Thank you for helping build the simulator we wish we had.