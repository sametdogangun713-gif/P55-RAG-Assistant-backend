"""RAG: ilgili parcalari bul -> LLM'e kaynak olarak ver -> yaniti DOGRULA -> kaynaklariyla dondur."""
import re
from dataclasses import dataclass, field
from typing import Optional

from app.core import config
from app.services import prompts, vector_search

NO_INFO_TEXT = "Yüklediğiniz belgelerde bu soruya dair yeterli bilgi bulamadım."
_CITE = re.compile(r"\[(\d{1,2})\]")
# Bazi modeller (orn. gpt-oss) alintiyi 【1】, ［1］ ya da 【1†kaynak】 diye yazar: dogrulamadan once [1]'e cevrilir
_WIDE_CITE = re.compile(r"[【［]\s*(\d{1,2})\s*(?:†[^】］]*)?[】］]")

# durumlar
ANSWERED = "answered"        # yanit kaynaklara dayaniyor ve alintilar dogrulandi
NO_CONTEXT = "no_context"    # yeterince ilgili parca yok -> LLM hic cagrilmadi
NO_INFO = "no_info"          # LLM 'bilgi yok' dedi
UNVERIFIED = "unverified"    # LLM yanit verdi ama gecerli kaynak alintisi yok -> guvenilmez


@dataclass
class RagResult:
    answer: str
    status: str
    grounded: bool
    sources: list = field(default_factory=list)
    best_score: Optional[float] = None

    def to_dict(self) -> dict:
        return {"answer": self.answer, "status": self.status, "grounded": self.grounded,
                "sources": self.sources, "best_score": self.best_score}


def verify_answer(text: str, n_sources: int):
    """LLM ciktisini dogrular. Doner: (temiz_metin, alinti_yapilan_numaralar, durum)."""
    text = _WIDE_CITE.sub(r"[\1]", (text or "").strip())
    if prompts.NO_INFO_MARKER in text:
        return NO_INFO_TEXT, [], NO_INFO
    cited = sorted({int(m) for m in _CITE.findall(text) if 1 <= int(m) <= n_sources})
    # Var olmayan kaynak numarasi (ornegin [9]) uydurulmus demektir: isareti sil
    clean = _CITE.sub(lambda m: m.group(0) if 1 <= int(m.group(1)) <= n_sources else "", text)
    clean = re.sub(r"[ \t]{2,}", " ", clean).strip()
    if not clean:
        return NO_INFO_TEXT, [], NO_INFO
    return clean, cited, (ANSWERED if cited else UNVERIFIED)


def _source_dict(n: int, hit: dict) -> dict:
    content = hit["content"]
    return {"n": n, "chunk_id": hit["chunk_id"], "document_id": hit["document_id"], "filename": hit["filename"],
            "page_no": hit["page_no"], "score": round(hit["score"], 4),
            "excerpt": content if len(content) <= 300 else content[:297] + "..."}


def answer_question(conn, user_id: int, question: str, llm, embedder=None, history=None,
                    retrieval_query=None, top_k=None, min_score=None, system_extra: str = "") -> RagResult:
    """Kullanicinin belgelerine dayali yanit uretir.

    llm: .complete(system, messages, max_tokens) metodu olan nesne (ClaudeClient, GroqClient ya da test sahtesi).
    history: onceki konusma [{'role','content'}, ...] (user ile baslayip assistant ile bitmeli).
    retrieval_query: aramada kullanilacak (yeniden yazilmis) soru; yoksa question kullanilir.
    LLMError ve EmbeddingError cagirana yukselir.
    """
    question = (question or "").strip()
    if not question:
        raise ValueError("Soru boş olamaz")
    if len(question) > config.MAX_QUESTION_CHARS:
        raise ValueError(f"Soru en fazla {config.MAX_QUESTION_CHARS} karakter olabilir")
    history = list(history or [])
    if history and history[-1]["role"] != "assistant":
        raise ValueError("Konuşma geçmişi 'assistant' mesajıyla bitmeli")

    top_k = config.RAG_TOP_K if top_k is None else top_k
    threshold = config.MIN_SCORE if min_score is None else min_score

    found = vector_search.search(conn, user_id, retrieval_query or question, top_k, embedder=embedder)
    best = found[0]["score"] if found else None
    hits = [h for h in found if h["score"] >= threshold]
    if not hits:
        # Ilgili parca yok: LLM'e hic sormayiz -> uydurma (halusinasyon) riski ve maliyet sifir
        return RagResult(NO_INFO_TEXT, NO_CONTEXT, False, [], best)

    system = prompts.SYSTEM_PROMPT + (("\n\n" + system_extra) if system_extra else "")
    messages = history + [{"role": "user", "content": prompts.build_user_message(question, hits)}]
    raw = llm.complete(system, messages)

    clean, cited, status = verify_answer(raw, len(hits))
    if status == NO_INFO:
        return RagResult(NO_INFO_TEXT, NO_INFO, False, [], best)
    if status == UNVERIFIED:
        # Yanit var ama kaynak gostermiyor: guvenilmez isaretle, aranan parcalari kullaniciya goster
        return RagResult(clean, UNVERIFIED, False, [_source_dict(i, h) for i, h in enumerate(hits, 1)], best)
    return RagResult(clean, ANSWERED, True, [_source_dict(n, hits[n - 1]) for n in cited], best)
