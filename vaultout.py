"""Turn segments into a vault Markdown note."""
import os, re, datetime

VAULT = os.getenv("VAULT", os.path.join(os.path.expanduser("~"), "vault"))

SIGNALS = [
    "budget", "magkano", "presyo", "price", "pricing", "how much", "cost",
    "commit", "sign", "contract", "deal", "start", "when can we", "kailan",
    "monthly", "installment", "bayad", "discount", "quota", "proposal",
    "ghl", "whatsapp", "sige", "payment", "invoice", "onboarding", "timeline",
]


def ts(seconds):
    return str(datetime.timedelta(seconds=int(seconds)))


def find_signals(rows):
    hits = []
    for start, speaker, text in rows:
        low = text.lower()
        for kw in SIGNALS:
            if kw in low:
                hits.append((start, speaker, kw, text))
                break
    return hits


def slug(name):
    return re.sub(r"[^A-Za-z0-9 .()&+-]", "", name).strip() or "Unknown"


def resolve_path(prospect, date_str):
    """Project folder if it exists, otherwise the Inbox."""
    proj = os.path.join(VAULT, "10 - Projects")
    if os.path.isdir(proj):
        for entry in os.listdir(proj):
            if prospect.lower() in entry.lower() or entry.lower() in prospect.lower():
                d = os.path.join(proj, entry, "Calls")
                os.makedirs(d, exist_ok=True)
                return os.path.join(d, f"{date_str} - Discovery Call.md")
    d = os.path.join(VAULT, "00 - Inbox", "Call Transcripts")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"{date_str} - {slug(prospect)}.md")


def write_note(rows, prospect, source, language, duration, extra=""):
    date_str = datetime.date.today().isoformat()
    path = resolve_path(prospect, date_str)
    hits = find_signals(rows)

    out = []
    out.append("---")
    out.append("type: call-transcript")
    out.append("status: raw")
    out.append(f"tags: [call, transcript, {slug(prospect).lower().replace(' ', '-')}]")
    out.append(f'updated: "{date_str}"')
    out.append("---")
    out.append("")
    out.append(f"# Call Transcript, {prospect}")
    out.append("")
    out.append(f"**Date:** {date_str}  ")
    out.append(f"**Source:** `{os.path.basename(source)}`  ")
    out.append(f"**Length:** {ts(duration)}  ")
    out.append(f"**Language detected:** {language}  ")
    out.append("**Consent:** confirmed before recording")
    out.append("")
    if extra:
        out.append(extra)
        out.append("")

    if hits:
        out.append("## Buying signals")
        out.append("")
        for start, speaker, kw, text in hits:
            out.append(f"- `{ts(start)}` **{kw}** ({speaker}): {text}")
        out.append("")

    out.append("## Transcript")
    out.append("")
    last = None
    for start, speaker, text in rows:
        if speaker != last:
            out.append("")
            out.append(f"**{speaker}**")
            last = speaker
        out.append(f"`{ts(start)}` {text}")
    out.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    return path
