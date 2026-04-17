import streamlit as st
import json
import time
import pandas as pd

# Pre-load hyperpipeline modules
from hyperpipeline.orchestrator import ParentOrchestrator
from hyperpipeline.indic_translator import IndicTranslator
from hyperpipeline.chunks import (
    RetrievalChunk,
    FeatureComposerChunk,
    DomainMetricChunk,
    EvidenceReportingChunk
)

CHUNKS_MAP = {
    "retrieval_chunk": RetrievalChunk(),
    "feature_chunk": FeatureComposerChunk(),
    "feature_composer_chunk": FeatureComposerChunk(),
    "domain_metric_chunk": DomainMetricChunk(),
    "reporting_chunk": EvidenceReportingChunk(),
    "evidence_and_reporting_chunk": EvidenceReportingChunk()
}

st.set_page_config(page_title="Hyperpipeline Agent", layout="wide", page_icon="🤖")

st.markdown("""
<style>
.main { background-color: #0d1117; color: #c9d1d9; }
.execution-log { background-color: #161b22; color: #79c0ff; padding: 10px; border-radius: 5px; font-family: monospace; white-space: pre-wrap; font-size: 13px;}
</style>
""", unsafe_allow_html=True)

st.title("🤖 Hyperpipeline Agent Terminal")
st.caption("Powered by LM Studio & AutoGluon Orchestrator")

# Initialize Orchestrator and Translator pointing to LM Studio default port
orchestrator = ParentOrchestrator(base_url="http://localhost:1234/v1")
translator = IndicTranslator(base_url="http://localhost:1234/v1")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "payload" in msg:
            with st.expander("🛠️ Execution Logs & Application Spec", expanded=False):
                st.markdown(f'<div class="execution-log">{msg["payload"]}</div>', unsafe_allow_html=True)

if prompt := st.chat_input("Ask the Hyperpipeline (e.g. 'Compute ocean heat content in the Indian Ocean down to 700m')"):
    st.session_state.messages.append({"role": "user", "content": prompt, "payload": ""})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        logs_placeholder = st.empty()
        
        logs = f"1. [IndicNLP Fusion] Translating query locally if needed...\n"
        logs_placeholder.markdown(f'<div class="execution-log">{logs}</div>', unsafe_allow_html=True)
        
        translated_query = translator.translate_if_needed(prompt)
        if translated_query != prompt:
            logs += f"-> Native Translation: {translated_query}\n\n"
        else:
            logs += f"-> Query is English. No translation needed.\n\n"

        logs += f"2. Contacting Local LM Studio Orchestrator for task routing...\n"
        logs_placeholder.markdown(f'<div class="execution-log">{logs}</div>', unsafe_allow_html=True)
        
        # 1. Orchestration Layer (Pull Context Memory natively)
        chat_history = ""
        for m in st.session_state.messages[-4:]:
            chat_history += f"{m['role']}: {m['content']}\n"
            
        spec, plan = orchestrator.generate_plan(translated_query, chat_history=chat_history)
        
        logs += f"\n[Spec Generated]: Application Type = {spec.application_type}\n"
        logs += f"[Spec Filters]: Regions = {spec.region_mode}, Time = {spec.time_mode}\n"
        logs += f"[Spec Vars]: {spec.required_variables}\n"
        logs += f"[Execution Plan]: Steps = {plan.steps}\n\n"
        logs_placeholder.markdown(f'<div class="execution-log">{logs}</div>', unsafe_allow_html=True)

        # 2. Execution Loop
        logs += "2. Spawning Specialist Chunks...\n"
        context = {"raw_query": translated_query}
        for step_name in plan.steps:
            if step_name not in CHUNKS_MAP:
                logs += f"  [Warning] Chunk {step_name} not found. Skipping.\n"
                continue
                
            chunk = CHUNKS_MAP[step_name]
            logs += f"  -> Running {step_name}...\n"
            context = chunk.execute(spec, context)
            
        logs_placeholder.markdown(f'<div class="execution-log">{logs}</div>', unsafe_allow_html=True)

        # 3. Final Output Assembly
        final_report = context.get("final_report", {})
        
        logs += "\n3. Report Assembled Validating Provenance Constraints. Synthesizing natural response...\n"
        logs_placeholder.markdown(f'<div class="execution-log">{logs}</div>', unsafe_allow_html=True)
        
        # 4. Agentic Synthesis Layer
        natural_response = orchestrator.synthesize_report(prompt, final_report)
        
        final_message = f"**Executed Action:** `{spec.application_type}`\n\n{natural_response}"
        st.markdown(final_message)
        
        # 5. Dynamic File Format Conversion
        if hasattr(spec, 'file_format') and spec.file_format:
            if spec.file_format == "json":
                st.download_button(label="📦 Download Data (JSON)", data=json.dumps(final_report, indent=2), file_name="hyper_output.json", mime="application/json")
            elif spec.file_format == "csv":
                # Convert retrieving context/metrics safely into a dummy DataFrame
                try:
                    df = pd.DataFrame(context.get("retrieval_data", {"data": ["empty"]}))
                except Exception:
                    df = pd.DataFrame([context.get("retrieval_data", {})])
                st.download_button(label="📊 Download Records (CSV)", data=df.to_csv(index=False).encode('utf-8'), file_name="hyper_output.csv", mime="text/csv")
            elif spec.file_format == "markdown":
                st.download_button(label="📝 Download Report (MD)", data=natural_response, file_name="hyper_report.md", mime="text/markdown")

        st.session_state.messages.append({"role": "assistant", "content": final_message, "payload": logs})
