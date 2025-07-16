from typing import Any, Dict
import json

def transform_gka_output(event: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform the raw GKA output into the strict JSON format and return it as 'response'.
    """
    gka_response = context["tools"].get("AQ&A Data Store", {})

    # DEBUG: Uncomment to inspect actual payload if things go wrong
    # print("🔍 Full GKA Response:\n", json.dumps(gka_response, indent=2))

    suggestion = (
        gka_response.get("humanAgentSuggestionResults", [{}])[0]
        .get("suggestKnowledgeAssistResponse", {})
        .get("knowledgeAssistAnswer", {})
        .get("suggestedQueryAnswer", {})
    )

    answer_text = suggestion.get("answerText", "").strip()

    # Try standard path
    snippets = suggestion.get("generativeSource", {}).get("snippets", [])
    
    # Fallback: Try alternative nesting if empty
    if not snippets:
        generative_sources = suggestion.get("generativeSources", [])
        if generative_sources:
            snippets = generative_sources[0].get("snippets", [])

    quotes_list = []
    sources_list = []

    for idx, s in enumerate(snippets):
        quote_text = s.get("snippet", "").strip()
        quote_url = s.get("uri", "").strip()
        quote_name = s.get("title", "").strip()

        # Only include quotes with at least the quote text and uri
        if quote_text and quote_url:
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
        "reasoning": "",  # Let the LLM complete this based on provided instructions
        "quotes": quotes_list,
        "sources": sources_list
    }

    return {
        "response": final_json
    }
