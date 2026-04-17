import sys
from hyperpipeline.orchestrator import ParentOrchestrator
from hyperpipeline.indic_translator import IndicTranslator

def backtest():
    print("=== HYPERPIPELINE BACKTEST SUITE: FORMAT CONVERTERS ===\n")
    
    orc = ParentOrchestrator(base_url="http://localhost:1234/v1")
    translator = IndicTranslator(base_url="http://localhost:1234/v1")
    
    queries = [
        ("Explicit CSV Request", "Map the ocean heat content of the Pacific over the last year. Give me the raw data downloaded as CSV."),
        ("Explicit JSON Request", "I need the exact telemetry tuples for float 1901111 exported as JSON script."),
        ("Markdown Report Request", "Provide an anomaly overview of BGC oxygen levels. Format it entirely as a markdown report to download."),
        ("No Format Defined (Default)", "What is the average temperature in the Mediterranean sea?"),
        ("Indic Language + CSV Request", "हिंद महासागर के तापमान के आंकड़े खोजें और इसे CSV फाइल के रूप में डाउनलोड करने दें")
    ]
    
    passed = 0
    failed = 0
    
    for name, raw_text in queries:
        print(f"\n[Test] {name}")
        print(f"Raw Text: '{raw_text}'")
        
        # 1. Indic Translation
        translated = translator.translate_if_needed(raw_text)
        if translated != raw_text:
            print(f"  -> Translated: '{translated}'")
            
        # 2. Orchestration
        print("  -> Running Orchestrator LLM...")
        try:
            spec, plan = orc.generate_plan(translated)
            fformat = getattr(spec, 'file_format', None)
            
            print(f"  -> Result format flag: '{fformat}' | Steps: {plan.steps}")
            
            # Simple assertions based on test name
            success = False
            if "CSV" in name and fformat == "csv": success = True
            elif "JSON" in name and fformat == "json": success = True
            elif "Markdown" in name and fformat == "markdown": success = True
            elif "Default" in name and fformat is None: success = True
            
            if success:
                print("  [✓] PASSED")
                passed += 1
            else:
                print(f"  [X] FAILED (Expected format flag based on query, got {fformat})")
                failed += 1
                
        except Exception as e:
            print(f"  [!] CRASHED: {e}")
            failed += 1

    print(f"\n=== BACKTEST COMPLETE: {passed}/{len(queries)} PASSED ===")

if __name__ == "__main__":
    backtest()
