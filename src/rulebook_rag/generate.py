from dotenv import load_dotenv
import anthropic
from rulebook_rag.retrieve import Retriever

load_dotenv()                      # reads .env from the folder you run from (Game)
MODEL = "claude-haiku-5-5"

SYSTEM = """You answer questions about board and card game rules, using ONLY the rulebook excerpts provided.

Rules:
1. Use only the excerpts. Do not use outside knowledge, even if you know the game well.
2. Each excerpt is labeled with its game. Only use excerpts from the game the question asks about.
   If the question names no game, answer separately for each game whose excerpts actually answer it, labeled by game.
   Leave out games whose excerpts don't address the question.
   If the question uses a term that belongs to only one game (e.g. "hole cards" for Texas Hold'em), treat it as about that game.
3. After each claim, cite the excerpt id in square brackets, e.g. [catan-p9-c0].
4. If the excerpts do not contain the answer, reply exactly: "The provided rules don't cover this."
   You may then mention the closest related rule, clearly labeled as related.
5. Be short and direct."""                 


def format_context(chunks):
    
    parts = []
    for c in chunks:
        parts.append(f"<excerpt id=\"{c['id']}\" game=\"{c['game']}\" page=\"{c['page']}\">\n{c['text']}\n</excerpt>")
    return "\n\n".join(parts)


class Generator:
    def __init__(self):
        self.retriever = Retriever()
        self.client = anthropic.Anthropic()

    def answer(self, question):
        chunks = self.retriever.search_routed(question)
        user_message = f"Excerpts:\n{format_context(chunks)}\n\nQuestion: {question}"
        response = self.client.messages.create(
            model=MODEL,
            max_tokens=2000,                      
            system=SYSTEM,
            messages=[{"role": "user", "content": user_message}],
        )
        if response.stop_reason == "max_tokens":
            print("WARNING: response was cut off")
        text = "".join(b.text for b in response.content if b.type == "text")
        return text, chunks


if __name__ == "__main__":
    gen = Generator()
    text, chunks = gen.answer("Do you collect money for landing on Free Parking?")
    print(text)
    print([c["id"] for c in chunks])