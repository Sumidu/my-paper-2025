---
generated: 2026-06-04
sources: 49 papers, 4 topics
---

# State of the Art: How can agentic AI systems in complex industrial environments be designed to maintain operator situation awareness — through shared domain terminology, explainable agent behaviour, and reflective multi-agent architectures — and what does this demand from future HCI and safety research?

## Overview

The rapid deployment of AI in safety-critical and industrial environments has forced a reconceptualisation of the human role from active controller to supervisory overseer — a transition with well-documented hazards for situation awareness (SA). Foundational work by Endsley established that SA in automated systems requires not only correct perception of the environment but also comprehension of its meaning and projection of future states [@endsley2023supporting]. As AI autonomy increases, the cognitive burden shifts from doing to monitoring, and from knowing to inferring — making SA simultaneously more important and harder to sustain. Parallel research streams in human-AI teaming (HAIT) have formalised this challenge, finding that mixed human-AI teams outperform human-only teams on measurable task metrics while frequently scoring lower on perceived team cognition [@mcneese2021who], a divergence that signals an emerging gap between objective performance and operator understanding.

Against this backdrop, the emergence of agentic AI — systems that autonomously perceive, reason, plan, and act over extended horizons with minimal human intervention [@acharya2025agentic; @bandi2025rise] — introduces qualitatively new challenges. Unlike classical decision support, agentic systems exhibit non-deterministic, context-sensitive behaviour that cannot be fully anticipated or easily audited. Research on HAIT has begun to address these challenges through frameworks for trust, transparency, and task allocation [@unknown2022human; @berretta2023defining], and through domain-specific deployment studies in aviation, healthcare, and cybersecurity. However, the specific intersection of agentic AI, operator SA, and industrial process monitoring remains largely uncharted, with no established architecture that addresses shared domain terminology, operator-legible explanations, and reflective self-monitoring as an integrated design challenge.

The existing literature converges on three partially overlapping frontiers: the SA requirements of human-AI teams, the design of explainability for high-autonomy systems, and the architectural properties of agentic and multi-agent systems. Each frontier has generated substantial insight, yet their synthesis into a coherent design vision for industrial agentic AI is missing. This state-of-the-art review maps those three frontiers and identifies the gap this paper addresses.

---

## Situation Awareness as the Core Challenge of Human-AI Teams

The centrality of SA to safe human-AI collaboration has been established across multiple high-stakes domains. Endsley's SA Oriented Design (SAOD) methodology provides a systematic process for identifying the information an AI agent needs to share with human teammates, decomposing it into taskwork SA, agent SA, and teamwork SA — and distinguishing the separate roles that transparency and explainability play in supporting mental models versus real-time awareness [@endsley2023supporting]. Empirical work has confirmed that communication behaviours — particularly anticipatory information pushing, transparency, and explainability — reliably improve team SA and trust outcomes in human-AI teams [@duan2023communication]. Similarly, studies of AI information-sharing tactics find that updates about intra- and extra-team state changes benefit trust and SA more than task-level performance metrics alone [@schelble2025examining].

The relationship between agent autonomy and operator SA is not monotonic. As AI takes on more cognitive work, operators risk transitioning from active engagement to passive monitoring, with associated losses in skill and situational acuity — a pattern extensively documented as automation complacency [@boy2024human; @hagemann2023human]. Hagemann et al. frame this as a team-centred design problem: for AI to function as a genuine teammate, it must maintain semantic communication, share situational models, and adapt its outputs to the operator's current cognitive state [@hagemann2023human]. Reinforcement-learning approaches have been proposed to automate the maintenance of SA model parameters in decision support systems, offering a path toward adaptive explainability [@costa2025reinforcement]. Research in automated vehicle interfaces further demonstrates that augmented-reality visualisations tied to AI decision rationale can significantly improve both user experience and SA scores in automated contexts [@manger2023explainability; @yang2018self].

