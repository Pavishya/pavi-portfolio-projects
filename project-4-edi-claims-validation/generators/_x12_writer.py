"""
Shared low-level X12 envelope/segment writer helpers used by the
834/837/835 generators. Newlines are appended after each '~' purely for
human readability in the saved .edi file -- the segment terminator '~'
is the authoritative delimiter, not the newline (the parser must treat
it that way too).
"""

SEGMENT_TERMINATOR = '~'
ELEMENT_SEPARATOR = '*'
SUB_ELEMENT_SEPARATOR = ':'


def seg(*elements) -> str:
    """Join elements with '*' and append '~\\n' terminator (newline for readability only)."""
    return ELEMENT_SEPARATOR.join(str(e) for e in elements) + SEGMENT_TERMINATOR + '\n'


def build_isa(sender_id: str, receiver_id: str, control_number: str,
              date_str: str, time_str: str) -> str:
    """ISA — Interchange Control Header. control_number must be a 9-digit zero-padded string."""
    return seg(
        'ISA', '00', ' ' * 10, '00', ' ' * 10,
        'ZZ', sender_id.ljust(15), 'ZZ', receiver_id.ljust(15),
        date_str, time_str, '^', '00501', control_number, '0', 'T', SUB_ELEMENT_SEPARATOR,
    )


def build_iea(group_count: int, control_number: str) -> str:
    """IEA — Interchange Control Trailer. control_number must match the matching ISA13."""
    return seg('IEA', group_count, control_number)


def build_gs(functional_id_code: str, sender_id: str, receiver_id: str,
             control_number: str, date_str: str, time_str: str, version: str) -> str:
    """GS — Functional Group Header. control_number is a small integer string (e.g. '1')."""
    return seg('GS', functional_id_code, sender_id, receiver_id, date_str, time_str, control_number, 'X', version)


def build_ge(transaction_count: int, control_number: str) -> str:
    """GE — Functional Group Trailer. control_number must match the matching GS06."""
    return seg('GE', transaction_count, control_number)


def build_st(transaction_set_code: str, control_number: str) -> str:
    """ST — Transaction Set Header. control_number is a 4-digit zero-padded string."""
    return seg('ST', transaction_set_code, control_number)


def build_se(segment_count: int, control_number: str) -> str:
    """SE — Transaction Set Trailer. segment_count = number of segments from ST to SE inclusive."""
    return seg('SE', segment_count, control_number)


def build_transaction(st_code: str, st_control_number: str, body_segments: list) -> list:
    """Wrap body_segments with ST/SE, computing the correct SE01 segment count."""
    segments = [build_st(st_code, st_control_number)]
    segments.extend(body_segments)
    se_count = len(segments) + 1  # +1 for the SE segment itself
    segments.append(build_se(se_count, st_control_number))
    return segments


def build_full_envelope(functional_id_code: str, version: str, sender_id: str, receiver_id: str,
                         transactions: list, interchange_control_number: str,
                         group_control_number: str = '1',
                         date_str: str = '240601', time_str: str = '1200') -> str:
    """
    Wrap one or more ST...SE transaction blocks in a single GS...GE group,
    itself wrapped in a single ISA...IEA interchange.

    transactions: list of (st_code, st_control_number, body_segments) tuples.
    """
    out = [build_isa(sender_id, receiver_id, interchange_control_number, date_str, time_str)]
    out.append(build_gs(functional_id_code, sender_id, receiver_id, group_control_number, date_str, time_str, version))

    for st_code, st_control_number, body_segments in transactions:
        out.extend(build_transaction(st_code, st_control_number, body_segments))

    out.append(build_ge(len(transactions), group_control_number))
    out.append(build_iea(1, interchange_control_number))
    return ''.join(out)
