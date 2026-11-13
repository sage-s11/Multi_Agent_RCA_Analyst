import sys

from langgraph.types import Command

from netops_agent.graph import build_graph

ticket_id = sys.argv[1] if len(sys.argv) > 1 else "NET-001"
graph = build_graph()
config = {"configurable": {"thread_id": ticket_id}}

result = graph.invoke({"ticket_id": ticket_id}, config)

if "__interrupt__" in result:
    payload = result["__interrupt__"][0].value
    print("\n--- REMOTE STEPS (NOC) ---")
    print("\n".join(f"- {s}" for s in payload["remote_steps"]))
    e = payload["email"]
    print(f"\n--- DRAFT EMAIL ---\nTo: {e['to']}\nSubject: {e['subject']}\n\n{e['body']}\n")
    answer = input("approve / reject: ").strip().lower()
    graph.invoke(Command(resume={"action": answer}), config)
    print("Draft saved to drafts/" if answer == "approve" else "Rejected, nothing saved.")