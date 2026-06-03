# services/ticket_service.py
"""0060 Multiple_Tickets_M — generate ticket number assignments."""
from models.reference import TicketNumber
from models.show_entry import CalculatedEntry
from models.class_glossary import ClassGlossary


def get_ticket_assignments() -> list:
    """
    Map each CalculatedEntry.auto_num to the next available ticket number.
    Ticket numbers in 0030T represent pre-issued ranges from the previous show.
    """
    entries = list(CalculatedEntry.select().order_by(CalculatedEntry.auto_num))
    tickets = sorted([t.ticket_number for t in TicketNumber.select() if t.ticket_number])

    class_desc_map = {
        g.class_code: g.description
        for g in ClassGlossary.select()
        if g.class_code
    }

    result = []
    for i, entry in enumerate(entries):
        ticket = tickets[i] if i < len(tickets) else entry.auto_num
        result.append({
            'auto_num':   entry.auto_num,
            'exh_no':     entry.exh_no,
            'class_code': entry.class_code,
            'class_desc': class_desc_map.get(entry.class_code or '', '') or '',
            'ticket_no':  ticket,
        })
    return result


def generate_ticket_range(start: int, count: int) -> list:
    """Generate a sequential ticket number range for a new show."""
    return list(range(start, start + count))
