# Data & Training Plan

**Copilot-Style Coding Agent - ML Training Strategy**
**Date: February 23, 2026**

---

## Table of Contents

1. [Overview](#1-overview)
2. [Training Data Sources](#2-training-data-sources)
3. [Data Collection Pipeline](#3-data-collection-pipeline)
4. [Data Filtering & Quality Control](#4-data-filtering--quality-control)
5. [Model Training Strategy](#5-model-training-strategy)
6. [Fine-Tuning Approaches](#6-fine-tuning-approaches)
7. [RLHF (Reinforcement Learning from Human Feedback)](#7-rlhf-reinforcement-learning-from-human-feedback)
8. [Evaluation & Benchmarks](#8-evaluation--benchmarks)
9. [Continuous Learning](#9-continuous-learning)
10. [Data Governance & Ethics](#10-data-governance--ethics)

---

## 1. Overview

### Goals

1. **High-Quality Suggestions**: Generate accurate, idiomatic code completions
2. **Context-Aware**: Leverage repository structure and recent edits
3. **Tool-Enabled**: Train models to use tools (test runners, linters, etc.)
4. **Safe & Ethical**: Filter out secrets, PII, offensive content, and license violations
5. **Continuous Improvement**: Learn from user feedback (accepted/rejected suggestions)

### Model Strategy

**Two-Tier Approach**:

1. **Fast Model (Tier 1)**: 1-7B parameters
   - **Purpose**: Inline completions (single-line to full functions)
   - **Latency**: <500ms (P95)
   - **Base Options**: CodeLlama-7B, StarCoder-3B, DeepSeek-Coder-6.7B

2. **Agent Model (Tier 2)**: 20-70B parameters
   - **Purpose**: Multi-step tasks, agentic workflows
   - **Latency**: 1-5s (acceptable)
   - **Base Options**: Mixtral-8x22B, GPT-4-Turbo (via API), Claude-3-Opus (via API)

### Training Phases

1. **Pre-Training**: Use public code corpora (optional, if training from scratch)
2. **Supervised Fine-Tuning (SFT)**: Fine-tune on high-quality code examples
3. **Tool Training**: Fine-tune on tool-use traces (function calling)
4. **RLHF**: Optimize based on acceptance/rejection signals
5. **Continuous Learning**: Retrain weekly with new accepted suggestions

---

## 2. Training Data Sources

### 2.1 Public Code Corpora

#### The Stack (HuggingFace)

- **Size**: 3TB+ of permissively licensed code
- **Languages**: 30+ programming languages
- **Licenses**: MIT, Apache-2.0, BSD (pre-filtered)
- **URL**: <https://huggingface.co/datasets/bigcode/the-stack>

**Considerations**:

- Already used to train StarCoder, CodeLlama
- Download and host locally (EU servers for compliance)
- Additional filtering may be needed (secrets, PII)

#### GitHub Public Repos

- **Size**: Petabytes (subset based on criteria)
- **Selection Criteria**:
  - Stars >10 (popularity filter)
  - Permissive licenses (MIT, Apache-2.0, BSD)
  - Recent activity (last 2 years)
  - Languages: Python, JavaScript, TypeScript, Go, Java, Rust
- **Access**: GitHub Archive, BigQuery Public Datasets

**Considerations**:

- Massive scale, requires filtering infrastructure
- License detection critical (see [SECURITY.md](./SECURITY.md))
- Respect rate limits if scraping directly

#### Stack Overflow

- **Size**: 50M+ questions and answers
- **License**: CC BY-SA 4.0 (attribution required)
- **Use Case**: Code snippets with explanations
- **Access**: Stack Overflow Data Dump (quarterly)

**Considerations**:

- Attribution required (display "Source: Stack Overflow" in UI)
- Quality varies (upvote filtering helps)
- Focus on high-voted answers

### 2.2 Internal Code Repositories (Opt-In)

#### Organization Repos

- **Source**: Internal GitLab/GitHub Enterprise
- **Size**: Varies (1-100GB per org)
- **Consent**: Explicit opt-in per repository
- **Use Case**: Domain-specific conventions, internal libraries

**Considerations**:

- **GDPR Critical**: Get explicit consent from org and developers
- **Privacy**: Never include secrets, PII, or proprietary business logic in training
- **Anonymization**: Strip author info, commit messages (optional)

#### Code Review Data

- **Source**: Pull request comments, code reviews
- **Use Case**: Learn from expert feedback (e.g., "This should use async/await" → improve suggestion)

**Considerations**:

- High-value signal (human expert corrections)
- Privacy: anonymize reviewers, redact sensitive comments

### 2.3 Synthetic Data

#### Test Case Generation

- **Method**: Use LLM to generate tests for functions
- **Example**:
  - Input: Function signature `def add(a, b)`
  - Output: Unit tests `assert add(2, 3) == 5`
- **Use Case**: Train agent model to generate tests

#### Code Transformation Pairs

- **Method**: Automated transformations (e.g., Python 2 → Python 3, refactor to use list comprehensions)
- **Use Case**: Train refactoring capabilities

#### Documentation → Code

- **Method**: Generate code from docstrings or comments
- **Example**:
  - Input: `# Function to calculate factorial recursively`
  - Output: `def factorial(n): return 1 if n == 0 else n * factorial(n-1)`

### 2.4 Human-Curated Examples

#### High-Quality Prompts

- **Method**: Engineers write ideal prompt-completion pairs
- **Example**:
  - Prompt: `# Parse JSON from API response`
  - Completion: `import json\ndata = json.loads(response.text)`
- **Volume**: 500-1000 examples per language

#### Tool-Use Traces

- **Method**: Manually create examples of agent using tools
- **Example**:

  ```json
  {
    "task": "Add caching to user service",
    "steps": [
      {"action": "edit_file", "file": "user_service.py", "changes": "..."},
      {"action": "run_tests", "output": "3 passed"},
      {"action": "create_pr", "title": "Add caching", "body": "..."}
    ]
  }
  ```

- **Volume**: 100-200 traces covering common workflows

---

## 3. Data Collection Pipeline

### 3.1 Architecture

```text
┌────────────────────────────────────────────────────────────┐
│                   DATA SOURCES                             │
│  ┌────────────┐  ┌────────────┐  ┌─────────────────────┐  │
│  │The Stack   │  │GitHub      │  │Internal Repos       │  │
│  │(Public)    │  │Public      │  │(Opt-In)             │  │
│  └─────┬──────┘  └─────┬──────┘  └──────┬──────────────┘  │
└────────┼────────────────┼─────────────────┼────────────────┘
         │                │                 │
         ▼                ▼                 ▼
┌────────────────────────────────────────────────────────────┐
│                 INGESTION LAYER                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Data Crawler (Apache Airflow DAGs)                  │  │
│  │  • Download files                                    │  │
│  │  • Extract metadata (language, license, author)      │  │
│  │  • Deduplicate (hashing)                             │  │
│  └──────────────────────┬───────────────────────────────┘  │
└───────────────────────────┼────────────────────────────────┘
                            ▼
┌────────────────────────────────────────────────────────────┐
│                 FILTERING LAYER                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Data Filters (PySpark or Ray jobs)                  │  │
│  │  • License detection (reject non-permissive)         │  │
│  │  • Secret detection (reject if secrets found)        │  │
│  │  • PII detection (reject emails, names)              │  │
│  │  • Quality filtering (length, syntax errors)         │  │
│  └──────────────────────┬───────────────────────────────┘  │
└───────────────────────────┼────────────────────────────────┘
                            ▼
┌────────────────────────────────────────────────────────────┐
│                 STORAGE LAYER                              │
│  ┌───────────────────────────────────────────────────┐    │
│  │  Training Data Lake (S3 Parquet files)            │    │
│  │  • Raw data (post-filtering)                      │    │
│  │  • Tokenized data (pre-processed for training)    │    │
│  │  • Metadata (provenance, license, quality score)  │    │
│  └───────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────┘
```

### 3.2 Ingestion (Apache Airflow)

**DAG Example** (daily GitHub crawl):

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

def crawl_github_repos():
    """Fetch new repos from GitHub Archive."""
    # Query BigQuery: SELECT * FROM github_archive WHERE created > last_run
    # Download repo files
    # Save to S3 raw bucket
    pass

def deduplicate():
    """Remove duplicate files using content hashing."""
    # Compute SHA-256 for each file
    # Check against existing hashes
    # Keep only unique files
    pass

with DAG(
    'github_data_ingestion',
    default_args={'owner': 'ml-team'},
    description='Daily GitHub data ingestion',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2026, 2, 1),
    catchup=False
) as dag:

    crawl_task = PythonOperator(
        task_id='crawl_github_repos',
        python_callable=crawl_github_repos
    )

    dedup_task = PythonOperator(
        task_id='deduplicate',
        python_callable=deduplicate
    )

    crawl_task >> dedup_task
```

### 3.3 Filtering (PySpark)

**Secret Detection**:

```python
from pyspark.sql import SparkSession
import re

SECRET_PATTERNS = {
    'api_key': r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']([a-zA-Z0-9_\-]{20,})["\']',
    'password': r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']([^"\']+)["\']',
    # ... more patterns
}

def contains_secrets(code: str) -> bool:
    for pattern in SECRET_PATTERNS.values():
        if re.search(pattern, code):
            return True
    return False

spark = SparkSession.builder.appName("FilterSecrets").getOrCreate()

df = spark.read.parquet("s3://training-data/raw/")

# Filter out files with secrets
filtered_df = df.filter(~df["code"].rdd.map(contains_secrets).collect())

filtered_df.write.parquet("s3://training-data/filtered/")
```

**License Detection**:

```python
def get_license(repo_url: str, file_path: str) -> str:
    """Query license database for repo."""
    # Check if repo has LICENSE file
    # Or lookup from GitHub API
    # Return license type (MIT, Apache-2.0, etc.)
    pass

# Filter: keep only permissive licenses
ALLOWED_LICENSES = ['MIT', 'Apache-2.0', 'BSD-2-Clause', 'BSD-3-Clause']

filtered_df = df.filter(df["license"].isin(ALLOWED_LICENSES))
```

### 3.4 Tokenization

**Pre-Tokenization for Training**:

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("codellama/CodeLlama-7b-hf")

def tokenize_code(code: str) -> list[int]:
    return tokenizer.encode(code, add_special_tokens=True)

# Tokenize all code samples
df_tokenized = df.withColumn("tokens", tokenize_code(df["code"]))

# Save in HuggingFace dataset format
df_tokenized.write.parquet("s3://training-data/tokenized/")
```

---

## 4. Data Filtering & Quality Control

### 4.1 Filtering Criteria

| Filter | Purpose | Rejection Rate |
| -------- | --------- | -------------- |
| **License Check** | Reject non-permissive licenses | ~30% |
| **Secret Detection** | Reject files with API keys, passwords | ~5% |
| **PII Detection** | Reject files with emails, phone numbers | ~2% |
| **Syntax Errors** | Reject files that don't parse | ~10% |
| **Length Filter** | Reject very short (<10 lines) or very long (>1000 lines) files | ~15% |
| **Duplicate Detection** | Reject exact duplicates | ~20% |
| **Quality Score** | Reject files with low readability or many TODOs | ~10% |

**Overall Pass Rate**: ~40-50% of raw data (aggressive filtering for quality)

### 4.2 Quality Scoring

**Heuristics**:

```python
def quality_score(code: str, metadata: dict) -> float:
    """Compute quality score (0.0-1.0)."""
    score = 1.0

    # Penalty for many TODOs/FIXMEs
    todo_count = code.lower().count('todo') + code.lower().count('fixme')
    score -= min(0.3, todo_count * 0.05)

    # Penalty for commented-out code
    comment_lines = len([l for l in code.split('\n') if l.strip().startswith('#')])
    total_lines = len(code.split('\n'))
    if total_lines > 0 and comment_lines / total_lines > 0.4:
        score -= 0.2

    # Bonus for tests
    if 'test' in metadata.get('file_path', '').lower():
        score += 0.1

    # Bonus for documentation
    if code.count('"""') > 2 or code.count("'''") > 2:
        score += 0.1

    # Bonus for popular repo (GitHub stars)
    stars = metadata.get('stars', 0)
    if stars > 100:
        score += 0.1
    if stars > 1000:
        score += 0.1

    return max(0.0, min(1.0, score))

# Filter: keep only high-quality code (score >0.6)
df_quality = df.filter(df["quality_score"] > 0.6)
```

### 4.3 Deduplication

**Exact Deduplication** (hash-based):

```python
import hashlib

def compute_hash(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()

# Remove duplicates
df_dedup = df.dropDuplicates(["code_hash"])
```

**Near-Deduplication** (MinHash):

```python
from datasketch import MinHash, MinHashLSH

lsh = MinHashLSH(threshold=0.9, num_perm=128)

for idx, row in df.iterrows():
    minhash = MinHash(num_perm=128)
    for token in row['code'].split():
        minhash.update(token.encode())

    # Check if similar document exists
    if len(lsh.query(minhash)) == 0:
        lsh.insert(idx, minhash)
        # Keep this document
    else:
        # Reject as duplicate
        pass
```

---

## 5. Model Training Strategy

### 5.1 Base Model Selection

#### Option 1: Open-Source Models (Recommended)

**Fast Model**: CodeLlama-7B

- **Pros**: Good quality, open weights, commercially usable
- **Cons**: Requires fine-tuning for best results

**Agent Model**: Mixtral-8x22B (Mixture of Experts)

- **Pros**: Strong reasoning, efficient (sparse activation), open weights
- **Cons**: Large model (141B total params), requires A100/H100 GPUs

#### Option 2: Commercial APIs

**Fast Model**: GPT-3.5-Turbo (via OpenAI API)

- **Pros**: Proven quality, no hosting needed
- **Cons**: Data leaves EU (GDPR concerns), cost per token

**Agent Model**: GPT-4-Turbo or Claude-3-Opus

- **Pros**: Best quality, tool-use support built-in
- **Cons**: Expensive, data residency issues

**Recommended for Slovakia Team**:

- **Start**: CodeLlama-7B + Mixtral-8x22B (open-source)
- **Fallback**: If quality insufficient, evaluate GPT-4 API with EU data residency option (if available)

### 5.2 Training Infrastructure

#### Hardware Requirements

**Fine-Tuning Fast Model (7B)**:

- **GPUs**: 1-2x NVIDIA A100 (40GB) or 4x A10G (24GB)
- **Training Time**: ~24-48 hours for full fine-tune
- **Cost**: ~€500-€1,000 per training run (cloud spot instances)

**Fine-Tuning Agent Model (70B)**:

- **GPUs**: 8x NVIDIA A100 (80GB) or 4x H100 (80GB)
- **Training Time**: ~3-7 days for full fine-tune
- **Cost**: ~€10,000-€20,000 per training run

**Alternative: PEFT (Parameter-Efficient Fine-Tuning)**:

- **Method**: LoRA (Low-Rank Adaptation)
- **GPUs**: 1-2x A100 for 7B model, 4-8x A100 for 70B model
- **Training Time**: 50% faster than full fine-tune
- **Cost**: 50% cheaper
- **Trade-off**: Slightly lower quality (usually <5% drop)

**Recommended**: LoRA for frequent retraining, full fine-tune for major updates

#### Training Framework

**DeepSpeed** (Microsoft):

```python
from transformers import AutoModelForCausalLM, Trainer, TrainingArguments
from peft import get_peft_model, LoraConfig

model = AutoModelForCausalLM.from_pretrained("codellama/CodeLlama-7b-hf")

# LoRA config
lora_config = LoraConfig(
    r=16,  # Low-rank dimension
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],  # Which layers to adapt
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, lora_config)

training_args = TrainingArguments(
    output_dir="./output",
    per_device_train_batch_size=4,
    gradient_accumulation_steps=8,
    num_train_epochs=3,
    learning_rate=2e-5,
    fp16=True,  # Mixed precision
    deepspeed="ds_config.json",  # DeepSpeed config
    logging_steps=100,
    save_steps=1000,
    evaluation_strategy="steps",
    eval_steps=500
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset
)

trainer.train()
```

---

## 6. Fine-Tuning Approaches

### 6.1 Supervised Fine-Tuning (SFT)

**Goal**: Teach model to generate code in expected format (completions, explanations, tool calls)

**Data Format** (JSONL):

```jsonl
{"prompt": "def calculate_sum(numbers: list[int]) -> int:", "completion": "\n    \"\"\"Calculate sum of integers.\"\"\"\n    return sum(numbers)"}
{"prompt": "# TODO: Add error handling for division by zero\ndef divide(a: float, b: float) -> float:", "completion": "\n    if b == 0:\n        raise ValueError(\"Cannot divide by zero\")\n    return a / b"}
```

**Training**:

```python
# Load dataset
from datasets import load_dataset

dataset = load_dataset('json', data_files={'train': 'train.jsonl', 'eval': 'eval.jsonl'})

# Tokenize
def tokenize_function(examples):
    inputs = tokenizer(examples['prompt'], truncation=True, max_length=2048)
    labels = tokenizer(examples['completion'], truncation=True, max_length=512)
    inputs['labels'] = labels['input_ids']
    return inputs

tokenized_dataset = dataset.map(tokenize_function, batched=True)

# Train (see code in Section 5.2)
```

**Hyperparameters**:

- Learning rate: 1e-5 to 5e-5
- Batch size: 32-128 (with gradient accumulation)
- Epochs: 1-3 (avoid overfitting)
- Warmup steps: 500-1000

### 6.2 Instruction Tuning

**Goal**: Teach model to follow natural language instructions (for agent model)

**Data Format**:

```jsonl
{"instruction": "Refactor this function to use async/await", "input": "def fetch_data(url):\n    return requests.get(url).json()", "output": "import httpx\n\nasync def fetch_data(url: str) -> dict:\n    async with httpx.AsyncClient() as client:\n        response = await client.get(url)\n        return response.json()"}
```

**Dataset Construction**:

- Generate synthetic instructions using GPT-4
- Collect from user queries in pilot phase
- Curate from Stack Overflow (instruction = question, answer = explanation + code)

### 6.3 Tool-Use Training

**Goal**: Teach agent model to call tools (test runners, linters, git commands)

**Data Format** (Function Calling):

```jsonl
{
  "messages": [
    {"role": "system", "content": "You are a coding assistant. You can use tools: run_tests, lint_code, create_pr."},
    {"role": "user", "content": "Add tests for the User class in user.py"},
    {"role": "assistant", "content": null, "tool_calls": [
      {"id": "call_1", "function": {"name": "run_tests", "arguments": "{\"test_file\": \"tests/test_user.py\"}"}}
    ]},
    {"role": "tool", "content": "{\"status\": \"fail\", \"output\": \"No tests found\"}", "tool_call_id": "call_1"},
    {"role": "assistant", "content": "I'll create tests first.", "tool_calls": [
      {"id": "call_2", "function": {"name": "create_file", "arguments": "{\"path\": \"tests/test_user.py\", \"content\": \"import pytest\\nfrom user import User\\n\\ndef test_user_creation():\\n    user = User('Alice')\\n    assert user.name == 'Alice'\"}"}}
    ]},
    {"role": "tool", "content": "{\"status\": \"success\"}", "tool_call_id": "call_2"},
    {"role": "assistant", "content": "Tests created and verified."}
  ]
}
```

**Training**:

- Fine-tune agent model on 100-200 tool-use traces
- Use OpenAI's function calling format for compatibility
- Test extensively (agent should reliably call tools correctly)

---

## 7. RLHF (Reinforcement Learning from Human Feedback)

### 7.1 Overview

**Goal**: Optimize model based on user preferences (accepted vs rejected suggestions)

**Workflow**:

```text
1. Collect feedback: User accepts or rejects completions
2. Train reward model: Learn to predict which suggestions users prefer
3. Optimize policy: Use PPO (Proximal Policy Optimization) to maximize reward
4. Deploy updated model
5. Repeat
```

### 7.2 Feedback Collection

**Signals**:

- **Positive**: User accepts suggestion (presses Tab)
- **Negative**: User rejects (presses Esc or types different code)
- **Strong Positive**: User accepts + code passes tests
- **Strong Negative**: User reports issue (thumbs down button)

**Data Storage**:

```jsonl
{"prompt": "def add(a, b):", "completion": "\n    return a + b", "accepted": true, "test_result": "pass", "timestamp": "2026-02-23T10:00:00Z"}
{"prompt": "class User:", "completion": "\n    def __init__(self, name):\n        self.name = name", "accepted": false, "reason": "user_typed_different", "timestamp": "2026-02-23T10:05:00Z"}
```

### 7.3 Reward Model Training

**Architecture**: Small classifier (e.g., BERT-base or DistilBERT)

**Input**: Prompt + Completion
**Output**: Score (0.0 = bad, 1.0 = good)

**Training**:

```python
from transformers import AutoModelForSequenceClassification, Trainer

# Dataset: pairs of (prompt+completion, score)
# score = 1.0 if accepted, 0.0 if rejected
# score = 1.5 if accepted + tests passed (optional: multiple labels)

model = AutoModelForSequenceClassification.from_pretrained("bert-base-uncased", num_labels=1)

# Train with MSE loss (regression) or binary cross-entropy (classification)
```

**Dataset Size**: 10,000+ examples for reliable reward model

### 7.4 PPO (Proximal Policy Optimization)

**Goal**: Update model to maximize expected reward

**Libraries**:

- **TRL (Transformer Reinforcement Learning)**: HuggingFace library
- **DeepSpeed-Chat**: Microsoft's RLHF toolkit

**PPO Training**:

```python
from trl import PPOTrainer, PPOConfig
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("codellama/CodeLlama-7b-hf")
tokenizer = AutoTokenizer.from_pretrained("codellama/CodeLlama-7b-hf")

ppo_config = PPOConfig(
    model_name="codellama-ppo",
    learning_rate=1e-5,
    batch_size=64,
    mini_batch_size=4,
    ppo_epochs=4
)

ppo_trainer = PPOTrainer(
    model=model,
    config=ppo_config,
    tokenizer=tokenizer,
    dataset=rlhf_dataset,
    reward_model=reward_model
)

# Train for multiple epochs
for epoch in range(10):
    for batch in ppo_trainer.dataloader:
        query_tensors = batch['input_ids']

        # Generate completions
        response_tensors = ppo_trainer.generate(query_tensors, max_new_tokens=128)

        # Get rewards
        rewards = [reward_model(q, r) for q, r in zip(query_tensors, response_tensors)]

        # Update model
        stats = ppo_trainer.step(query_tensors, response_tensors, rewards)

    # Save checkpoint
    ppo_trainer.save_model(f"checkpoints/epoch-{epoch}")
```

**Hyperparameters**:

- Learning rate: 1e-6 to 1e-5 (smaller than SFT)
- PPO clip: 0.2
- KL penalty: 0.01 (prevent model from diverging too much from base)
- Batch size: 64-256

### 7.5 Safety Constraints

**Problem**: RLHF can lead to "reward hacking" (model games reward without being helpful)

**Solutions**:

1. **KL Divergence Penalty**: Penalize model for straying too far from base model
2. **Rule-Based Filters**: Reject completions with secrets, syntax errors, license violations
3. **Multi-Objective Reward**: Optimize for acceptance rate AND test pass rate AND safety

**Combined Reward**:

```python
def compute_reward(completion, context):
    reward = 0.0

    # User accepted?
    if completion['accepted']:
        reward += 1.0

    # Tests passed?
    if completion['test_result'] == 'pass':
        reward += 0.5

    # No secrets detected?
    if not contains_secrets(completion['text']):
        reward += 0.2
    else:
        reward -= 2.0  # Heavy penalty

    # Valid syntax?
    if is_valid_syntax(completion['text']):
        reward += 0.1
    else:
        reward -= 1.0

    return reward
```

---

## 8. Evaluation & Benchmarks

### 8.1 Internal Evaluation

**Metrics**:

- **Acceptance Rate**: % of suggestions accepted by users (target: >60%)
- **Test Pass Rate**: % of generated code that compiles and passes tests (target: >70%)
- **Latency**: P95 inference time (target: <500ms for fast model)
- **Hallucination Rate**: % of suggestions with invalid API usage (target: <10%)

**Evaluation Dataset**:

- Hold-out set from training data (10% of curated examples)
- Real user prompts from pilot phase
- Synthetic prompts covering edge cases

**Automated Tests**:

```python
def evaluate_model(model, eval_dataset):
    total = 0
    accepted = 0
    test_passed = 0

    for example in eval_dataset:
        prompt = example['prompt']
        expected_completion = example['completion']

        # Generate
        generated = model.generate(prompt, max_tokens=256)

        # Check acceptance (exact match or high similarity)
        similarity = compute_similarity(generated, expected_completion)
        if similarity > 0.8:
            accepted += 1

        # Check tests
        if run_tests(generated):
            test_passed += 1

        total += 1

    acceptance_rate = accepted / total
    test_pass_rate = test_passed / total

    return {'acceptance_rate': acceptance_rate, 'test_pass_rate': test_pass_rate}
```

### 8.2 Public Benchmarks

#### HumanEval (OpenAI)

- **Size**: 164 hand-written Python programming problems
- **Metric**: pass@k (% of problems solved with k attempts)
- **Baseline**: GPT-3.5-Turbo ~48%, GPT-4 ~67%, CodeLlama-7B ~30%

**Run Evaluation**:

```bash
# Clone HumanEval
git clone https://github.com/openai/human-eval

# Evaluate model
python evaluate.py --model codellama/CodeLlama-7b-hf --temperature 0.8 --k 10
```

#### MBPP (Mostly Basic Python Problems)

- **Size**: 974 Python problems
- **Difficulty**: Easier than HumanEval
- **Metric**: pass@k

#### MultiPL-E (Multi-Language)

- **Size**: HumanEval translated to 18 languages
- **Languages**: Python, JavaScript, Java, C++, Go, Rust, etc.
- **Use Case**: Test language-agnostic performance

### 8.3 Human Evaluation

**Method**: Have engineers rate suggestions (1-5 scale)

**Criteria**:

1. **Correctness**: Does the code work?
2. **Idiomatic**: Is it written in language-idiomatic style?
3. **Concise**: Is it unnecessarily verbose?
4. **Helpful**: Does it save time vs writing manually?

**Sample Size**: 100-200 prompts per evaluation round

**Frequency**: After each major model update (monthly)

---

## 9. Continuous Learning

### 9.1 Retraining Cadence

**Weekly Retraining** (Fast Model):

- **Data**: Last week's accepted suggestions (10,000-50,000 examples)
- **Method**: LoRA fine-tune (quick, cheap)
- **Duration**: ~6 hours
- **Deploy**: Canary test for 24 hours, then full rollout

**Monthly Retraining** (Agent Model):

- **Data**: Last month's accepted suggestions + RLHF feedback
- **Method**: Full fine-tune or large LoRA
- **Duration**: ~2-3 days
- **Deploy**: Extensive testing, then gradual rollout

### 9.2 A/B Testing

**Setup**:

- Serve two models simultaneously (old vs new)
- Route 10% of traffic to new model (canary)
- Compare metrics (acceptance rate, latency, errors)

**Decision Criteria**:

- If new model acceptance rate >5% higher: full rollout
- If new model acceptance rate <5% higher OR worse latency: rollback
- If inconclusive: expand canary to 50%, test for another week

**Implementation** (Kubernetes):

```yaml
apiVersion: v1
kind: Service
metadata:
  name: model-serving
spec:
  selector:
    app: model-serving
  ports:
  - port: 8000
---
# Stable model (90% traffic)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: model-serving-stable
spec:
  replicas: 9
  selector:
    matchLabels:
      app: model-serving
      version: stable
  template:
    metadata:
      labels:
        app: model-serving
        version: stable
    spec:
      containers:
      - name: vllm
        image: vllm/vllm-openai:v0.3.0
        args: ["--model", "codellama-v1.2"]
---
# Canary model (10% traffic)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: model-serving-canary
spec:
  replicas: 1
  selector:
    matchLabels:
      app: model-serving
      version: canary
  template:
    metadata:
      labels:
        app: model-serving
        version: canary
    spec:
      containers:
      - name: vllm
        image: vllm/vllm-openai:v0.3.0
        args: ["--model", "codellama-v1.3-new"]
```

### 9.3 Feedback Loop

```text
Users → Completions → Accept/Reject → Telemetry DB → Training Pipeline → New Model → Deploy → Users
```

**Automation**:

- Daily: Export accepted/rejected suggestions to S3
- Weekly: Trigger training pipeline (Airflow DAG)
- Weekly: Train new model, evaluate on hold-out set
- Weekly: Deploy to canary (if quality improved)
- Bi-weekly: Full rollout (if canary successful)

---

## 10. Data Governance & Ethics

### 10.1 Privacy

**GDPR Compliance**:

- **Consent**: Explicit opt-in for training on user code
- **Anonymization**: Strip author names, emails from training data
- **Right to Delete**: Remove user's data from training set (and retrain if necessary)
- **Data Minimization**: Use only necessary data (code, not comments with personal info)

**Implementation**:

```python
def anonymize_training_sample(sample: dict) -> dict:
    """Remove PII before training."""
    # Remove author metadata
    sample.pop('author', None)
    sample.pop('email', None)

    # Redact common PII patterns in code
    code = sample['code']
    code = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '<EMAIL>', code)
    code = re.sub(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', '<PHONE>', code)

    sample['code'] = code
    return sample
```

### 10.2 Bias & Fairness

**Risks**:

- Model trained mostly on English comments may perform worse for non-English developers
- Over-representation of certain languages (Python, JavaScript) vs under-representation (COBOL, Fortran)
- Biased towards popular frameworks (React, Django) vs niche ones

**Mitigation**:

- **Balanced Dataset**: Ensure all major languages represented (Python, JS, Java, Go, Rust, C++, etc.)
- **Internationalization**: Include code with non-English comments (German, Slovak, etc.)
- **Evaluation**: Test model on diverse set of languages and frameworks

### 10.3 Copyright & Licensing

**Training Data**:

- **Only Permissive Licenses**: MIT, Apache-2.0, BSD
- **No GPL/AGPL**: Viral licenses excluded to avoid copyright issues
- **Attribution**: Track provenance, display source if high similarity detected

**Generated Code**:

- **Disclaimer**: "Suggestions are AI-generated and may not be original. Review before using."
- **License Detection**: Warn user if generated code matches copyrighted code
- **No Warranty**: Not liable for copyright infringement by users (terms of service)

### 10.4 Ethical Use

**Prohibited Uses** (in Terms of Service):

- Generating malware, exploits, or harmful code
- Bypassing security systems
- Violating third-party intellectual property

**Enforcement**:

- **Content Filters**: Detect and block malicious code patterns
- **Abuse Detection**: Flag users with high rejection rate + suspicious patterns
- **Human Review**: Investigate flagged cases

---

## Summary

This training plan provides:

1. **Data Sources**: Public corpora (The Stack, GitHub), internal repos (opt-in), synthetic data, human curation
2. **Data Pipeline**: Ingestion (Airflow), filtering (PySpark), deduplication, tokenization
3. **Quality Control**: License checks, secret/PII detection, quality scoring, 40-50% pass rate
4. **Training Strategy**: Two-tier models (CodeLlama-7B + Mixtral-8x22B), LoRA fine-tuning, tool-use training
5. **RLHF**: Reward model, PPO optimization, safety constraints, multi-objective rewards
6. **Evaluation**: Internal metrics (acceptance rate, test pass rate), public benchmarks (HumanEval, MBPP), human eval
7. **Continuous Learning**: Weekly retraining (fast model), monthly retraining (agent model), A/B testing
8. **Data Governance**: GDPR compliance, bias mitigation, copyright protection, ethical use policies

**Key Success Factors**:

- **High-Quality Data**: Aggressive filtering (50% rejection rate) for best training data
- **User Feedback**: RLHF loop to continuously improve from real usage
- **Safety First**: Secret detection, license checks, and abuse prevention built-in
- **Transparency**: Clear disclosure of AI-generated code, attribution when needed

**Next Steps**:

1. Download The Stack dataset (permissive subset)
2. Set up data pipeline (Airflow + PySpark on EMR or Dataproc)
3. Run initial filtering and quality checks
4. Fine-tune CodeLlama-7B on filtered dataset
5. Evaluate on internal hold-out set and HumanEval
6. Deploy to staging for initial testing

**Dependencies**:

- [ARCHITECTURE.md](./ARCHITECTURE.md): System design
- [COMPONENTS.md](./COMPONENTS.md): Model serving infrastructure
- [SECURITY.md](./SECURITY.md): Secret detection, privacy controls
- [ROADMAP.md](./ROADMAP.md): Training milestones (Month 5: RLHF loop)

---

**Document Version**: 1.0
**Last Updated**: February 23, 2026
**Owner**: Slovakia Engineering Team / ML Team
**Review Cycle**: Monthly or after major training runs
