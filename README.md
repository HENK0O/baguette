baguette

A 123M-parameter French language model trained from scratch — corpus, tokenizer, pretraining, conversational fine-tuning and evaluation included.

No pretrained weights, no transfer from English. The corpus, the vocabulary and all 123 million parameters are built here.

Total cost: about $12 of GPU time and 4 hours of compute.

Results

Compared against three public French GPT-2 models of equivalent size (~124M), on a validation corpus held out from training.

Model	bpb ↓	arithmetic ↑	facts ↑
baguette · 123M	1.200	93%	88%
GPT-fr small · 124M (Inria)	1.504	7%	38%
BelGPT-2 · 124M (60 GB of French)	1.732	7%	62%
GPT-2 fr · 124M (EN→FR transfer)	1.755	0%	38%

The headline metric is bits per byte, the only honest way to compare models with different tokenizers. BelGPT-2 saw 60 GB of French; baguette saw 3.2.

Generalisation

40 hand-written problems, phrased in ways absent from the training corpus:

Model	rephrased	new context	new concept	total
baguette	11/15	7/15	6/10	24/40
GPT-fr small	0/15	0/15	0/10	0/40
BelGPT-2	0/15	0/15	0/10	0/40
GPT-2 fr	0/15	0/15	1/10	1/40

Most of this gap comes from conversational fine-tuning, which the base models don't have: they follow no instructions and loop. The comparison measures the full pipeline, not pretraining alone.

What the model cannot do

On a second benchmark whose problem families are deliberately absent from the corpus, baguette scores 4/40:

family	score	
transitivity	3/6	A>B, B>C ⇒ A>C — never taught, learned from reading French
off-by-one	1/6	fencepost errors
trick questions	0/6	cannot say "I don't know"
composition	0/7	"double the double of 5" → computes a single double
branches, remainder, cycles	0/15	families absent from the corpus

The three GPT-2 models score 1 to 3 out of 40 on the same test, and no model passes a single trick question. Knowing when to refuse to answer is a capability that does not emerge from next-token prediction — it has to be taught.

Architecture

123M parameters (110M excluding embeddings), 16 layers, d=768.

GQA 3:1 — 12 query heads, 4 key/value heads
Zero-centred RMSNorm and QK-Norm (Qwen3.5)
Partial RoPE — 16 dimensions out of 64
SwiGLU, FFN width 2048
Muon for 2D matrices, AdamW for embeddings and gains
WSD schedule (Warmup-Stable-Decay) — a plateau, then decay over the final 20%
1024 context, 16,384-entry BPE vocabulary trained on the corpus
Corpus

836M pretraining tokens (French FineWeb-Edu, Wikipedia, dialogue) and 91M fine-tuning tokens, including a generated arithmetic dataset (gen_math.py) and distilled dialogue.

The tokenizer is trained on the corpus: weights and vocabulary go together, and a checkpoint is only usable with the tokenizer it learned on.

Usage
bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
Locally
bash
python run.py prepare --target-tokens 1e9   # corpus, tokenizer, binarisation
python run.py train   --preset small        # pretraining
python run.py sft                           # conversational fine-tuning
python run.py chat                          # talk to the result
python run.py info                          # corpus and checkpoint status

Training detects CUDA, MPS (Apple Silicon) or CPU. torch.compile is only enabled on CUDA — Triton does not exist on MPS.

On a MacBook Air M5, full pretraining would take roughly 17 days. Hence what follows.

On rented GPU

modal_train.py runs the same pipeline on an A100 via Modal, with a persistent volume for the corpus and checkpoints.

bash
modal run --detach modal_train.py::prepare
modal run --detach modal_train.py::train --steps 25000
modal run --detach modal_train.py::sft   --steps 2500
modal volume get llm-data runs/gpu1/sft/ckpt_best.pt ./runs/gpu1/sft/ckpt_best.pt

160,000 tokens/s, 42% MFU. Full pretraining fits in 3h20.

Containers are preemptible: Modal can reclaim the GPU at any time and then restarts the function with the same arguments. Without care, the run starts over from scratch and overwrites the work done. train() and sft() therefore detect the checkpoint at startup and add --resume themselves. Two preemptions occurred during pretraining, costing a few minutes each.

Evaluating
bash
modal run modal_train.py::extract_eval_text   # extract the real validation set
modal volume get llm-data eval_text.txt ./eval_text.txt
python bench_vs.py     --run gpu1             # against French GPT-2 models
python bench_ood.py    --run gpu1             # unseen problems
python bench_ood_v2.py --run gpu1             # held-out families

extract_eval.py replays the random draw performed by encode_pretrain (seed 1234) to recover the documents that actually went to validation. Reading the tail of the raw files, the obvious shortcut, would feed the model data it has already seen — and produce a flattering but meaningless bpb.

Files
	
run.py	entry point: prepare / train / sft / chat / info
model.py	architecture
data.py	corpus, tokenizer, binarisation
optim.py	Muon and learning-rate schedules
modal_train.py	training on rented GPU
gen_math.py	arithmetic corpus generation
rebuild_sft.py	fine-tuning corpus rebinarisation
extract_eval.py	validation set extraction
bench_*.py	evaluation

Weights and corpus are not versioned (1 GB per checkpoint). The full pipeline reproduces with the commands above.

Two things learned along the way

Which fine-tuning data you use matters more than how much. The initial corpus contained a reasoning source whose <think> blocks ran to 300 words of hesitant monologue. The model learned to imitate them and would produce paragraphs of deliberation over "give me three colours". Removing that source improved validation loss and conciseness. Adding a systematically-covered arithmetic corpus afterwards — every two-digit addition, with the operation decomposed inside the <think> block — took arithmetic from 50% to 93% without degrading bits per byte.

A benchmark dies the moment its families enter the corpus. The first out-of-distribution benchmark measured generalisation; now that the arithmetic corpus covers doubles, halves and equal shares, it partly measures revision. Hence the second one, with families kept out — and the hygiene rule written at the top of the file.

Credits

Muon: Keller Jordan. Corpus: FineWeb-Edu (HuggingFace), French Wikipedia. The v2 out-of-distribution benchmark reuses the structure and problem families designed by @0xZKnw for his own model