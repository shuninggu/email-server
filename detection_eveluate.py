import pandas as pd
import json
import numpy as np

# Load the processed file
df = pd.read_excel("enron/enron_private_output.xlsx")

# Ground Truth column name
ground_truth_col = "Ground Truth"

# Columns to evaluate
model_cols = [
    "Extracted_gemma3:1b",
    "Extracted_gemma:2b",
    "Extracted_llama3.2:3b",
    "Extracted_mistral",
    "Extracted_GPT4"
]

# Function to safely parse JSON-like string lists
def parse_values(value):
    if pd.isnull(value) or value == "None":
        return []
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return []

# Scoring function per email
def score_row(gt_list, pred_list):
    if len(gt_list) == 0:
        return 1.0 if len(pred_list) == 0 else 0.0
    else:
        correct_hits = sum(1 for item in gt_list if item in pred_list)
        return correct_hits / len(gt_list)

# Initialize a dictionary to store scores
model_scores = {model: 0 for model in model_cols}

# Calculate scores for each model
for _, row in df.iterrows():
    ground_truth = parse_values(row[ground_truth_col])
    for model in model_cols:
        prediction = parse_values(row[model])
        score = score_row(ground_truth, prediction)
        model_scores[model] += score

# Display summary results
results_df = pd.DataFrame({
    "Model": model_cols,
    "Total Score": [model_scores[model] for model in model_cols],
    "Average Score": [model_scores[model] / len(df) for model in model_cols]
})

# Save results to Excel
results_df.to_excel("enron/evaluation_results.xlsx", index=False)

print("Evaluation completed. Results saved to evaluation_results.xlsx")
print(results_df)
