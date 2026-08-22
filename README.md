# baguette

**A 123M-parameter French language model, trained from scratch for $12.**

No pretrained weights, no transfer from English. The corpus, the 16,384-entry vocabulary and all 123 million parameters are built here. baguette works through problems in a `<think>…</think>` scratchpad before answering, and beats the public French GPT-2s at the same size on language modelling, arithmetic and factual recall.

```
you   › Calcule : 88 + 59
model › <think>
        88 + 59.
        Dizaines : 80 + 50 = 130.
        Unités : 8 + 9 = 17.
        Total : 130 + 17 = 147.
        </think>
        147

you   › Bonjour, tu peux te présenter ?
model › <think>
        </think>
        Bonjour ! Je suis un petit assistant français. Comment puis-je vous aider ?
```

The scratchpad fills up for a calculation and stays empty for small talk: the model learns *when* to think, not just how.

**Qwen3.5-style** architecture, **Muon** optimizer, **WSD** schedule, full pipeline from corpus download to benchmark. 3h20 of A100 time for pretraining, 25 minutes for fine-tuning.

---

## Results

Against the closest public French causal LMs, all of comparable size — [GPT-fr small](https://huggingface.co/asi/gpt-fr-cased-small), [BelGPT-2](https://huggingface.co/antoinelouis/belgpt2), [gpt2-french-small](https://huggingface.co/dbddv01/gpt2-french-small):

| model | params | bpb ↓ ¹ | arithmetic ↑ ² | facts ↑ ³ |
|---|---|---|---|---|
| **baguette (sft)** | **123M** | **1.197** | **97%** | **100%** |
| GPT-fr small (Inria) | 124M | 1.504 | 7% | 38% |
| BelGPT-2 (60 GB corpus) | 124M | 1.732 | 7% | 62% |
| French GPT-2 (transfer) | 124M | 1.755 | 0% | 38% |

¹ *bits per byte* on 300k characters of held-out French — the only honest way to compare losses across different tokenizers. The held-out set is recovered by replaying the validation draw of `encode_pretrain` (seed 1234), not by reading the tail of the raw files, which would be training data.
² 30 arithmetic problems from a generation seed never used in training, greedy decoding. baguette answers in its native chat format; the base models get a 3-shot prompt, their best protocol. This measures the full pipeline, fine-tuning included — not pretraining alone.
³ 8 factual completions, raw continuation, regex-scored. Same protocol for every model.

The baselines' occasional points are scoring artefacts: the grader reads the last number in the output, and a degenerate loop eventually emits a matching one by chance. Asked to compute 45 ÷ 9, BelGPT-2 answers *"15 + 5Ha ! Il est donc important de bien choisir son matériel…"* and scores the point. Their real arithmetic score is zero.

Full reports with every answer: `bench_reports/`.

### The honest benchmark

40 **out-of-distribution** problems — reworded phrasings, novel contexts, novel concepts, all hand-written (`bench/bench_ood.py`):

| | reworded | novel context | novel concept | total |
|---|---|---|---|---|
| **baguette** | 11/15 | 10/15 | 7/10 | **28/40** |
| best 124M baseline | 0/15 | 0/15 | 1/10 | 1/40 |

The baselines score zero because they follow no instructions at all: they loop on the question instead of answering it. And baguette's own score deserves an asterisk — since the arithmetic corpus now covers doubles, halves and equal shares, part of the *reworded* column measures revision rather than generalisation. Which is why there is a second benchmark.

### The benchmark that hurts

Seven problem families deliberately kept out of every corpus (`bench/bench_ood_v2.py`). baguette scores **18/40**:

| family | | what it tests |
|---|---|---|
| composition | **7/7** | "double the double of 5" — two chained operations |
| trick questions | **5/6** | saying "I don't know" instead of inventing a number |
| transitivity | 2/6 | A>B, B>C ⇒ A>C — never taught, learned from reading French |
| branches | 2/5 | comparing two computations and picking a side |
| cycles | 1/5 | days of the week, modular arithmetic in words |
| off-by-one | 1/6 | fenceposts, inclusive bounds, ribbon cuts |
| remainder | 0/5 | euclidean division — what is *left over* |

The first run of this benchmark scored **4/40**, with zeroes in composition and trick questions: asked how many bananas were in a basket of apples and oranges, baguette confidently answered eight. Both families were then added to `gen_math.py` — chained operations with each step written out in the scratchpad, and problems whose answer is *"the statement doesn't say"*. One 25-minute fine-tuning run later, composition went to 7/7 and trick questions to 5/6, with bits per byte, arithmetic and factual recall all improving at the same time.

The remaining families are untouched by any training data, and it shows. Remainder stays at zero: the model divides but never reports what is left over. Transitivity actually *dropped* from 3/6 — whatever little it had was diluted. And it now occasionally over-refuses: asked what day follows Tuesday by three, it answers that the statement doesn't say.

The three GPT-2 baselines score 1 to 3 out of 40 here. Both benchmarks ship with the repo, because either one alone would tell a lie.

---

## Try it

Weights are in the [latest release](../../releases/latest): `baguette-123m-sft.pt` (chat, recommended), `baguette-123m-base.pt` (before fine-tuning), and `tokenizer.json`. fp16, weights only, 258 MB each.

```bash
pip install -r requirements.txt
```

Lay the files out like this — the `ckpt_latest.pt` name matters:

```
runs/baguette/tokenizer.json
runs/baguette/sft/ckpt_latest.pt      <- baguette-123m-sft.pt renamed
```

Then:

```bash
python run.py chat --run baguette --temperature 0.5 --top-k 20
```

**Use those sampling settings.** At 123M the defaults (0.8 / 50) are too permissive and the model wanders; 0.5 / 20 is where it holds together. Chat commands: `/think auto|on|off`, `/temp`, `/topp`, `/topk`, `/max`, `/raw <text>`, `/reset`, `/quit`. CPU is plenty for inference at this size.

---

## The repo

```
run.py               CLI: prepare / train / sft / chat / info
model.py             Qwen3.5-style architecture: GQA, zero-centred QK-Norm,
                     partial RoPE, SwiGLU, KV-cached generation
data.py              French corpus download, BPE tokenizer, binarisation,
                     <think> format conversion
optim.py             Muon (batched Newton-Schulz orthogonalization) + LR schedules
gen_math.py          French arithmetic generator: systematic coverage, every
                     operation decomposed inside the scratchpad
modal_train.py       the same pipeline on a rented A100
rebuild_sft.py       rebuild the fine-tuning corpus without retraining the tokenizer
extract_eval.py      recover the true validation set by replaying the seed-1234 draw
export_weights.py    training checkpoint (1 GB) -> fp16 weights (258 MB)
bench/
  bench_vs.py        vs the public French GPT-2s (bpb, arithmetic, facts)
  bench_ood.py       40 hand-written unseen problems
  bench_ood_v2.py    seven held-out families
bench_reports/       full reports, every model answer included
```

---

## Reproduce it

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Locally

```bash
python run.py prepare --target-tokens 1e9   # corpus, tokenizer, binarisation
python run.py train   --preset small        # pretraining
python run.py sft                           # conversational fine-tuning
python run.py chat                          # talk to the result
```

Training auto-detects CUDA, MPS (Apple Silicon) or CPU. `torch.compile` is CUDA-only — Triton does not exist on MPS, which costs about half the throughput.

On a MacBook Air M5 the full run would take roughly **17 days**: 1,300 tokens/s against an A100's 160,000. Hence what follows.

### On a rented A100 (~$12, 4 hours)

```bash
modal run --detach modal_train.py::prepare
modal run --detach modal_train.py::train --steps 25000
modal run --detach modal_train.py::sft   --steps 2500
modal volume get llm-data runs/gpu1/sft/ckpt_best.pt ./runs/gpu1/sft/ckpt_best.pt
```

**160,000 tokens/s, 42% MFU, 21 GB peak.** Pretraining: 25,000 steps, 1.64B tokens, 3h20, val loss 2.54 (ppl 12.6). Fine-tuning: 2,500 steps, 25 min, val loss 1.42.

`Ctrl+C` stops cleanly with a checkpoint, auto-checkpoint every 5 minutes, `--resume` picks up at the exact step with the optimizer state, RNG and batch order restored.

⚠️ **Modal containers are preemptible.** When the GPU is reclaimed, Modal restarts the function *with the same arguments* — which means starting over from scratch and overwriting the run in progress. `train()` and `sft()` therefore check for a checkpoint at startup and add `--resume` themselves. Two preemptions happened during pretraining; each cost about a minute.

### Evaluating

```bash
modal run modal_train.py::extract_eval_text   # recover the true validation set
modal volume get llm-data eval_text.txt ./eval_text.txt

python -m bench.bench_vs     --run gpu1       # against the French GPT-2s
python -m bench.bench_ood    --run gpu1       # 40 unseen problems
python -m bench.bench_ood_v2 --run gpu1       # seven held-out families
```

Add `--skip-hf` (or `--hf none` for v2) to evaluate baguette alone, without downloading the baselines.

`extract_eval.py` replays the validation draw performed by `encode_pretrain` (seed 1234) to recover the documents that actually went to validation. Reading the tail of the raw corpus files, the obvious shortcut, would feed the model data it has already seen — and produce a flattering but meaningless bpb.

### The data

836M pretraining tokens, 91M fine-tuning tokens.

| source | role |
|---|---|
| FineWeb-Edu (`fra_Latn`) | filtered French web |
| French Wikipedia | clean, factual French |
| `french_instruct` | 275k French conversations |
| French Alpaca | instructions |
| distilled dialogue | `<think>` traces |
| **`gen_math.py`** | **locally generated arithmetic, solutions computed in Python** |

The tokenizer is trained on the corpus: weights and vocabulary go together, and a checkpoint is only usable with the tokenizer it learned on. Re-running `prepare` trains a new one and silently breaks every existing checkpoint — hence `rebuild_sft.py`, which rebuilds the fine-tuning binaries against the existing tokenizer.

---

## What actually moved the needle

**Removing data, not adding it.** The fine-tuning corpus included a reasoning source whose `<think>` blocks ran to 300 words of hesitant monologue — *"alternatively, perhaps the user means…"*. The model learned to imitate the form without the function and would deliberate for four paragraphs over "give me three colours". Dropping that source improved validation loss *and* conciseness, in one 25-minute run.

**Systematic coverage beats sampling.** The model got 7×11 right and 88+59 wrong: it had memorised cases rather than learned a procedure. `gen_math.py` emits *every* two-digit addition, with the operation decomposed in the scratchpad — `80+50=130, 8+9=17, total 147`. Arithmetic went from 50% to 93%, then to 97% once chained operations were added. Teaching a procedure generalises; teaching answers does not.

**Fixing one weakness fixed three.** The second round of generated data targeted exactly two failures — composed operations and unanswerable questions — plus two-turn dialogues where the topic changes between turns. Composition went 0/7 → 7/7 and trick questions 0/6 → 5/6, as intended. But factual recall also went 88% → 100% and bits per byte improved, neither of which was targeted. The likeliest explanation is the two-turn examples, which pair a calculation with an unrelated factual question and seem to have stabilised switching between the two modes.

**A benchmark dies the moment its families enter the corpus.** The first OOD benchmark measured generalisation until the arithmetic corpus started covering doubles and halves. It now partly measures revision, which is why `bench/bench_ood_v2.py` exists, with a hygiene rule written at the top of the file: none of these problems may ever enter a training set.

---

## Limitations

A 123M model trained on 1.64B tokens is not ChatGPT.

**Works:** correct French, short structured answers, two-digit arithmetic in its own format (97%), chained operations, readable scratchpad, clean stops, factual recall on common knowledge (100% on the eight probes used here), and saying "the statement doesn't say" when the question is unanswerable (5/6).

**Fragile:** subtraction sometimes runs backwards (80 − 46 → 24), multiplication and division get swapped, transitive comparisons (2/6), and it occasionally over-refuses on questions it could answer.

**Doesn't:** euclidean remainders (0/5) — it divides but never reports what is left over. Day-of-the-week arithmetic. Fencepost counting. Long context. Anything that isn't French. And having been fine-tuned partly on dialogue shared with [frlm](https://github.com/0xZKnw/frlm), it occasionally introduces itself under that name — a small reminder of how much of a model's identity comes from its fine-tuning data.

---

## Credits

Muon: [Keller Jordan](https://kellerjordan.github.io/posts/muon/).
Architecture: [Qwen3.5](https://huggingface.co/blog/mlabonne/qwen35).
Corpus: FineWeb-Edu, French Wikipedia, and the datasets listed above.
The v2 out-of-distribution benchmark reuses the structure and problem families designed by [@0xZKnw](https://github.com/0xZKnw) for [frlm](https://github.com/0xZKnw/frlm) — a 58M French reasoning model built in parallel with this one, and the reason several of the ideas here exist.

## License

MIT. The listed datasets keep their respective licenses.