Despite this progress, existing SA frameworks were designed for classical automation and do not account for the opacity, non-determinism, and goal-directedness of agentic AI. The question of how Endsley's three SA levels apply when the agent can autonomously redefine its goals, delegate subtasks to other agents, or learn from operational feedback has not been formally addressed.

---

## Human-AI Teaming: Frameworks, Trust, and Safety-Critical Design

The human-AI teaming literature has matured substantially over the past five years, producing frameworks, taxonomies, and empirical findings across a range of domains. Berretta et al.'s scoping review and network analysis identifies five research clusters in HAIT — human variables, task variables, AI explainability, robotic systems, and AI performance effects — while noting the absence of a shared definition and a persistent technology-centric bias in the field [@berretta2023defining]. The National Academies' state-of-the-art report reinforces this fragmentation, identifying brittleness, hidden bias, and limited causal reasoning as near-term blockers for effective HAT in complex environments [@unknown2022human].

Design-oriented work has responded with frameworks for structuring human-AI collaboration. The HACO framework extends multi-agent architectures to support model-driven development of HAIT systems [@dubey2020haco], while Caldwell et al.'s agile research framework proposes a structured pathway for testing HAIT concepts in safe experimental environments before transfer to real-world contexts [@caldwell2022agile]. Bienefeld et al.'s Delphi study in intensive care units finds that clinicians and data scientists converge on human-augmented-AI designs for most tasks, with interpretability, predictability, and operator control as the decisive criteria [@bienefeld2024human]. The A2C framework for security operations centres similarly proposes fluid transitions between automated, augmented, and collaborative modes — allowing operators to dynamically reclaim oversight as threat complexity increases [@chhetri2024human].

Aviation has emerged as the leading domain for operationalising HAIT safety requirements. Kirwan and colleagues have developed detailed human factors requirement sets for AI-based intelligent agents in cockpit and ATC contexts [@kirwan2025human; @kirwan2024human], while Venditti et al. apply Construal Level Theory to design explainability interfaces that deliver information at the right level of abstraction for the operator's current cognitive context [@venditti2025construal]. The concept of Operational Design Domains — borrowed from automotive safety — has been applied to constrain AI autonomy within bounded, validated operational envelopes in ATC [@stefani2024operational]. Cohen et al. identify teamness and trust as emergent cognitive properties of human-AI interaction that existing evaluation methods do not adequately capture [@cohen2023teamness], while Zhang et al.'s survey of player expectations for AI teammates highlights shared situational understanding and adaptive communication as the most valued properties [@zhang2021ideal].

Across this literature, key gaps for the industrial agentic AI case are apparent: most frameworks assume stable, relatively bounded task domains; few address the personalisation of agent communication to individual operators; and none propose mechanisms for agents to monitor their own performance drift and feed that awareness back to human supervisors.

---

## Agentic AI: Architectures, Autonomy, and Multi-Agent Coordination

The agentic AI literature has undergone rapid expansion, driven by advances in large language models and their integration into autonomous tool-using systems. Taxonomic reviews distinguish AI agents — modular LLM-based systems for task-specific automation — from agentic AI, which adds persistent memory, dynamic task decomposition, multi-agent collaboration, and coordinated autonomy [@sapkota2026ai; @nisa2026agentic]. Bandi et al. provide a comprehensive architecture review covering planning, memory, reflection, and goal pursuit, noting that evaluation metrics for agentic systems remain underdeveloped [@bandi2025rise]. Acharya et al.'s IEEE Access survey frames agentic AI as a sociotechnical deployment challenge as much as a technical one, emphasising goal alignment, resource constraints, and ethical governance [@acharya2025agentic].

