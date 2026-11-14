from netops_agent.agents.supervisor import supervisor_node


def test_supervisor_order():
    assert supervisor_node({})["next_step"] == "ticket_agent"
    assert supervisor_node({"ticket": {"x": 1}})["next_step"] == "inventory_agent"
    s = {"ticket": {"x": 1}, "device": {"x": 1}, "contact": {"x": 1}}
    assert supervisor_node(s)["next_step"] == "diagnostics_agent"
    s["diagnostics"] = {"available": False}
    assert supervisor_node(s)["next_step"] == "triage_agent"
    s["judgement"] = {"x": 1}
    assert supervisor_node(s)["next_step"] == "draft_email"
    assert supervisor_node({"error": "boom"})["next_step"] == "error"


def test_supervisor_no_fault_when_healthy():
    s = {"ticket": {"x": 1}, "device": {"x": 1}, "contact": {"x": 1},
         "diagnostics": {"available": True, "category": "healthy"}}
    assert supervisor_node(s)["next_step"] == "no_fault"
