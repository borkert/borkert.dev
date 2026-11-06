# A small classifier in Rust and Metal

*By Chris Borkert · November 2026*

I’m building minimodels: a small email classifier and a training engine in Rust, with custom Metal kernels for Apple Silicon. The goal is to replace a larger classifier without giving up accuracy. So far, speed is ahead of accuracy.

The current model has 3.35 million parameters, four encoder layers, and a 512-token limit. The engine handles differentiation and AdamW directly, without a tensor framework. The saved weights occupy 13.42 MB.

The interesting result came from changing the runtime around the model. Reusing GPU buffers, keeping a compute encoder open across dispatches, and changing the matrix multiplication and reduction kernels brought warm inference from **2.465 to 0.630 ms per email** on an Apple M5. Those are medians of five run means, each over the same 256 validation emails. Tokenization and loading are excluded.[^1]

That is a combined change, so I can’t assign the improvement to one optimization. Full validation accuracy stayed at **72.45% across 3,982 emails**. Independent CPU reference checks agreed within 1.43e-6 logits at sequence lengths 1, 17, and 512.[^1]

The replacement check was less encouraging. Against the shipped classifier, the small model scored **71.62% versus 88.05%** on the same 3,982 email identities. Urgent-email recall was **37.10% versus 81.45%**. This was a practical regression screen: the shipped model may have historical training overlap, so those numbers do not establish a clean generalization comparison.[^2]

The engine is fast enough to keep exploring. The checkpoint still misses too many urgent messages to replace the existing classifier.

## References

[^1]: Local experiment records, November 2026: `runs/engine-check-v1/results.json` and `README-handoff.md` in minimodels. Warm, synchronized, batch-one inference; unchanged checkpoint. Records are not yet published.
[^2]: Local replacement assessment: `runs/dart-feasibility-v1/REPORT.md`. The comparison used the shipped DART model and the custom checkpoint on Apple M5 Ultra, with each model’s own tokenizer and context limit. Records are not yet published.
