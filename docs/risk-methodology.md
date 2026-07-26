# Middle East Geopolitical Intelligence Platform — Risk Methodology Guide

This document defines the mathematical models, indicator normalizations, and scoring rules used by the platform's Risk Engine.

---

## 1. Core Risk Principles

1. **Separation of Risk Categories**: The platform avoids a single generic "geopolitical risk" number. Instead, it tracks 12 explicit categories (e.g., `interstate_war`, `civil_conflict`, `maritime_disruption`, `energy_disruption`, `nuclear_escalation`).
2. **Deterministic Base Score**: Base risk scores are derived strictly from weighted, observable indicators to ensure transparency, auditability, and reproducibility.
3. **Bounded LLM Adjustment**: Large language models may recommend contextual adjustments bounded within `[-10, +10]` points. The base score, LLM recommendation, and final score are stored separately.
4. **Counter-Indicators & Confidence**: Every assessment includes explicit counter-indicators and an overall confidence score based on indicator freshness and data quality.

---

## 2. Risk Calculation Formula

For a given risk category $R$ and scope $S$:

$$\text{BaseScore}(R, S) = \sum_{i=1}^{n} w_i \times \text{NormalizedValue}(I_i, S)$$

Where:
- $w_i$ is the weight assigned to indicator $I_i$ ($\sum w_i = 100$).
- $\text{NormalizedValue}(I_i, S) \in [0, 100]$ is the normalized intensity score of indicator $I_i$.

The final score is:

$$\text{FinalScore}(R, S) = \text{Clamp}\Big(\text{BaseScore}(R, S) + \Delta_{\text{LLM}}, \, 0, \, 100\Big)$$

Where $\Delta_{\text{LLM}} \in [-10, +10]$ is validated and clamped by the deterministic engine.

---

## 3. Core Indicators & Weighting Example (Interstate War Risk)

| Indicator Code | Indicator Name | Weight | Primary Data Source |
|---|---|---|---|
| `IND_DIRECT_ATTACKS` | Direct cross-border military exchanges | 20% | Verified military event records |
| `IND_FORCE_MOBILIZATION` | Troop/asset mobilization & deployment | 15% | Intelligence reports & imagery |
| `IND_STRATEGIC_ATTACKS` | Strikes on high-value infrastructure | 15% | Event impact records |
| `IND_ESCALATION_RHETORIC` | Direct threats of war / declaration | 10% | Official claims & speeches |
| `IND_ALLIANCE_ACTIVATION` | Formal defense pact activation | 10% | Diplomatic announcements |
| `IND_DIPLOMATIC_BREAKDOWN` | Recall of ambassadors / channel closure | 10% | Relationship observations |
| `IND_CIVILIAN_IMPACT` | Casualty scale & mass evacuations | 10% | Humanitarian data |
| `IND_GEOGRAPHIC_SPREAD` | Multi-front expansion of kinetic actions | 10% | Spatial event clustering |

---

## 4. Score Change Explanation Structure

Every risk update produces a structured explanation object:

```json
{
  "risk_code": "interstate_war",
  "scope_id": "actor-iran-israel",
  "base_score": 72,
  "llm_adjustment": 3,
  "final_score": 75,
  "previous_score": 68,
  "trend": "escalating",
  "confidence": 0.85,
  "changed_indicators": [
    "IND_DIRECT_ATTACKS (+15%)",
    "IND_STRATEGIC_ATTACKS (+10%)"
  ],
  "counter_indicators": [
    "Backchannel diplomatic contacts remain active in Oman."
  ],
  "explanation": "Score increased due to verified direct missile exchanges targeting military infrastructure, partially offset by ongoing backchannel diplomatic messaging."
}
```
