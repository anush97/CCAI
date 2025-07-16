from typing import Any, Dict
from agentassist.runtime import Action, EventHandler, Event

@Action()
def transform_gka_output(event: Event, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform the raw GKA output into the strict JSON format.
    """
    # Get the raw GKA output from the Data Store tool
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

    for idx, s in enumerate(snippets):
        quote_text = s.get("snippet", "")
        quote_url = s.get("uri", "")
        quote_name = s.get("title", "")

        quotes_list.append({
            "quote": quote_text,
            "url": quote_url,
            "name": quote_name
        })

        # Use snippet index +1 as a simple doc index (adjust if you have real indexes)
        sources_list.append(idx + 1)

    # If no answerText, fallback
    if not answer_text:
        answer_text = "I DO NOT KNOW"

    # If no quotes, fallback
    if not quotes_list:
        sources_list = []

    final_json = {
        "answer": answer_text,
        "reasoning": "",  # Let LLM instructions generate reasoning step
        "quotes": quotes_list,
        "sources": sources_list
    }

    return final_json
