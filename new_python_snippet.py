from typing import Any, Dict

def transform_gka_output(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform the raw GKA output into the strict JSON format.
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
        quote_text = s.get("snippet", "").strip()
        quote_url = s.get("uri", "").strip()
        quote_name = s.get("title", "").strip()

        if quote_text:
            quotes_list.append({
                "quote": quote_text,
                "url": quote_url or "",
                "name": quote_name or ""
            })
            sources_list.append(idx + 1)

    if not answer_text:
        answer_text = "I DO NOT KNOW"

    if not quotes_list:
        sources_list = []

    final_json = {
        "answer": answer_text,
        "reasoning": "I used the AQ&A Data Store snippets and quotes to verify the answer step-by-step.",  # Will be expanded by LLM
        "quotes": quotes_list,
        "sources": sources_list
    }

    return final_json
