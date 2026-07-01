"""OpenGaia command-line interface (Typer-based)."""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import numpy as np
from pathlib import Path

app = typer.Typer(
    name="opengaia",
    help="OpenGaia — Planetary Simulator for Humanity's Foresight",
    add_completion=False,
)
console = Console()


@app.command()
def version():
    """Show version."""
    from opengaia import __version__

    console.print(f"OpenGaia v{__version__}")


@app.command()
def demo(
    name: str = typer.Argument("mvp", help="Demo name (mvp, socio, tech, safety)"),
    years: int = typer.Option(30, "--years", "-y", help="Simulation years"),
    monte_carlo: int = typer.Option(3, "--monte-carlo", "-n", help="Number of runs"),
    policy: float = typer.Option(0.6, "--policy", "-p", help="Policy strength 0-1"),
    no_plot: bool = typer.Option(False, "--no-plot", help="Skip matplotlib output"),
):
    """Run a built-in demonstration simulation."""
    if name.lower() == "mvp":
        console.print(
            Panel.fit(
                "[bold cyan]OpenGaia MVP Demo[/bold cyan]\n"
                "Minimal coupled climate + socio-economic simulation\n"
                "Toy model for illustration — real modules coming soon.",
                title="Welcome",
            )
        )
        from examples.mvp_demo import main as mvp_main

        mvp_main()
    elif name.lower() == "socio":
        _run_socio_demo(years)
    elif name.lower() == "tech":
        _run_tech_demo(years)
    elif name.lower() == "safety":
        _run_safety_demo()
    else:
        console.print("[red]Available demos: mvp, socio, tech, safety[/red]")
        raise typer.Exit(1)


@app.command()
def info():
    """Show project mission, positioning, and how to get involved."""
    console.print(
        Panel.fit(
            "[bold]OpenGaia[/bold]\n"
            "Open-source planetary-scale simulator for humanity's foresight.\n\n"
            "What it is:\n"
            "  A modular coupling framework that connects Earth system models\n"
            "  (physics/bio/climate) with socio-economic agent simulations,\n"
            "  technology & innovation dynamics, and AI safety research.\n\n"
            "What it is not:\n"
            "  A replacement for DestinE, NASA ESDT, ESA DTE, or NVIDIA Earth-2.\n"
            "  OpenGaia complements these by adding the human-system coupling\n"
            "  layer that institutional efforts do not provide.\n\n"
            "Key modules:\n"
            "  core/           — Coupling engine + WorldState\n"
            "  physics_bio/    — Climate emulator (toy → ACE/Earth2Studio)\n"
            "  socio_economic/ — Agents, economy, demographics, migration\n"
            "  tech_innovation/— R&D, tech diffusion, AI capability\n"
            "  safety_sandbox/ — AI agent insertion + alignment research\n\n"
            "Start: [cyan]opengaia demo mvp[/cyan]\n"
            "Demos: [cyan]opengaia demo socio|tech|safety[/cyan]\n"
            "Modules: [cyan]opengaia modules[/cyan]\n"
            "Contribute: See CONTRIBUTING.md and GitHub Issues.",
            title="OpenGaia",
        )
    )


