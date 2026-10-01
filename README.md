# agentic-data-engineering

Portfolio of AI agents for modern data engineering, with a focus on Data Pipelines, Data Quality, Automation, and Production-Ready Agentic systems. Each numbered project builds on the one before it, moving from the fundamentals of LLM tool calling up to a full, production-style agent.

## Projects

| # | Project | Status |
|---|---------|--------|
| 01 | [LLM Tool Calling](01-llm-tool-calling/) | In progress |
| 02 | [Snowflake Agent](02-snowflake-agent/) | Planned |
| 03 | [Data Quality Agent](03-data-quality-agent/) | Planned |
| 04 | [Pipeline Investigator](04-pipeline-investigator/) | Planned |
| 05 | [Schema Change Agent](05-schema-change-agent/) | Planned |
| 06 | [AWS Agent](06-aws-agent/) | Planned |
| 07 | [Autonomous Remediation](07-autonomous-remidation/) | Planned |
| 08 | [Capstone](08-capstone/) | Planned |

### 01 · [LLM Tool Calling](01-llm-tool-calling/)

A hands-on exploration of LLM tool calling (function calling) using AWS Bedrock as the model provider: giving an LLM a set of Python functions, letting it decide when to call them, executing the calls, and feeding results back for a final answer.

**Why:** this is the foundational pattern — the agent loop — that every later project in this portfolio builds on. Getting it right here first means the rest of the projects can focus on their own domain logic instead of re-deriving tool calling from scratch.

### 02 · [Snowflake Agent](02-snowflake-agent/)

An agent that uses tool calling to interact with a Snowflake warehouse — inspecting schemas, running queries, and answering natural-language questions about the data it finds.

**Why:** applies the project 01 agent loop to a real, widely-used data warehouse, moving from toy tools to tools that touch production-shaped data infrastructure.

### 03 · [Data Quality Agent](03-data-quality-agent/)

An agent that checks data for quality issues — nulls, duplicates, schema drift, anomalies — and reports or flags what it finds.

**Why:** data quality monitoring is traditionally a set of brittle, hand-written rules; an agent that can reason about what "looks wrong" generalises better and needs less upkeep as data shapes change.

### 04 · [Pipeline Investigator](04-pipeline-investigator/)

An agent that triages failing or misbehaving data pipelines — reading logs, correlating failures, and proposing a root cause.

**Why:** pipeline triage is usually manual, slow, and relies on tribal knowledge of "where to look first"; an agent can encode that investigative process and run it the moment something breaks.

### 05 · [Schema Change Agent](05-schema-change-agent/)

An agent that detects schema changes across systems and assesses their downstream impact before they break something.

**Why:** schema drift is one of the most common causes of silent pipeline failures; catching it proactively (rather than discovering it from a broken dashboard) is a high-leverage use of an agent's ability to reason over structured metadata.

### 06 · [AWS Agent](06-aws-agent/)

A broader agent for operating across AWS data services (beyond just Bedrock) — e.g. S3, Glue, Athena — as tools.

**Why:** generalises the tool-calling pattern from a single warehouse (project 02) to a whole cloud provider's surface area, closer to how a real data platform is actually composed.

### 07 · [Autonomous Remediation](07-autonomous-remidation/)

An agent that goes beyond detection to autonomously fix issues it finds — e.g. re-running a failed step, backfilling bad data, rolling back a bad schema change.

**Why:** this is the step from "agent that tells you something is wrong" to "agent that fixes it," which is where agentic systems start delivering operational time savings rather than just better alerts.

### 08 · [Capstone](08-capstone/)

A combined, production-style system drawing on all of the above: tool calling, data quality checks, pipeline investigation, schema change detection, and autonomous remediation working together.

**Why:** ties the individual skills from projects 01–07 into one coherent, end-to-end agentic system — the portfolio's demonstration of what a production-ready agentic data engineering platform looks like.

---

