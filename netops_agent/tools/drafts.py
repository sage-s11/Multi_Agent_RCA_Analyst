from netops_agent.tools.text import ascii_clean


def build_email(ticket: dict, contact: dict, onsite_steps: list[str]) -> dict:
    first = contact["contact_name"].split()[0]
    steps = "\n".join(f"{i}. {ascii_clean(s)}" for i, s in enumerate(onsite_steps, 1))
    return {
        "to": contact["contact_email"],
        "subject": f"Request for on-site physical checks - {ticket['ticket_id']} ({ticket['hostname']} {ticket['interface']})",
        "body": (
            f"Hi {first},\n\n"
            f"We have an alert on {ticket['hostname']} ({ticket['interface']}): the interface is "
            f"administratively up but the line protocol is down.\n\n"
            f"Could you please arrange the following on-site checks:\n{steps}\n\n"
            f"Please reply with the results.\n\nBest regards,\nNetwork Operations"
        ),
    }