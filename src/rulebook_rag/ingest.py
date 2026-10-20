import json
import re
import pymupdf

JUNK_MARKERS = [
    "4C2S",                       # print spec: "700 x 161 mm, 4C2S Folded..."
    "©",                          # copyright lines (Catan and Monopoly)
    "Hasbro SA",                  # manufacturer address
    "Represented by",
    "P.O. Box",
    "consumer_affairs",
    "Fast-Dealing Property Trading Game",  # repeated slogan
    "are trademarks of Hasbro",
]

REPLACEMENTS = {
    "\u2011": "-",   # non-breaking hyphen → normal hyphen
    "\u200b": "",    # zero-width space → delete
    "\x07": "",      # control character → delete
    "\x03": "",      # control character → delete
    "\u2019": "'",   # curly apostrophe → straight (don’t → don't)
}


def extract_pages(pdf_path):
    # open the file
    # build the list of (page_number, text)
    # return the list

    doc = pymupdf.open(pdf_path)

    pages = []
    for page_number, page in enumerate(doc, start = 1):
        #print(page_number)
        blocks = page.get_text("blocks", sort=True)
        text = "\n\n".join([block[4].strip() for block in blocks])
        pages.append((page_number, text))
    return pages


def normalize_characters(text):
    for old, new in REPLACEMENTS.items():
        text = text.replace(old, new)
    return text


def fix_currency(text, game):
    if game != "monopoly":
        return text
    return re.sub(r"\b[aAb](\d+)", r"M\1", text)


def remove_junk_lines(text):
    blocks = text.split("\n\n")
    kept = []
    for block in blocks:
        if any(marker in block for marker in JUNK_MARKERS):
            continue
        kept.append(block)
    return "\n\n".join(kept)

def join_broken_lines(text):
    blocks = text.split("\n\n")          # separate the paragraphs
    kept = []
    for block in blocks:
        block = block.replace("\n", " ")       # 1. join the broken lines
        block = re.sub(r" +", " ", block)      # 2. squeeze double spaces
        block = block.strip()                  # 3. trim the ends
        kept.append(block)                     # 4. keep it
    return "\n\n".join(kept) 


def clean_text(text, game):
    text = normalize_characters(text)   # rows 2 + 13
    text = fix_currency(text, game)     # row 1
    text = remove_junk_lines(text)      # rows 3, 4, 5
    text = join_broken_lines(text)      # row 12
    return text


PDF_PATHS = {
    "catan": "data/raw/catan.pdf",
    "monopoly": "data/raw/monopoly.pdf",
    "blackjack": "data/raw/blackjack.pdf",
    "poker": "data/raw/poker.pdf",
    "rummy": "data/raw/rummy.pdf",
    "texas_holdem": "data/raw/texas_holdem.pdf",
}
OUTPUT_PATH = "data/processed/cleaned_pages.json"


def run_ingest():
    cleaned_pages = {}
    for game, pdf_path in PDF_PATHS.items():
        pages = extract_pages(pdf_path)           # extract this PDF
        cleaned_pages[game] = []
        for page_number, text in pages:
            cleaned_pages[game].append((page_number, clean_text(text, game)))   # (page_number, cleaned text)
        print(f"{game}: {len(pages)} pages")

    with open(OUTPUT_PATH, "w") as f:
        json.dump(cleaned_pages, f, indent=2, ensure_ascii=False)
    print(f"Saved to {OUTPUT_PATH}")

if __name__ == "__main__":
       run_ingest()

