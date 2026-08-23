
from pathlib import Path
import fitz

DOC_DIR = Path("data/documents")


def source_metadata(filename: str) -> dict:
    """Assign authority/reliability metadata without tuple-unpacking."""
    lower = filename.lower()

    if "agreement" in lower:
        authority, status, source_type = 5, "current", "customer_agreement"
    elif "deprecated" in lower:
        authority, status, source_type = 2, "deprecated", "deprecated_policy"
    elif "sop" in lower:
        authority, status, source_type = 4, "current", "current_sop"
    elif "current" in lower or "policy" in lower:
        authority, status, source_type = 4, "current", "current_policy"
    elif "product" in lower:
        authority, status, source_type = 3, "current", "product_documentation"
    elif "ticket" in lower or "historical" in lower:
        authority, status, source_type = 1, "historical", "historical_ticket"
    else:
        authority, status, source_type = 3, "current", "document"

    customer = None
    if "northstar" in lower:
        customer = "Northstar Logistics"
    elif "lumenworks" in lower:
        customer = "LumenWorks"

    return {
        "source": filename,
        "authority": authority,
        "status": status,
        "source_type": source_type,
        "customer": customer,
    }


def extract_chunks(chunk_size: int = 1200, overlap: int = 180) -> list[dict]:
    chunks = []

    if not DOC_DIR.exists():
        return chunks

    for pdf_path in sorted(DOC_DIR.glob("*.pdf")):
        metadata = source_metadata(pdf_path.name)

        try:
            doc = fitz.open(pdf_path)

            for page_number, page in enumerate(doc, start=1):
                text = page.get_text("text").strip()
                if not text:
                    continue

                start = 0
                while start < len(text):
                    end = min(start + chunk_size, len(text))
                    content = text[start:end].strip()

                    if content:
                        chunks.append({
                            **metadata,
                            "page": page_number,
                            "content": content,
                        })

                    if end >= len(text):
                        break

                    start = max(0, end - overlap)

            doc.close()

        except Exception as exc:
            # One bad PDF must not prevent the application from starting.
            print(f"[retrieval] Skipping {pdf_path.name}: {exc}")

    return chunks


def ensure_index() -> dict:
    """
    Always return the expected index shape.
    Retrieval failures are isolated so Streamlit can still start.
    """
    try:
        chunks = extract_chunks()
        return {"chunks": chunks, "ready": bool(chunks), "error": None}
    except Exception as exc:
        return {"chunks": [], "ready": False, "error": str(exc)}
