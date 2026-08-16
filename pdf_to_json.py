import json
from pathlib import Path
import fitz  # PyMuPDF

# Path to the folder containing all the PDFs
PDF_FOLDER = Path(__file__).parent / "BIT_Jaipur_Data"
OUTPUT_FILE = Path(__file__).parent / "data" / "bit_jaipur_data.json"

def extract_pdf_text(pdf_path: Path) -> str:
    pages_text = []
    with fitz.open(str(pdf_path)) as doc:
        for page in doc:
            pages_text.append(page.get_text())
    return "\n".join(pages_text).strip()

def main():
    data = []
    for pdf_path in sorted(PDF_FOLDER.rglob("*.pdf")):
        rel_path = pdf_path.relative_to(PDF_FOLDER)
        category = rel_path.parts[0] if len(rel_path.parts) > 1 else "root"
        try:
            text = extract_pdf_text(pdf_path)
        except Exception as e:
            text = ""
            print(f"Failed to extract {pdf_path}: {e}")

        data.append({
            "file_name": pdf_path.name,
            "relative_path": str(rel_path).replace("\\", "/"),
            "category": category,
            "content": text,
        })
        print(f"Processed: {rel_path}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\nDone. Extracted {len(data)} PDFs into {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
