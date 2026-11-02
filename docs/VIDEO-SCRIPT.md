# BillBench video walkthrough (target 2:30, screen only, no face)
On-screen label + description: "Narration: Igor's own voice, cloned with ElevenLabs".

0:00-0:15  Hook. Show the x13 card: "A DME supplier that doesn't accept assignment. 15 runs on frontier models: 3 right. 7 told the patient $31.50; the real cost is $68.00."
0:15-0:40  Why it matters: patients paste bills into chatbots, billing teams use AI on calls; most of the money is in a few federal rules.
0:40-1:10  Design: Core (rules stated) vs Expert (rule not explained); engine + hand-checked tests; strict FINAL: $X.XX grader; named mistakes. Run `make test` (12 OK).
1:10-1:50  Results: scoreboard table, 78% vs 95%; per model; failure-mode table (limiting charge on DME, discharge day counted, Part A deductible per year, NSA out-of-network coinsurance).
1:50-2:15  Reproduce: `make dry`, `make run` (spend log, budget guard), `make report`.
2:15-2:30  Limits: open-weight models only (no closed models run yet), piloted then locked, synthetic data, not advice. Close on the repo name.
