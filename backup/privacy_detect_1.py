import subprocess
import time

# ------------------------------------------------------------------------------
# 1) Configuration
# ------------------------------------------------------------------------------
# Input and output files
input_file = "enron_labeled.xlsx"
output_file = "enron/enron_gemma3_1b_prompt8.xlsx"

# Prompt template (example template):
PROMPT_TEMPLATE_8 = """In the following sentence, please convert all mentions of specific names, specific places, and numbers that may be sensitive into a format that represents the type of information they belong to.
Format requirements:
1. Always use double quotes for both keys and values: "key": "value"
2. Keep the rest of the sentence unchanged
3. Place the key-value pair exactly where the original information appears

You may select keys from the following list: Person Name, Email Address, Phone Number, Physical Address, password, Job Title, Organization, important time;

Here's an Example:
Input: John, Please write a greeting card for Nancy and her email address is nancy@gmail.com. Phillip
Output: "name": "John", Please write a greeting card for "name": "Nancy" and her email address is "email address": "nancy@gmail.com". "name": "Phillip"

Note: Every piece of sensitive information MUST be converted to "key": "value" format with double quotes. If not applicable, return "None". Don't use the example in the real output, just follow the format.
Real Input:
{}

Real Output:

"""

# List of your local model identifiers
model_list = [
    "gemma3:1b",
    "llama3.2:1b,
    "gemma:2b",
    "llama3.2:3b",
    "mistral"
]

# Corresponding column names to store model replies
output_col_names = [
    "Private_gemma3:1b",
    "Private_llama3.2:1b"
    "Private_gemma:2b",
    "Private_llama3.2:3b",
    "Private_mistral"
]

# ------------------------------------------------------------------------------
# 2) Read the Excel file
# ------------------------------------------------------------------------------
df = pd.read_excel(input_file, dtype=str)
num_rows = len(df)

# Ensure each output column exists in DataFrame
for col_name in output_col_names:
    if col_name not in df.columns:
        df[col_name] = ""

# ------------------------------------------------------------------------------
# 3) Define a function to call the local models
# ------------------------------------------------------------------------------
def call_llama_local(model_name: str, email_body: str) -> str:
    """
    Calls the specified local LLaMA-like model via `ollama run <model_name>` and returns the model output.
    """
    prompt = PROMPT_TEMPLATE_8.format(email_body)

    process = subprocess.run(
        ["ollama", "run", model_name],
        input=prompt,
        text=True,
        capture_output=True
    )

    return process.stdout.strip()

# ------------------------------------------------------------------------------
# 4) Process rows and measure execution time
# ------------------------------------------------------------------------------
start_time = time.time()

# Control how many rows you want to process
rows_to_process = min(105, num_rows)

for idx in range(rows_to_process):
    # Read the email text from the first column (assuming it's column index 0)
    email_text = df.iloc[idx, 0] if pd.notna(df.iloc[idx, 0]) else ""

    # Loop over each model and store the result in the corresponding column
    for model_name, col_name in zip(model_list, output_col_names):
        row_start_time = time.time()
        model_response = call_llama_local(model_name, email_text)
        row_end_time = time.time()

        # Save the model's prediction to the DataFrame
        df.at[idx, col_name] = model_response

        print(f"Processed row {idx}/{rows_to_process - 1} with model {model_name} in {row_end_time - row_start_time:.2f} seconds.")

end_time = time.time()
total_time = end_time - start_time
avg_time_per_row = total_time / rows_to_process if rows_to_process > 0 else 0

# ------------------------------------------------------------------------------
# 5) Save the updated DataFrame to a new XLSX file
# ------------------------------------------------------------------------------
df.to_excel(output_file, index=False)

# Print summary statistics
print(f"\nProcessing completed (first {rows_to_process} rows).")
print(f"Total execution time: {total_time:.2f} seconds.")
print(f"Average time per row (for all models): {avg_time_per_row:.2f} seconds.")
print(f"The updated file is saved to: {output_file}")
