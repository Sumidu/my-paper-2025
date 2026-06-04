---
research_question: "How can agentic AI systems in complex industrial environments be designed to maintain operator situation awareness — through shared domain terminology, explainable agent behaviour, and reflective multi-agent architectures — and what does this demand from future HCI and safety research?"
keywords:
  - situation awareness
  - agentic AI
  - explainability
  - domain-driven shared terminology
  - reflective multi-agent systems
  - human-AI teaming
  - industrial process monitoring
---

## Summary

As agentic AI systems take on increasingly autonomous roles in complex sociotechnical environments — such as predictive maintenance in chemical process plants — a critical challenge emerges: operators may lose meaningful oversight of what the system is doing, why it is doing it, and when it fails to act. This is fundamentally a situation awareness problem. Unlike classical automation, agentic AI behaves more like a semi-autonomous colleague than a deterministic tool, making it harder for operators to build and sustain accurate mental models. The paper positions this as an under-examined frontier at the intersection of HCI, safety, and agentic AI research.

The proposed architecture addresses three interlinked mechanisms. First, a domain-driven shared terminology layer establishes a common conceptual language between the agent and its operators — analogous to domain-specific languages in software engineering — which can also serve as a basis for personalisation across different operator roles and expertise levels. Second, the system should provide transparent, operator-legible explanations of which events were detected or missed and why, grounding explainability in the operator's own vocabulary. Third, a reflective sub-agent layer runs in parallel to the primary agent, continuously monitoring for overlooked cases, past failures, and performance drift — providing a mechanism for ongoing, autonomous self-improvement while keeping humans informed of the system's epistemic limits.

This is presented as a vision and design proposal rather than an empirical result. The contribution is a conceptual architecture that frames situation awareness in agentic AI as a first-class design challenge and offers a structured research agenda for the HCI and safety communities.

## Anticipated Topics

- [[situation-awareness]] — Endsley's three-level model (perception, comprehension, projection) in automated systems
- [[human-ai-teaming]] — trust calibration, appropriate reliance, and supervisory control
- [[agentic-ai]] — LLM-based agents, tool use, multi-step autonomy
- [[explainability-xai]] — post-hoc and intrinsic explainability for autonomous agents
- [[domain-driven-design]] — shared language, ubiquitous language, domain-specific models
- [[personalization]] — user-adaptive systems, operator profiling, role-based communication
- [[reflective-agents]] — self-monitoring, meta-cognition in AI, multi-agent critique loops
- [[predictive-maintenance]] — industrial use case grounding, data stream analysis, anomaly detection
- [[process-control-hci]] — SCADA interfaces, operator workload, alarm management
- [[automation-complacency]] — overtrust, skill degradation, out-of-the-loop syndrome

## Open Questions

- How do existing situation awareness frameworks (Endsley, SAGAT) need to be extended to account for agent opacity and non-determinism?
- What existing work has addressed shared terminology or ontology alignment between AI agents and human operators in industrial settings?
- Are there precedents in CSCW or CSAI for reflective/self-monitoring multi-agent loops that feed back into operator awareness?
- How does personalisation of agent communication interact with safety-critical standardisation requirements (e.g. IEC 62682 alarm management)?
- What empirical methods are appropriate for evaluating situation awareness with agentic AI — simulation studies, field studies, think-aloud protocols?
- Is there a tension between making agents more explainable and making them more autonomous/capable, and how has this been addressed?
