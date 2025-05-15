import pandas as pd
import json

# File paths
response_file = "agent_assist_responses.xlsx"
question_id_file = "non_ambiguous_questions.json"

# Load Excel responses
responses_df = pd.read_excel(response_file)

# Load JSON with question IDs
with open(question_id_file, 'r', encoding='utf-8') as f:
    questions_data = json.load(f)

question_id_df = pd.DataFrame(questions_data)

# Normalize question text for matching
responses_df["question_clean"] = responses_df["question"].str.strip().str.lower()
question_id_df["question_clean"] = question_id_df["Question"].str.strip().str.lower()

# Merge by normalized question text
merged_df = pd.merge(
    responses_df,
    question_id_df[["questionId", "question_clean"]],
    on="question_clean",
    how="left"
)

# Optional: check for unmatched entries
missing = merged_df[merged_df["questionId"].isnull()]
if not missing.empty:
    print("⚠️ Warning: Some questions couldn't be matched to a questionId:")
    print(missing["question"].tolist())

# Expand rows per source title/uri pair
expanded_rows = []

for _, row in merged_df.iterrows():
    qid = row["questionId"]
    question = row["question"]
    answer = row["answer"]
    answer_status = row.get("answer_status", "")
    titles = str(row["source_titles"]).split("\n") if pd.notna(row["source_titles"]) else [""]
    uris = str(row["source_uris"]).split("\n") if pd.notna(row["source_uris"]) else [""]

    max_len = max(len(titles), len(uris))
    titles += [""] * (max_len - len(titles))
    uris += [""] * (max_len - len(uris))

    for title, uri in zip(titles, uris):
        expanded_rows.append({
            "question_id": qid,
            "question": question,
            "answer_status": answer_status,
            "answer": answer,
            "source_title": title.strip(),
            "source_uri": uri.strip()
        })

# Create final DataFrame
final_df = pd.DataFrame(expanded_rows)

# Save to Excel
final_df.to_excel("agent_assist_final_expanded.xlsx", index=False)
print("✅ Final file saved as agent_assist_final_expanded.xlsx")