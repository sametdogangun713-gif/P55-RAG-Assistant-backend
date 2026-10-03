"""Parcalama (chunking): uzun metni, cumle sinirlarini koruyarak ortusen parcalara boler."""
import re
from dataclasses import dataclass
from typing import Optional

from app.core import config

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?…])\s+")


@dataclass
class Chunk:
    index: int
    content: str
    page_no: Optional[int]


def _units(text: str) -> list:
    """Metni paragraf -> cumle birimlerine ayirir; bosluklari tek bosluga indirir."""
    units = []
    for para in re.split(r"\n\s*\n", text.replace("\r\n", "\n").replace("\r", "\n")):
        para = re.sub(r"\s+", " ", para).strip()
        if not para:
            continue
        for sentence in _SENTENCE_SPLIT.split(para):
            sentence = sentence.strip()
            if sentence:
                units.append(sentence)
    return units


def _hard_split(unit: str, size: int) -> list:
    """Tek basina size'dan uzun bir cumleyi (noktalamasiz dev metin) kelime sinirindan keser."""
    parts = []
    while len(unit) > size:
        cut = unit.rfind(" ", 0, size)
        if cut <= 0:
            cut = size
        parts.append(unit[:cut].strip())
        unit = unit[cut:].strip()
    if unit:
        parts.append(unit)
    return parts


def split_text(text: str, size: int, overlap: int) -> list:
    if size < 50:
        raise ValueError("chunk_size en az 50 olmali")
    if not 0 <= overlap < size:
        raise ValueError("overlap 0 ile chunk_size arasinda olmali")
    units = []
    for u in _units(text):
        units.extend(_hard_split(u, size) if len(u) > size else [u])

    chunks, cur = [], []
    for u in units:
        if cur and len(" ".join(cur)) + 1 + len(u) > size:
            chunks.append(" ".join(cur))
            # ortusme: onceki parcanin sonundaki cumleleri yeni parcaya tasi
            carry, total = [], 0
            for s in reversed(cur):
                if total >= overlap:
                    break
                carry.insert(0, s)
                total += len(s) + 1
            if len(" ".join(carry)) + 1 + len(u) > size:
                carry = []
            cur = carry
        cur.append(u)
    if cur:
        chunks.append(" ".join(cur))
    return chunks


def chunk_pages(pages, chunk_size=None, overlap=None) -> list:
    """[(sayfa_no, metin)] -> [Chunk]. Her sayfa ayri parcalanir, boylece sayfa_no dogru kalir."""
    size = config.CHUNK_SIZE if chunk_size is None else chunk_size
    ov = config.CHUNK_OVERLAP if overlap is None else overlap
    result, idx = [], 0
    for page_no, text in pages:
        for content in split_text(text or "", size, ov):
            result.append(Chunk(index=idx, content=content, page_no=page_no))
            idx += 1
    return result
