import pandas as pd

# File paths
response_file = "agent_assist_responses.xlsx"
question_id_file = "non_ambiguous_questions.xlsx"

# Load Excel files
responses_df = pd.read_excel(response_file)
question_ids_df = pd.read_excel(question_id_file)

# Standardize question column names
responses_df["question_clean"] = responses_df["question"].str.strip().str.lower()
question_ids_df["question_clean"] = question_ids_df["Question"].str.strip().str.lower()

# Merge based on cleaned question
merged_df = pd.merge(
    responses_df,
    question_ids_df[["questionId", "question_clean"]],
    on="question_clean",
    how="left"
)

# Check for unmatched questions
missing = merged_df[merged_df["questionId"].isnull()]
if not missing.empty:
    print("⚠️ Warning: Some questions could not be matched to a questionId:")
    print(missing["question"].tolist())

# Normalize rows per source title/URI
normalized_rows = []

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
        normalized_rows.append({
            "question_id": qid,
            "question": question,
            "answer_status": answer_status,
            "answer": answer,
            "source_title": title.strip(),
            "source_uri": uri.strip()
        })

# Create final DataFrame
final_df = pd.DataFrame(normalized_rows)

# Save to Excel
final_df.to_excel("agent_assist_final_expanded.xlsx", index=False)
print("✅ Final file saved as agent_assist_final_expanded.xlsx")