Application-domain surveys have documented deployments across healthcare [@sharma2026reimagining], manufacturing [@ren2025ai; @mendonca2026human], oil and gas [@jessen2025agentic], cybersecurity [@kshetri2025transforming], and 6G network operations [@cimen2025integration; @zhang2026edge]. The ENERGYai platform — ADNOC's large-scale agentic AI deployment across upstream, midstream, and downstream O&G operations — is a notable real-world case, combining domain-specific intelligence with LLM reasoning for seismic interpretation, production forecasting, and process monitoring, while identifying data quality, QA/QC protocols, and trust and explainability as the primary unresolved challenges [@jessen2025agentic]. Mendonça et al. propose a digital twin-based architecture for predictive maintenance that integrates explainable AI, agentic orchestration, and continuous operator feedback — the closest existing work to the architecture proposed in this paper — but focuses on a single-agent system without a reflective monitoring layer or personalisation mechanism [@mendonca2026human].

Multi-agent coordination has been benchmarked in challenging synthetic environments: CREW-Wildfire tests LLM-based multi-agent frameworks on large-scale wildfire response scenarios with partial observability and long-horizon planning, exposing significant gaps in coordination, spatial reasoning, and communication [@hyun2025crew]. Portugal et al.'s recommender-system framework and Kumar et al.'s MCP server implementation demonstrate the practical complexity of multi-agent orchestration even in lower-stakes domains [@portugal2024agentic; @kumar2025comprehensive]. The broader agentic AI literature consistently identifies opaque decision-making, limited human oversight, and coordination failure as the most critical open challenges [@brohi2025research; @chahar2025agentic; @pati2025agentic; @olujimi2025agentic; @hosseini2025role].

---

## Explainability and Transparency in High-Stakes Agentic Systems

Explainability has been a central concern of the HAIT literature, but its treatment has been largely confined to post-hoc explanation of individual model outputs rather than the ongoing, context-sensitive disclosure that agentic autonomy demands. Radanliev's transparency-by-design framework argues that agentic architectures require safety mechanisms beyond algorithmic audits: specifically, traceable decision provenance, runtime behavioural observability, and forensic audit trails implemented at the architectural level [@radanliev2026transparent]. Raza et al.'s TRiSM review proposes explainability as one of four governance pillars for LLM-based multi-agent systems, alongside security, privacy, and ModelOps lifecycle governance [@raza2026trism].

Domain deployments corroborate the urgency. In aviation, Venditti et al.'s CLT-based interface design delivers structured explanations at multiple levels of abstraction, enabling air traffic controllers to progressively query an AI assistant's reasoning without disrupting workflow [@venditti2025construal]. Ahmed et al.'s remote digital tower study identifies human-centred XAI and human-machine interface customisation as the critical design requirements for AI-assisted ATC, emphasising that explainability must be tailored to operator roles and operational context [@ahmed2025role]. In healthcare, Sharma et al. flag explainability as a first-order risk factor for agentic AI in psychiatry, where the therapeutic alliance depends on clinicians understanding and trusting AI reasoning [@sharma2026reimagining]. Khun's analysis of autonomous vehicles similarly argues that progressive disclosure and transparent interfaces are essential preconditions for adoption, independent of technical capability [@khun2026human].

Critically, existing work treats explainability as a display design problem — how to show reasoning to operators — rather than as a shared language problem. The notion that the agent and operator might need to co-construct a domain-specific conceptual vocabulary, which then becomes the medium through which explanations are generated and interpreted, is absent from the literature. Samadi et al. come closest in the flood evacuation context, calling for the integration of different types of human knowledge — including citizen knowledge and stakeholder vocabularies — into AI system design [@samadi2024challenges], but do not extend this to agentic architectures or personalisation.

---

## Research Gaps

The existing literature has established strong foundations for SA in automated systems, HAIT design across multiple domains, and the architectural properties of agentic AI. However, it has not addressed the combination of challenges that arises when agentic AI operates as an autonomous colleague in complex industrial process environments. Three gaps are directly relevant to the contribution of this paper. First, no existing SA framework or HAIT design methodology has been adapted for agentic AI's non-determinism and self-modifying behaviour: Endsley's model, Kirwan's HF requirements, and the aviation ODD concept all assume bounded, specifiable automation behaviour. Second, the literature on explainability treats operator comprehension as a display design problem, ignoring the possibility that operators and agents might need a shared domain vocabulary — a form of terminological grounding analogous to domain-driven design in software engineering — as the basis for both explanation and personalisation. Third, while reflective and self-monitoring architectures are discussed in abstract terms in agentic AI surveys [@brohi2025research; @raza2026trism; @radanliev2026transparent], no concrete architectural proposal exists for parallel sub-agents that continuously monitor primary agent performance, detect overlooked events, and communicate epistemic limits back to operators in a human-legible form. The present paper addresses this three-part gap through a design architecture that integrates shared terminology, operator-adaptive explanations, and reflective multi-agent oversight as a coherent response to the SA challenge posed by agentic AI in industrial environments.

