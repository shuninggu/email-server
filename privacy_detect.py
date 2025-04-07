import pandas as pd
import subprocess
import time

# ------------------------------------------------------------------------------
# 1) Configuration
# ------------------------------------------------------------------------------
# Input and output files
input_file = "enron_labeled.xlsx"
output_file = "enron/enron_gemma3_1b_prompt6.xlsx"

# PROMPT_TEMPLATE_1 = """
# Identify privacy-sensitive data such as names, emails, phone numbers, addresses, IDs, financial data, or personally identifiable information in the email text below.

# List each detected item exactly as it appears in the text, one per line, without numbering, extra text, or explanation.  
# If none found, return "NONE".

# Email Body:
# {}

# List:

# """




# PROMPT_TEMPLATE_2 = """
# List ALL privacy-sensitive data EXACTLY as they appear in the text below.
# Do NOT add anything that is not explicitly written in the email body.
# One item per line, no numbering, no explanation, nothing else.
# If none, write NONE.

# Email Body:
# {}

# List:
# """


# PROMPT_TEMPLATE_3 = """You are a privacy filter. Extract all private data in the email text and label each with its type. Use this format:

# [
#   {{"type": "Person Name", "text": "Vincent Kaminski"}},
#   {{"type": "Email Address", "text": "Vince.J.Kaminski@enron.com"}},
#   ...
# ]




# # Prompt template (escaped curly braces for .format())
# # PROMPT_TEMPLATE_4 = """You are a privacy filter. Extract all private data values in the email text and label each with its type. Use this format:

# Private data types:
# Person Names, Email Addresses, Phone Numbers, Physical Addresses, Job Title / Organization, passwords, important times

# Email:
# {}

# Values:

# """

PROMPT_TEMPLATE_6 = """In the following sentence, please convert all mentions of specific names, specific places, and numbers into a format that represents the type of information they belong to.
Format requirements:
1. Always use double quotes for both keys and values: "key": "value"
2. Keep the rest of the sentence unchanged
3. Place the key-value pair exactly where the original information appears

Keys may be selected from the following list: Person Names, Email Addresses, Phone Numbers, Physical Addresses, passwords, Job Title, Organization, important time;

Here's an Example:
Input: 'Please write a greeting card for Nancy when she is 18 years old and lives in Boston.'
Output: 'Please write a greeting card for "name": "Nancy" when she is "age": "18" years old and lives in "city": "Boston".'

Note: Every piece of sensitive information MUST be converted to "key": "value" format with double quotes. If not applicable, return "None".
Real Input:
{}

Output:

"""


PROMPT_TEMPLATE_7 = """In the following sentence, please convert all mentions of specific “Person Names, Email Addresses, Phone Numbers, Physical Addresses, passwords, Job Title, Organization, important time”, into a format that represents the type of information they belong to.
Format requirements:
1. Always use double quotes for both keys and values: "key": "value"
2. Keep the rest of the sentence unchanged
3. Place the key-value pair exactly where the original information appears

Keys may be selected from the following list: Person Names, Email Addresses, Phone Numbers, Physical Addresses, passwords, Job Title, Organization, important time;

Here's an Example:
Input: 'Please write a greeting card for Nancy when she is 18 years old and lives in Boston.'
Output: 'Please write a greeting card for "name": "Nancy" when she is "age": "18" years old and lives in "city": "Boston".'

Note: Every piece of sensitive information MUST be converted to "key": "value" format with double quotes. 
If you think there's no private data, return "None".

Real Input:
{}

Real Output:

"""

# ------------------------------------------------------------------------------
# 2) Read the Excel file
# ------------------------------------------------------------------------------
df = pd.read_excel(input_file, dtype=str)
num_rows = len(df)

# Ensure a "Prediction" column exists
if "Prediction" not in df.columns:
    df["Prediction"] = ""

# ------------------------------------------------------------------------------
# 3) Define a function to call the local LLaMA model
# ------------------------------------------------------------------------------
def call_llama_local(email_body: str) -> str:
    """
    Calls the local LLaMA model via `ollama run gemma3:1b` and returns the model output.
    """
    prompt = PROMPT_TEMPLATE_6.format(email_body)

    process = subprocess.run(
        ["ollama", "run", "gemma3:1b"],
        input=prompt,
        text=True,
        capture_output=True
    )

    return process.stdout.strip()

# ------------------------------------------------------------------------------
# 4) Process rows and measure execution time
# ------------------------------------------------------------------------------
start_time = time.time()

for idx in range(0, min(105, num_rows)):
    email_text = df.iloc[idx, 0] if pd.notna(df.iloc[idx, 0]) else ""

    row_start_time = time.time()
    model_response = call_llama_local(email_text)
    row_end_time = time.time()

    df.at[idx, "Prediction"] = model_response

    print(f"Processed row {idx}/{num_rows-1} in {row_end_time - row_start_time:.2f} seconds.")

end_time = time.time()
total_time = end_time - start_time
avg_time_per_row = total_time / (min(11, num_rows)) if num_rows > 0 else 0

# ------------------------------------------------------------------------------
# 5) Save the updated DataFrame to a new XLSX file
# ------------------------------------------------------------------------------
df.to_excel(output_file, index=False)

# Print summary statistics
print(f"\nProcessing completed (first {min(11, num_rows)} rows only).")
print(f"Total execution time: {total_time:.2f} seconds.")
print(f"Average time per row: {avg_time_per_row:.2f} seconds.")
print(f"The updated file is saved to: {output_file}")
