from typing import Any, Dict

def transform_gka_output(event: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform the raw GKA output into the strict JSON format and return as 'response'.
    """
    gka_response = context["tools"]["AQ&A Data Store"]

    suggestion = (
        gka_response.get("humanAgentSuggestionResults", [{}])[0]
        .get("suggestKnowledgeAssistResponse", {})
        .get("knowledgeAssistAnswer", {})
        .get("suggestedQueryAnswer", {})
    )

    answer_text = suggestion.get("answerText", "").strip()
    snippets = suggestion.get("generativeSource", {}).get("snippets", [])

    quotes_list = []
    sources_list = []

    for idx, s in enumerate(snippets):
        quote_text = s.get("snippet", "") or s.get("passage", "")
        quote_url = s.get("uri", "") or s.get("sourceUri", "")
        quote_name = s.get("title", "") or s.get("documentTitle", "")

        if quote_text:
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
        "reasoning": "",  # Let the LLM fill this part using instructions
        "quotes": quotes_list,
        "sources": sources_list
    }

    return {
        "response": final_json
    }
