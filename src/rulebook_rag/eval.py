import csv
import os
import sys
from collections import Counter

from rulebook_rag.generate import Generator, MODEL

QUESTIONS_PATH = "eval/questions.csv"

JUDGE_SYSTEM = """You grade answers to rulebook questions.
Compare the ANSWER with the EXPECTED answer.
- PASS if the answer states the same facts as EXPECTED (wording may differ; extra correct detail is fine).
- FAIL if it contradicts EXPECTED, misses a key fact, or invents a rule.
- If EXPECTED says the rules don't specify it, PASS only if the answer clearly says the rules don't cover it.
Reply in exactly this format:
VERDICT: PASS or FAIL
REASON: one sentence """   

def judge(client, question, expected, answer_text):
    msg = f"QUESTION: {question}\nEXPECTED: {expected}\nANSWER: {answer_text}"
    response = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=JUDGE_SYSTEM,
        messages=[{"role": "user", "content": msg}],
    )

    if response.stop_reason == "max_tokens":
        print("WARNING: response was cut off")
    out = "".join(b.text for b in response.content if b.type == "text")
    if "VERDICT: PASS" in out:
        verdict = "PASS"
    elif "VERDICT: FAIL" in out:
        verdict = "FAIL"
    else:
        verdict = "ERROR"     # the judge didn't answer, so we don't know
    return verdict, out


def run_eval(run_name):
    out_path = f"eval/results_{run_name}.csv"
    if os.path.exists(out_path):                                   # check BEFORE spending API calls
        sys.exit(f"{out_path} already exists. Pick a new run name.")

    gen = Generator()
    with open(QUESTIONS_PATH) as f:
        questions = list(csv.DictReader(f))

    results = []
    for row in questions:
        text, chunks = gen.answer(row["question"])
        verdict, note = judge(gen.client, row["question"], row["expected_answer"], text)
        results.append({
            "id": row["id"],
            "question_type": row["question_type"],
            "question": row["question"],
            "expected_answer": row["expected_answer"],
            "answer": text,
            "chunks": ";".join(c["id"] for c in chunks),
            "verdict": verdict,
            "judge_note": note,
        })
        print(row["id"], row["question_type"], verdict)

    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    total = Counter(r["question_type"] for r in results)
    passed = Counter(r["question_type"] for r in results if r["verdict"] == "PASS")
    for t in total:
        print(f"{t}: {passed[t]}/{total[t]}")
    print(f"TOTAL: {sum(passed.values())}/{len(results)}  (model: {MODEL})  → {out_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: PYTHONPATH=src python -m rulebook_rag.eval <run_name>")
    run_eval(sys.argv[1])