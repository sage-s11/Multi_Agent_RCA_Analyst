import sys

from langgraph.types import Command

from netops_agent.graph import build_graph

ticket_id = sys.argv[1] if len(sys.argv) > 1 else "NET-001"
graph = build_graph()
config = {"configurable": {"thread_id": ticket_id}}

result = graph.invoke({"ticket_id": ticket_id}, config)

if "__interrupt__" in result:
    p = result["__interrupt__"][0].value
    t = p["ticket"]
    print(f"\n--- TICKET {t['ticket_id']} ---")
    print(f"{t['title']}  |  device {t['hostname']}  |  {t['interface']}  |  severity {t['severity']}")
    print(f"\n--- LIVE CHECK ---\n{p['live_check']}")
    print(f"\n--- RCA (runbook: {p['runbook_used']}) ---")
    print(f"Likely cause: {p['likely_cause']}")
    print("\n--- REMOTE STEPS (NOC) ---")
    print("\n".join(f"- {s}" for s in p["remote_steps"]))
    e = p["email"]
    print(f"\n--- DRAFT EMAIL ---\nTo: {e['to']}\nSubject: {e['subject']}\n\n{e['body']}\n")

    answer = ""
    while answer not in ("approve", "reject"):
        answer = input("approve / reject: ").strip().lower()
    graph.invoke(Command(resume={"action": answer}), config)
    if answer == "approve":
        print(f"Draft saved to drafts/{t['ticket_id']}.txt")
    else:
        print("Rejected, nothing saved.")
