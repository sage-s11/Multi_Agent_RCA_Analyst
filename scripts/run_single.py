from netops_agent.agents.single_agent import run

report = run("NET-001")
print(report.model_dump_json(indent=2))
