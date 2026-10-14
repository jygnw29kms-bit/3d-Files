from __future__ import annotations
from dataclasses import dataclass
from typing import Any

SUPPORTED_TAG_TYPES = {'ntag','ntag213','ntag215','ntag216','mifare_ultralight','unknown'}

@dataclass(frozen=True)
class TagObservation:
    reader_id: str
    ams_id: str
    slot_id: str
    uid: str
    tag_type: str = 'unknown'
    payload: dict[str, Any] | None = None


def normalize_uid(value: Any) -> str:
    compact=''.join(c for c in str(value or '').upper() if c in '0123456789ABCDEF')
    if len(compact) < 8 or len(compact) % 2:
        raise ValueError('invalid NFC UID')
    if set(compact)=={'0'}:
        raise ValueError('zero NFC UID')
    return ':'.join(compact[i:i+2] for i in range(0,len(compact),2))


def validate(obs: TagObservation) -> TagObservation:
    reader=str(obs.reader_id or '').strip()
    if not reader or len(reader)>64: raise ValueError('invalid reader_id')
    try: slot=int(obs.slot_id)
    except Exception as exc: raise ValueError('invalid slot_id') from exc
    if slot not in range(4): raise ValueError('slot_id must be 0..3 for AMS 2 Pro')
    tag=str(obs.tag_type or 'unknown').lower().strip()
    if tag not in SUPPORTED_TAG_TYPES: raise ValueError('unsupported tag_type')
    uid=normalize_uid(obs.uid)
    payload=obs.payload if isinstance(obs.payload,dict) else {}
    return TagObservation(reader,str(obs.ams_id or '0'),str(slot),uid,tag,payload)
