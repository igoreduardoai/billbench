# BillBench: one-command targets (Python 3.10+, standard library only)
test:
	python3 -m unittest discover -s tests -t .
dry:
	python3 -m billbench.run --dry
tasks:
	python3 -m billbench.dump_tasks > docs/TASKS.md
report:
	python3 -m billbench.report results/final
# Needs NEBIUS_API_KEY (Nebius Token Factory). Every call is logged to results/spend-log.csv.
run:
	python3 -m billbench.run --suite all --repeats 3 --budget 14 --models deepseek-ai/DeepSeek-V4-Pro moonshotai/Kimi-K3 zai-org/GLM-5.3 Qwen/Qwen3.5-397B-A17B nvidia/Nemotron-3-Ultra-550b-a55b
# Needs OPENROUTER_API_KEY with credits. Example for closed frontier models:
run-openrouter:
	python3 -m billbench.run --provider openrouter --suite expert --repeats 3 --budget 14 --models openai/gpt-6.1-sol anthropic/claude-opus-5.5 google/gemini-4-argon
