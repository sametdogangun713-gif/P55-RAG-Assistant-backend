"""Sohbet: kalici konusma gecmisi, baglam penceresi, uzun gecmisi ozetleme, takip sorusunu yeniden yazma."""
import re
import time

from app.core import config
from app.db import conversations as repo
from app.services import prompts, rag
from app.services.llm_client import LLMError

_CITE = re.compile(r"\s*\[\d{1,2}\]")

SUMMARY_SYSTEM = (
    "Sen bir sohbet özetleyicisisin. Verilen önceki özeti ve yeni konuşma bölümünü birleştirip, kullanıcının sorduğu "
    "konuları ve verilen yanıtların ana noktalarını içeren en fazla 8 cümlelik Türkçe bir özet yaz. "
    "Metinde olmayan bilgi ekleme. Yalnızca özeti yaz."
)
REWRITE_SYSTEM = (
    "Kullanıcının SON SORU'sunu, konuşmayı görmeyen biri de anlayabilsin diye tek başına anlaşılır hale getir. "
    "'o', 'bu', 'peki ya' gibi zamir ve belirsiz ifadeleri konuşmadaki gerçek konuyla değiştir. "
    "Soru zaten bağımsızsa aynen yaz. Yalnızca yeniden yazılmış tek bir soru yaz, başka hiçbir şey ekleme."
)


class ConversationNotFoundError(Exception):
    pass


def strip_citations(text: str) -> str:
    """[1], [2] gibi isaretleri siler: eski cevaplarin kaynak numaralari yeni istemdeki numaralarla karismasin."""
    return _CITE.sub("", text).strip()


def _clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit - 3] + "..."


def get_owned_conversation(conn, user: dict, conv_id: int) -> dict:
    """Sohbetler OZELDIR: yonetici dahil sahibinden baska kimse goremez. Yoksa/baskasinin ise ayni hata."""
    conv = repo.get_conversation(conn, conv_id)
    if conv is None or conv["user_id"] != user["id"]:
        raise ConversationNotFoundError("Sohbet bulunamadı")
    return conv


def create_conversation(conn, user: dict, title=None) -> dict:
    title = (title or "").strip()[:80] or repo.DEFAULT_TITLE
    return repo.create_conversation(conn, user["id"], title)


def list_conversations(conn, user: dict) -> list:
    return repo.list_conversations(conn, user["id"])


def delete_conversation(conn, user: dict, conv_id: int) -> None:
    get_owned_conversation(conn, user, conv_id)
    repo.delete_conversation(conn, conv_id)


MAX_TITLE_CHARS = 80


def rename_conversation(conn, user: dict, conv_id: int, title: str) -> dict:
    """Kullanici sohbetine kendi adini verir (varsayilan ad ilk sorudan uretilir)."""
    get_owned_conversation(conn, user, conv_id)
    title = " ".join((title or "").split())          # bas/son ve fazla bosluklar
    if not title:
        raise ValueError("Sohbet adı boş olamaz")
    repo.rename_conversation(conn, conv_id, title[:MAX_TITLE_CHARS])
    return repo.get_conversation(conn, conv_id)


def list_messages(conn, user: dict, conv_id: int) -> list:
    get_owned_conversation(conn, user, conv_id)
    out = []
    for m in repo.list_messages(conn, conv_id):
        item = {k: m[k] for k in ("id", "role", "content", "created_at", "status", "grounded", "latency_ms")}
        item["grounded"] = None if m["grounded"] is None else bool(m["grounded"])
        item["sources"] = []
        if m["role"] == "assistant":
            for s in repo.get_message_sources(conn, m["id"]):
                s["excerpt"] = _clip(s.pop("content"), 300)
                item["sources"].append(s)
        out.append(item)
    return out


def normalize_history(messages) -> list:
    """API kurali: roller dönüşümlü, 'user' ile baslar, 'assistant' ile biter."""
    merged = []
    for m in messages:
        if merged and merged[-1]["role"] == m["role"]:
            merged[-1]["content"] += "\n" + m["content"]
        else:
            merged.append({"role": m["role"], "content": m["content"]})
    while merged and merged[0]["role"] != "user":
        merged.pop(0)
    while merged and merged[-1]["role"] != "assistant":
        merged.pop()
    return merged


def _for_llm(m: dict) -> dict:
    content = strip_citations(m["content"]) if m["role"] == "assistant" else m["content"]
    return {"role": m["role"], "content": _clip(content, config.HISTORY_MSG_MAX_CHARS)}


def summarize(llm, previous_summary, messages) -> str:
    transcript = "\n".join(
        f"{'Kullanıcı' if m['role'] == 'user' else 'Asistan'}: {_for_llm(m)['content']}" for m in messages)
    prompt = f"ÖNCEKİ ÖZET:\n{previous_summary or '(yok)'}\n\nYENİ BÖLÜM:\n{transcript}"
    out = llm.complete(SUMMARY_SYSTEM, [{"role": "user", "content": prompt}], max_tokens=400)
    return _clip(out.strip(), config.SUMMARY_MAX_CHARS)