@app.command()
def modules():
    """List all registered modules and their status."""
    table = Table(title="OpenGaia Modules")
    table.add_column("Module", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Description")
    table.add_row("core", "Implemented", "Coupling engine, WorldState, orchestrator")
    table.add_row("physics_bio", "Stub (toy backend)", "Climate, ecosystems, carbon, biology")
    table.add_row("socio_economic", "Implemented", "Agents, economy, demographics, migration")
    table.add_row("tech_innovation", "Implemented", "R&D, tech diffusion, AI capability")
    table.add_row("safety_sandbox", "Implemented", "AI agent insertion, alignment metrics")
    table.add_row("adapters", "Stub", "Interoperability with external digital twins")
    table.add_row("data", "Empty stub", "Ingestion pipelines, synthetic generators")
    table.add_row("eval", "Empty stub", "Validation, benchmarks, UQ")
    table.add_row("ui_viz", "Empty stub", "Dashboard, globe, NL query interface")
    console.print(table)


@app.command()
def scenarios():
    """List available example scenario configuration files."""
    config_dir = Path(__file__).resolve().parent.parent / "examples" / "configs"
    if not config_dir.exists():
        console.print("[yellow]No scenario configs found yet.[/yellow]")
        raise typer.Exit(0)

    yaml_files = sorted(config_dir.glob("*.yaml"))
    if not yaml_files:
        console.print("[yellow]No scenario configs found yet.[/yellow]")
        raise typer.Exit(0)

    table = Table(title="Available Scenario Configs")
    table.add_column("Config", style="cyan")
    table.add_column("Description")
    for yf in yaml_files:
        # Read first line for a basic name
        content = yf.read_text().split("\n")
        name_line = ""
        for line in content:
            if line.startswith("name:"):
                name_line = line.replace("name:", "").strip().strip('"').strip("'")
                break
        table.add_row(yf.name, name_line or "No description")
    console.print(table)
    console.print("\nRun with: [cyan]opengaia run-scenario --config <file>[/cyan] (coming soon)")


@app.command()
def run_scenario():
    """Run a scenario from a YAML config (placeholder — not yet implemented)."""
    console.print("[yellow]Scenario runner is not yet implemented in v0.2.[/yellow]")
    console.print("See [cyan]examples/configs/[/cyan] for example YAML configs.")
    console.print("The runner will be implemented in v0.5 as part of the coupling engine.")


def _run_socio_demo(years: int):
    console.print("[bold]Running Socio-Economic Demo...[/bold]")
    from opengaia.socio_economic.agents import Region, WorldEconomy

    economy = WorldEconomy()
    for i in range(3):
        region = Region(
            region_id=i,
            name=f"Region_{i}",
            population=np.random.uniform(50, 500),
            gdp_per_capita=np.random.uniform(5, 50),
            governance=np.random.uniform(0.3, 0.8),
        )
        region.generate_agents(n=20)
        economy.add_region(region)
    for t in range(years):
        result = economy.step(dt=1.0)
        if t % 10 == 0:
            console.print(
                f"  Year {t}: GDP={result['global_gdp']:.1f}, Emissions={result['emissions']:.1f}"
            )
    console.print(f"[green]Socio-Economic Demo Complete ({years} years)[/green]")


def _run_tech_demo(years: int):
    console.print("[bold]Running Technology & Innovation Demo...[/bold]")
    from opengaia.tech_innovation.tech_diffusion import TechDiffusionModel, Technology
    from opengaia.tech_innovation.ai_capability import AICapabilityModel
    from opengaia.tech_innovation.rd_investment import RDInvestmentModel

    tech = TechDiffusionModel()
    tech.register(Technology(name="solar", growth_rate=0.12))
    tech.register(Technology(name="ev", growth_rate=0.15))
    tech.register(Technology(name="fusion", growth_rate=0.02))
    ai = AICapabilityModel()
    rd = RDInvestmentModel()
    for t in range(years):
        rd_result = rd.step(global_gdp=100000, governance=0.5)
        tech.step(dt=1.0)
        ai.step(global_rd=rd_result["productivity_boost"], governance=0.5)
        if t % 10 == 0:
            adoption = tech.get_adoption_vector()
            console.print(
                f"  Year {t}: Solar={adoption['solar']:.2%}, EV={adoption['ev']:.2%}, "
                f"AI Cap={ai.capability_index:.2f}"
            )
    console.print(f"[green]Tech Demo Complete ({years} years)[/green]")


def _run_safety_demo():
    console.print("[bold]Running Safety Sandbox Demo...[/bold]")
    from opengaia.safety_sandbox.sandbox import SafetySandbox, AIAgent, AgentMotivation
    from opengaia.safety_sandbox.interventions import InterventionRegistry

    sandbox = SafetySandbox()
    sandbox.insert_agent(
        AIAgent(
            agent_id="cooperator",
            capability_level=0.6,
            motivation=AgentMotivation.COOPERATION,
            alignment_score=0.9,
        )
    )
    sandbox.insert_agent(
        AIAgent(
            agent_id="power_seeker",
            capability_level=0.8,
            motivation=AgentMotivation.POWER_SEEKING,
            alignment_score=0.2,
        )
    )
    sandbox.insert_agent(
        AIAgent(
            agent_id="deceiver",
            capability_level=0.7,
            motivation=AgentMotivation.DECEPTION,
            alignment_score=0.3,
            deception_capability=0.6,
        )
    )
    console.print("  Running sandbox without interventions...")
    for _ in range(5):
        results = sandbox.step({"global_gdp": 100000})
        m = results["_metrics"]
        console.print(f"    Risk: {m['risk_score']:.3f}, Agents: {m['n_agents']}")
    registry = InterventionRegistry()
    console.print("  Applying 'transparency_mandate' intervention...")
    registry.get("transparency_mandate").apply(sandbox)
    for _ in range(3):
        results = sandbox.step({"global_gdp": 100000})
        m = results["_metrics"]
        console.print(f"    After intervention - Risk: {m['risk_score']:.3f}")
    console.print("[green]Safety Sandbox Demo Complete[/green]")


if __name__ == "__main__":
    app()
