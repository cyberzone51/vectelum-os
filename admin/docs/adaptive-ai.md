# VECTELUM Adaptive AI (developer preview)

Local AI requests now automatically select a conservative hardware profile using the Linux/WSL memory limit, CPU parallelism and Ollama-reported GPU VRAM. Remote model endpoints keep their existing behavior.

| Profile | Context ceiling | Output ceiling | Retrieval candidates | Embedding batch |
|---|---:|---:|---:|---:|
| Low | 4096 | 384 | 3 | 1 |
| Balanced | 8192 | 1024 | 6 | 4 |
| Performance | 32768 | 4096 | 12 | up to 8 |

Low is selected for less than 16 GiB effective RAM or CPU-only/low-VRAM hosts with at most four available CPU threads. Performance requires at least 16 GiB RAM and 8 GiB detected VRAM; otherwise Balanced applies. The existing model-specific context budget can further reduce these limits. Low and CPU-only Balanced skip the extra LLM query-rewrite, relevance-check and automatic title generation calls. Low keeps the selected chat model resident for two minutes, suppresses default (not explicit) thinking, and recommends smaller installed chat models when selected model weights exceed its conservative memory budget (30% of RAM, capped at 3 GiB). It does not silently change the selected model or delete any model.

The background document embedding worker yields between single-chunk batches while a Low profile chat is active, with a bounded wait of 120 seconds per batch. In-flight embeddings are not interrupted. This is cooperative pacing, not a strict scheduler, and does not eliminate every timeout. It can reduce indexing speed and retrieval quality; output may be truncated at the token cap. Hardware detection is cached briefly. Actual performance depends on models, concurrent services and available RAM.

Unit tests cover profile decisions, model recommendations and priority lease release. Full clean-install and cross-platform performance validation are still required.
