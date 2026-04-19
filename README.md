# batchmark

A CLI tool for benchmarking batches of shell commands with statistical summaries.

## Installation

```bash
pip install batchmark
```

Or install from source:

```bash
git clone https://github.com/yourname/batchmark.git && cd batchmark && pip install .
```

## Usage

Run a batch of commands and get timing statistics:

```bash
batchmark run --runs 10 "sleep 0.1" "echo hello" "ls -la"
```

**Example output:**

```
Command          Runs   Mean (s)   Median (s)   Std Dev   Min (s)   Max (s)
---------------------------------------------------------------------------
sleep 0.1        10     0.1023     0.1021       0.0004    0.1017    0.1031
echo hello       10     0.0021     0.0020       0.0003    0.0018    0.0028
ls -la           10     0.0045     0.0044       0.0005    0.0039    0.0057
```

You can also load commands from a file:

```bash
batchmark run --runs 5 --file commands.txt
```

### Options

| Flag | Description |
|------|-------------|
| `--runs N` | Number of times to run each command (default: 10) |
| `--file FILE` | Load commands from a newline-separated file |
| `--output csv` | Export results to CSV format |
| `--warmup N` | Number of warmup runs before measuring |

## License

MIT