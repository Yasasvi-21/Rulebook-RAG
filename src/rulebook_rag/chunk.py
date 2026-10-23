import json

INPUT_PATH = "data/processed/cleaned_pages.json"
OUTPUT_PATH = "data/processed/chunks.json"

def chunk_page(text, game, page_number, target=800):
    chunks = []
    current = []          # blocks in the chunk being built
    current_len = 0

    for block in text.split("\n\n"):
        if not block.strip():                 # skip empty blocks
            continue

        # adding this block would overflow, so save the current chunk first
        if current_len + len(block) + 2 > target and current:
            chunks.append({
                "id": f"{game}-p{page_number}-c{len(chunks)}",
                "game": game,
                "page": page_number,
                "text": "\n\n".join(current),
            })
            current = []
            current_len = 0

        current.append(block)
        current_len += len(block) + 2

    # after the loop: save whatever is left (the end of the page)
    if current:
        chunks.append({
            "id": f"{game}-p{page_number}-c{len(chunks)}",
            "game": game,
            "page": page_number,
            "text": "\n\n".join(current),
        })

    return chunks


def run_chunking():
    # 1. load the cleaned pages produced by ingest.py
    with open(INPUT_PATH) as f:
        pages = json.load(f)

    # 2. chunk every page of every game
    all_chunks = []
    for game, game_pages in pages.items():
        for page_number, text in game_pages:
            all_chunks.extend(chunk_page(text, game, page_number))

    # 3. save
    with open(OUTPUT_PATH, "w") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    # 4. report
    counts = {}
    for c in all_chunks:
        counts[c["game"]] = counts.get(c["game"], 0) + 1
    print(len(all_chunks), "chunks total")
    print(counts)
    print(f"Saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    run_chunking()