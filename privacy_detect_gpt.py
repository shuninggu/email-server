import os
import time
from openai import OpenAI
import pandas as pd

# ------------------------------------------------------------------------------
# 1) Configuration
# ------------------------------------------------------------------------------
# Input and output files
input_file = "enron_labeled.xlsx"
output_file = "enron/enron_gpt4_prompt8_gpt.xlsx"

# Set your OpenAI API key from environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Prompt template (example template):
PROMPT_TEMPLATE_8 = """In the following sentence, please convert all mentions of specific names, specific places, and numbers that may be sensitive into a format that represents the type of information they belong to.
Format requirements:
1. Always use double quotes for both keys and values: "key": "value"
2. Keep the rest of the sentence unchanged
3. Place the key-value pair exactly where the original information appears

You may select keys from the following list: Person Name, Email Address, Phone Number, Physical Address, password, Job Title, Organization, important time;

Here's an Example:
Input: Please write a greeting card for Nancy and her email address is nancy@gmail.com.
Output: Please write a greeting card for "name": "Nancy" and her email address is "email address": "nancy@gmail.com".

Note: Every piece of sensitive information MUST be converted to "key": "value" format with double quotes. If not applicable, return "None". Don't use the example in the real output, just follow the format.
Real Input:
{}

Real Output:

"""

# ------------------------------------------------------------------------------
# 2) Read the Excel file
# ------------------------------------------------------------------------------
df = pd.read_excel(input_file, dtype=str)
num_rows = len(df)

# Create a new column for GPT-4 responses if it doesn't exist
if "Private_GPT4" not in df.columns:
    df["Private_GPT4"] = ""

# ------------------------------------------------------------------------------
# 3) Define a function to call GPT-4
# ------------------------------------------------------------------------------
def call_gpt4(email_body: str) -> str:
    """
    Calls GPT-4 via OpenAI's ChatCompletion endpoint and returns the response.
    """
    prompt = PROMPT_TEMPLATE_8.format(email_body)

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.0,  # Adjust temperature as needed
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error calling GPT-4: {e}")
        return "Error or Timeout"

# ------------------------------------------------------------------------------
# 4) Process rows and measure execution time
# ------------------------------------------------------------------------------
start_time = time.time()

# Control how many rows you want to process
rows_to_process = min(105, num_rows)

for idx in range(rows_to_process):
    email_text = df.iloc[idx, 0] if pd.notna(df.iloc[idx, 0]) else ""

    row_start_time = time.time()
    model_response = call_gpt4(email_text)
    row_end_time = time.time()

    # Save the model's prediction to the DataFrame
    df.at[idx, "Private_GPT4"] = model_response

    print(f"Processed row {idx}/{rows_to_process - 1} in {row_end_time - row_start_time:.2f} seconds.")

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
print(f"Average time per row: {avg_time_per_row:.2f} seconds.")
print(f"The updated file is saved to: {output_file}")
