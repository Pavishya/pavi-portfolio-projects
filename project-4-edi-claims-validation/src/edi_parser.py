"""
Generic, dependency-light X12 segment/element parser.
Shared by parsers_834.py, parsers_837.py, and parsers_835.py -- the
semantic mapping of element positions to field names lives in those
type-specific modules, not here.
"""

from typing import Dict, List


def read_edi_file(path: str) -> str:
    """Read a raw .edi text file and return its full contents as a string."""
    with open(path, 'r') as f:
        return f.read()


def split_segments(raw_text: str, segment_terminator: str = '~') -> List[str]:
    """
    Split raw EDI text into a list of segment strings (one per logical
    segment). Newlines added for file readability are stripped; the
    segment terminator is authoritative, not the newline.
    """
    flattened = raw_text.replace('\n', '').replace('\r', '')
    segments = [s.strip() for s in flattened.split(segment_terminator)]
    return [s for s in segments if s]


def parse_segment(segment: str, element_separator: str = '*') -> List[str]:
    """Split one segment string into its element list, e.g. ['CLM','CLAIM00001','350.00',...]."""
    return segment.split(element_separator)


def detect_delimiters(raw_text: str) -> Dict[str, str]:
    """
    Detect element separator and segment terminator from the ISA segment.
    ISA is a fixed-position segment: the element separator is the character
    immediately after 'ISA', and the segment terminator is the character
    immediately following the 16th element (after the sub-element separator).
    """
    flattened = raw_text.replace('\n', '').replace('\r', '')
    element_separator = flattened[3]
    # ISA has exactly 16 elements; element 16 is one character (sub-element separator),
    # immediately followed by the segment terminator.
    isa_segment_end = flattened.index('ISA') + 3 + 16 * 4 + 1
    segment_terminator = flattened[isa_segment_end] if isa_segment_end < len(flattened) else '~'
    return {'element_separator': element_separator, 'segment_terminator': segment_terminator}


def index_segments_by_id(parsed_segments: List[List[str]]) -> Dict[str, List[List[str]]]:
    """
    Group already-parsed segment-element-lists by their segment ID
    (first element). Accepts the output of parse_segment() / the
    body_segments produced by parse_envelope() -- not raw strings.
    """
    index: Dict[str, List[List[str]]] = {}
    for elements in parsed_segments:
        if not elements or not elements[0]:
            continue
        index.setdefault(elements[0], []).append(elements)
    return index


def parse_envelope(segments: List[str], element_separator: str = '*') -> Dict:
    """
    Parse a flat segment list into a structured envelope dict:
    {
        'isa': [...], 'gs': [...],
        'st_transactions': [{'st': [...], 'body_segments': [...], 'se': [...]}],
        'ge': [...], 'iea': [...],
    }
    Supports multiple ST...SE transaction blocks within a single GS group
    (used by the 837 file, which has one ST per claim).
    """
    envelope = {'isa': None, 'gs': None, 'st_transactions': [], 'ge': None, 'iea': None}
    current_transaction = None

    for segment in segments:
        elements = parse_segment(segment, element_separator)
        seg_id = elements[0] if elements else ''

        if seg_id == 'ISA':
            envelope['isa'] = elements
        elif seg_id == 'GS':
            envelope['gs'] = elements
        elif seg_id == 'ST':
            current_transaction = {'st': elements, 'body_segments': [], 'se': None}
        elif seg_id == 'SE':
            if current_transaction is not None:
                current_transaction['se'] = elements
                envelope['st_transactions'].append(current_transaction)
                current_transaction = None
        elif seg_id == 'GE':
            envelope['ge'] = elements
        elif seg_id == 'IEA':
            envelope['iea'] = elements
        else:
            if current_transaction is not None:
                current_transaction['body_segments'].append(elements)

    return envelope