---

## References

- [@acharya2025agentic] Acharya D.B. et al. (2025) — Agentic AI: Autonomous Intelligence for Complex Goals - A Comprehensive Survey.
- [@ahmed2025role] Ahmed M.U. et al. (2025) — Role of Multi-modal Machine Learning, Explainable AI and Human-AI Teaming in Trusted Intelligent Systems for Remote Digital Towers.
- [@attig2024more] Attig C. et al. (2024) — More than Task Performance: Developing New Criteria for Successful Human-AI Teaming Using the Cooperative Card Game Hanabi.
- [@bandi2025rise] Bandi A. et al. (2025) — The Rise of Agentic AI: A Review of Definitions, Frameworks, Architectures, Applications, Evaluation Metrics, and Challenges.
- [@berretta2023defining] Berretta S. et al. (2023) — Defining human-AI teaming the human-centered way: a scoping review and network analysis.
- [@bienefeld2024human] Bienefeld N. et al. (2024) — Human-AI Teaming in Critical Care: A Comparative Analysis of Data Scientists' and Clinicians' Perspectives on AI Augmentation and Automation.
- [@boy2024human] Boy G.A. (2024) — Human Systems Integration of Human-AI Teaming.
- [@brohi2025research] Brohi S. et al. (2025) — A Research Landscape of Agentic AI and Large Language Models: Applications, Challenges and Future Directions.
- [@caldwell2022agile] Caldwell S. et al. (2022) — An Agile New Research Framework for Hybrid Human-AI Teaming: Trust, Transparency, and Transferability.
- [@chahar2025agentic] Chahar S. et al. (2025) — Agentic AI: A Paradigm Shift in Autonomous Decision-Making and Intelligent Systems.
- [@chhetri2024human] Chhetri M.B. et al. (2024) — Towards Human-AI Teaming to Mitigate Alert Fatigue in Security Operations Centres.
- [@cimen2025integration] Cimen S. et al. (2025) — The Integration of Agentic AI in 6G Wireless Networks: State-of-the-Art, Challenges, and Future Perspectives.
- [@cohen2023teamness] Cohen M.C. et al. (2023) — Teamness and Trust in AI-Enabled Decision Support Systems: Current Challenges and Future Directions.
- [@costa2025reinforcement] Costa R.D. et al. (2025) — Reinforcement learning applied to a situation awareness decision-making model.
- [@dubey2020haco] Dubey A. et al. (2020) — HACO: A Framework for Developing Human-AI Teaming.
- [@duan2023communication] Duan W. et al. (2023) — Communication in Human-AI Teaming.
- [@hagemann2023human] Hagemann V. et al. (2023) — Human-AI teams—Challenges for a team-centered AI at work.
- [@haindl2022reference] Haindl P. et al. (2022) — Towards a Reference Software Architecture for Human-AI Teaming in Smart Manufacturing.
- [@hosseini2025role] Hosseini S. et al. (2025) — The role of agentic AI in shaping a smart future: A systematic review.
- [@hyun2025crew] Hyun J. et al. (2025) — CREW-Wildfire: Benchmarking Agentic Multi-Agent Collaborations at Scale.
- [@jessen2025agentic] Jessen H. et al. (2025) — Agentic AI Revolution Across O&G Value Streams: New Strategy Through ENERGYai Examples.
- [@khun2026human] Khun J.L. (2026) — Human Interaction Influences the Adoption of Robotics and Autonomous Agentic AI Systems.
- [@kirwan2024human] Kirwan B. et al. (2024) — A Human Centric Design Approach for Future Human-AI Teaming in Aviation.
- [@kirwan2025human] Kirwan B. (2025) — Human Factors Requirements for Human-AI Teaming in Aviation.
- [@kshetri2025transforming] Kshetri N. (2025) — Transforming cybersecurity with agentic AI to combat emerging cyber threats.
- [@kumar2025comprehensive] Kumar N. et al. (2025) — A Comprehensive Study and Implementation of Agentic AI via MCP Servers.
- [@manger2023explainability] Manger C. et al. (2023) — Explainability in Automated Parking: The Effect of Augmented Reality Visualizations on User Experience and Situation Awareness.
- [@mcneese2021who] McNeese N.J. et al. (2021) — Who/What Is My Teammate? Team Composition Considerations in Human-AI Teaming.
- [@mendonca2026human] Mendonça L. et al. (2026) — A Human-Centred Architecture Integrating Digital Twin and Agentic AI for Predictive Maintenance.
- [@nisa2026agentic] Nisa U. et al. (2026) — Agentic AI: The age of reasoning—A review.
- [@olujimi2025agentic] Olujimi P.A. et al. (2025) — Agentic AI Frameworks in SMMEs: A Systematic Literature Review of Ecosystemic Interconnected Agents.
- [@pati2025agentic] Pati A.K. (2025) — Agentic AI: A Comprehensive Survey of Technologies, Applications, and Societal Implications.
- [@portugal2024agentic] Portugal I.D.S. et al. (2024) — An Agentic AI-based Multi-Agent Framework for Recommender Systems.
- [@radanliev2026transparent] Radanliev P. (2026) — Transparent by Design: Ensuring Safety in Agentic AI Through Decision Traceability.
- [@raza2026trism] Raza S. et al. (2026) — TRiSM for Agentic AI: A review of Trust, Risk, and Security Management in LLM-based Agentic Multi-Agent Systems.
- [@ren2025ai] Ren Y. et al. (2025) — AI Agents and Agentic AI–navigating a plethora of concepts for future manufacturing.
- [@samadi2024challenges] Samadi V. et al. (2024) — Challenges and opportunities when bringing machines onto the team: Human-AI teaming and flood evacuation decisions.
- [@sapkota2026ai] Sapkota R. et al. (2026) — AI Agents vs. Agentic AI: A Conceptual taxonomy, applications and challenges.
- [@schelble2025examining] Schelble B.G. et al. (2025) — Examining the Role of AI Information-Sharing on Trust in Human-AI Teams.
- [@sharma2026reimagining] Sharma D. et al. (2026) — Reimagining psychiatric care with agentic AI: promise, challenges, and a roadmap forward.
- [@simon2024integrating] Simón C. et al. (2024) — Integrating AI in organizations for value creation through Human-AI teaming: A dynamic-capabilities approach.
- [@stefani2024operational] Stefani T. et al. (2024) — Towards an Operational Design Domain for Safe Human-AI Teaming in the Field of AI-Based Air Traffic Controller Operations.
- [@unknown2022human] Unknown (2022) — Human-AI Teaming: State-of-the-Art and Research Needs.
- [@venditti2025construal] Venditti R. et al. (2025) — Construal Level Theory (CLT) for Designing Operational Explainability for Human-AI Teaming Interfaces in Aviation Contexts.
- [@xu2024applying] Xu W. et al. (2024) — Applying HCAI in Developing Effective Human-AI Teaming: A Perspective from Human-AI Joint Cognitive Systems.
- [@yang2018self] Yang Y. et al. (2018) — The self-explainability of demand-oriented road improvement.
- [@zhang2021ideal] Zhang R. et al. (2021) — "An Ideal Human": Expectations of AI Teammates in Human-AI Teaming.
- [@zhang2026edge] Zhang R. et al. (2026) — Toward Edge General Intelligence With Agentic AI and Agentification: Concepts, Technologies, and Future Directions.
