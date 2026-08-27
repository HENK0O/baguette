import modal

app = modal.App("llm-fr")

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("torch", "numpy", "datasets", "tokenizers", "rich")
    .add_local_dir(".", remote_path="/root/llm",
                   ignore=[
                       "data", "runs", ".venv", "__pycache__", ".git",
                       ".env", ".env.*", ".modal.toml",
                       "*.pem", "*.key", "*.p12", "*.pfx",
                   ])
)

vol = modal.Volume.from_name("llm-data", create_if_missing=True)


@app.function(image=image, cpu=8.0, volumes={"/root/persist": vol},
              timeout=60 * 60 * 4)
def prepare():
    import subprocess
    subprocess.run(
        ["python", "run.py", "prepare", "--target-tokens", "1e9",
         "--data-dir", "/root/persist/data"],
        cwd="/root/llm", check=True)
    vol.commit()


@app.function(image=image, gpu="H100", volumes={"/root/persist": vol},
              timeout=60 * 60 * 6)
def train(steps: int = 200, resume: bool = False):
    import os, subprocess
    vol.reload()
    if os.path.exists("/root/persist/runs/gpu1/pretrain/ckpt_latest.pt"):
        resume = True
    cmd = ["python", "run.py", "train", "--run", "gpu1", "--preset", "small",
           "--max-steps", str(steps), "--batch-size", "32", "--seq-len", "1024",
           "--data-dir", "/root/persist/data", "--out-dir", "/root/persist/runs",
           "--gpu-peak-tflops", "312"]
    if resume:
        cmd.append("--resume")
    subprocess.run(cmd, cwd="/root/llm", check=True)
    vol.commit()


@app.function(image=image, gpu="A100-80GB", volumes={"/root/persist": vol},
              timeout=60 * 60 * 6)
def sft(steps: int = 4000, resume: bool = False):
    import os, subprocess
    vol.reload()
    if os.path.exists("/root/persist/runs/gpu1/sft/ckpt_latest.pt"):
        resume = True
    cmd = ["python", "run.py", "sft", "--run", "gpu1", "--preset", "small",
           "--max-steps", str(steps), "--batch-size", "32", "--seq-len", "1024",
           "--data-dir", "/root/persist/data", "--out-dir", "/root/persist/runs",
           "--gpu-peak-tflops", "312"]
    if resume:
        cmd.append("--resume")
    subprocess.run(cmd, cwd="/root/llm", check=True)
    vol.commit()


@app.function(image=image, cpu=8.0, volumes={"/root/persist": vol},
              timeout=60 * 60 * 2)
def rebuild_sft(repeat: int = 25, repeat_math: int = 1):
    import subprocess
    vol.reload()
    subprocess.run(["python", "rebuild_sft.py", "/root/persist/data",
                    str(repeat), str(repeat_math)],
                   cwd="/root/llm", check=True)
    vol.commit()


@app.function(image=image, cpu=4.0, volumes={"/root/persist": vol},
              timeout=60 * 60)
def extract_eval_text(n_chars: int = 400000):
    import subprocess
    vol.reload()
    subprocess.run(["python", "extract_eval.py", "/root/persist/data",
                    "/root/persist/eval_text.txt", str(n_chars)],
                   cwd="/root/llm", check=True)
    vol.commit()