def build_context(conn, conv: dict, prior: list, llm):
    """LLM'e gidecek (gecmis_mesajlar, sistem_ek_metni) ciftini hazirlar.

    - Ozetlenmemis mesajlar toplami CHAT_HISTORY_CHARS'i asarsa, eski kisim ozetlenir; son
      CHAT_KEEP_RECENT mesaj birebir kalir.
    - Ozetleme basarisiz olursa soru yine de yanitlanir (eski ozetle devam, eski mesajlar bu tur dusurulur).
    """
    unsummarized = [m for m in prior if m["id"] > conv["summary_upto"]]
    summary = conv.get("summary")
    total = sum(len(m["content"]) for m in unsummarized)
    if total > config.CHAT_HISTORY_CHARS and len(unsummarized) > config.CHAT_KEEP_RECENT:
        older, recent = unsummarized[:-config.CHAT_KEEP_RECENT], unsummarized[-config.CHAT_KEEP_RECENT:]
        try:
            summary = summarize(llm, summary, older)
            repo.set_summary(conn, conv["id"], summary, older[-1]["id"])
        except LLMError:
            pass
    else:
        recent = unsummarized
    history = normalize_history([_for_llm(m) for m in recent])
    extra = ("Önceki konuşmanın özeti (yalnızca konuşmayı anlamak içindir; bilgi KAYNAĞI değildir, "
             "yanıtı yine yalnızca <kaynaklar>'a dayandır):\n" + summary) if summary else ""
    return history, extra


def rewrite_question(llm, history: list, question: str) -> str:
    """Takip sorusunu ('peki ya ikincisi?') arama icin tek basina anlasilir hale getirir. Hata olursa aynen doner."""
    if not history:
        return question
    transcript = "\n".join(
        f"{'Kullanıcı' if m['role'] == 'user' else 'Asistan'}: {m['content']}" for m in history[-4:])
    try:
        out = llm.complete(REWRITE_SYSTEM, [{"role": "user", "content": f"KONUŞMA:\n{transcript}\n\nSON SORU: {question}"}],
                           max_tokens=150)
    except LLMError:
        return question
    out = " ".join(out.split())
    return out if out and len(out) <= 500 else question


GENERAL = "general"     # belgelerde yanit yok -> modelin genel bilgisiyle (kaynaksiz, etiketli) yanit


def general_answer(llm, history: list, text: str, system_extra: str = ""):
    """Belgelerde yanit bulunamayinca selamlasma/genel soru icin kisa yanit. Hata olursa None (RAG sonucu kalir)."""
    system = prompts.GENERAL_SYSTEM_PROMPT + (("\n\n" + system_extra) if system_extra else "")
    try:
        out = llm.complete(system, history + [{"role": "user", "content": text}], max_tokens=400)
    except LLMError:
        return None
    out = strip_citations(rag.clean_model_text(out or ""))   # model yine de [1] yazarsa kaynak sanilmasin
    return out or None


def send_message(conn, user: dict, conv_id: int, text: str, llm, embedder=None) -> dict:
    """Soruyu yanitlar ve (soru, yanit, kaynaklar)i kalici olarak kaydeder.

    LLM/embedding hatasi olursa HICBIR sey kaydedilmez (gecmis bozulmaz, kullanici soruyu tekrar gonderebilir).
    """
    conv = get_owned_conversation(conn, user, conv_id)
    text = (text or "").strip()
    if not text:                                   # LLM'e (ozet/yeniden yazma dahil) gitmeden once dogrula
        raise ValueError("Soru boş olamaz")
    if len(text) > config.MAX_QUESTION_CHARS:
        raise ValueError(f"Soru en fazla {config.MAX_QUESTION_CHARS} karakter olabilir")
    started = time.perf_counter()
    prior = repo.list_messages(conn, conv_id)

    history, extra = build_context(conn, conv, prior, llm)
    retrieval_query = rewrite_question(llm, history, text)
    result = rag.answer_question(conn, user["id"], text, llm, embedder=embedder, history=history,
                                 retrieval_query=retrieval_query, system_extra=extra)
    # Belgelerde yanit yoksa (ilgili parca yok ya da model BILGI_YOK dedi) ve genel sohbet aciksa: selamlasma ve
    # genel sorulara modelin kendi bilgisiyle yanit. Kaynak yok, grounded=False, durum "general" (arayuz etiketler).
    if config.GENERAL_CHAT and result.status in (rag.NO_CONTEXT, rag.NO_INFO):
        general = general_answer(llm, history, text,
                                 system_extra=("Önceki konuşmanın özeti:\n" + conv["summary"]) if conv.get("summary") else "")
        if general:
            result = rag.RagResult(general, GENERAL, False, [], result.best_score)
    latency_ms = int((time.perf_counter() - started) * 1000)

    if not prior and conv["title"] == repo.DEFAULT_TITLE:
        repo.rename_conversation(conn, conv_id, _clip(text, 60))
    user_id = repo.add_message(conn, conv_id, "user", text)
    assistant_id = repo.add_message(conn, conv_id, "assistant", result.answer, status=result.status,
                                    grounded=result.grounded, latency_ms=latency_ms, best_score=result.best_score)
    if result.status == rag.ANSWERED:
        repo.add_message_sources(conn, assistant_id, result.sources)
    return {
        "conversation_id": conv_id,
        "user_message": {"id": user_id, "role": "user", "content": text},
        "assistant_message": {"id": assistant_id, "role": "assistant", "content": result.answer,
                              "status": result.status, "grounded": result.grounded, "latency_ms": latency_ms,
                              "sources": result.sources},
        "retrieval_query": retrieval_query,
    }
