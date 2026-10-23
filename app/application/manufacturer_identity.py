"""Candidates for an explicit human manufacturer identity decision."""

from app.application.ports.evidence_identity_read import EvidenceIdentityReadPort


def manufacturer_candidates(read: EvidenceIdentityReadPort, reviewed_name: str):
    exact = read.manufacturers_named(reviewed_name)
    exact_ids = {row.record_id for row in exact}
    similar = tuple(row for row in read.similar_manufacturers(reviewed_name)
                    if row.record_id not in exact_ids)
    return exact, similar
