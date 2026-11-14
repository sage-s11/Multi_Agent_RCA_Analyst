from netops_agent.tools.text import ascii_clean

SUMMARY = {
    "physical_layer": "the interface is reported down and the link does not come up.",
    "admin_down": "the interface is administratively down.",
    "err_disabled": "the interface is in err-disabled state.",
}


def build_email(ticket: dict, contact: dict, onsite_steps: list[str],
                runbook: str = "physical_layer", observed: str | None = None) -> dict:
    first = contact["contact_name"].split()[0]
    steps = "\n".join(f"{i}. {ascii_clean(s)}" for i, s in enumerate(onsite_steps, 1))
    summary = SUMMARY.get(runbook, "the interface is not working.")
    live = f"Live check from the NOC: {observed}.\n\n" if observed else ""
    return {
        "to": contact["contact_email"],
        "subject": f"Request for on-site physical checks - {ticket['ticket_id']} ({ticket['hostname']} {ticket['interface']})",
        "body": (
            f"Hi {first},\n\n"
            f"We have an alert on {ticket['hostname']} ({ticket['interface']}): {summary}\n\n"
            f"{live}"
            f"Could you please arrange the following on-site checks:\n{steps}\n\n"
            f"Please reply with the results.\n\nBest regards,\nNetwork Operations"
        ),
    }
