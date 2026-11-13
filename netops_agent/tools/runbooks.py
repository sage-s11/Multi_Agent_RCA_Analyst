from netops_agent.config import RUNBOOKS_DIR

def list_runbooks() -> list[str]:
    """Return available runbook names (without .md extension)."""
    return sorted(p.stem for p in RUNBOOKS_DIR.glob("*.md"))

def get_runbook(name: str) -> str:
    """Load a markdown runbook by name."""
    path = RUNBOOKS_DIR / f"{name}.md"
    if not path.exists():
        raise LookupError(f"Runbook '{name}' not found")
    return path.read_text()

def get_all_runbooks_text() -> str:
    """Load all runbooks into one string so the triage agent can read them."""
    blocks = []
    for path in sorted(RUNBOOKS_DIR.glob("*.md")):
        blocks.append(f"=== RUNBOOK: {path.stem} ===\n{path.read_text().strip()}")
    return "\n\n".join(blocks)