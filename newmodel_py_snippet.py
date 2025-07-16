from typing import Any, Dict

def transform_gka_output(event: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    gka_response = context["tools"]["AQ&A Data Store"]

    suggestion = (
        gka_response["humanAgentSuggestionResults"][0]
        .get("suggestKnowledgeAssistResponse", {})
        .get("knowledgeAssistAnswer", {})
        .get("suggestedQueryAnswer", {})
    )

    answer_text = suggestion.get("answerText", "").strip()
    snippets = suggestion.get("generativeSource", {}).get("snippets", [])

    quotes_list = []
    sources_list = []
    debug_info = []  # <-- collect debug info here

    for idx, s in enumerate(snippets):
        quote_text = s.get("snippet", "")
        quote_url = s.get("uri", "")
        quote_name = s.get("title", "")

        debug_info.append(f"Snippet {idx+1}: {quote_text[:30]}... | {quote_url} | {quote_name}")  # shorten text

        quotes_list.append({
            "quote": quote_text,
            "url": quote_url,
            "name": quote_name
        })
        sources_list.append(idx + 1)

    if not answer_text:
        answer_text = "I DO NOT KNOW"

    if not quotes_list:
        sources_list = []

    final_json = {
        "answer": answer_text,
        "reasoning": "",  # LLM will fill
        "quotes": quotes_list,
        "sources": sources_list
    }

    return {
        "response": final_json,
        "debug": debug_info  # <-- appears in the final output JSON
    }
