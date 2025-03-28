import pandas as pd
import subprocess
import time
import logging

# ------------------------------------------------------------------------------
# 1) Configuration
# ------------------------------------------------------------------------------
input_file = "enron.xlsx"          # Input Excel file
output_file = "enron_output.xlsx"  # Output Excel file

# Set up logging to a file. 
# level=logging.INFO ensures info, warning, error, critical logs are captured.
# You can also set a different format if you like.
logging.basicConfig(
    filename='reply_log.txt', 
    level=logging.INFO, 
    format='%(asctime)s %(levelname)s: %(message)s'
)

# Example prompt template
PROMPT_TEMPLATE = """You are a helpful email assistant. I have just received the following email. 
Please generate a reply for me. Only return the email body without reasoning.
Email:
{}
===================="""

# Define your model names as needed
model_list = [
    "gemma3:1b", 
    "gemma:2b", 
    "llama3.2:3b", 
    "mistral"

]

# Corresponding column names to store the replies
output_col_names = [
    "Reply_gemma3:1b", 
    "Reply_gemma:2b", 
    "Reply_llama3.2:3b", 
    "Reply_mistral"

]

# ------------------------------------------------------------------------------
# 2) Read the Excel file
# ------------------------------------------------------------------------------
df = pd.read_excel(input_file, dtype=str)

# Ensure the DataFrame has at least 1 column (the email body)
if df.shape[1] < 1:
    raise ValueError("The Excel file does not have at least one column for email text.")

# Create new columns for the 4 model outputs if they do not exist
for col_name in output_col_names:
    if col_name not in df.columns:
        df[col_name] = ""

# ------------------------------------------------------------------------------
# 3) Define a function to call local LLaMA models via ollama
# ------------------------------------------------------------------------------
def call_local_model(model_name: str, email_body: str, row_index: int) -> str:
    """
    Calls a local LLM model using `ollama run <model_name>` and returns its text response.
    Also logs input, output, and time taken.
    """
    prompt = PROMPT_TEMPLATE.format(email_body)

    # Log the input before calling the model
    logging.info(f"[Row {row_index}] Model: {model_name} | Input: {email_body}")

    start_time_model = time.time()
    process = subprocess.run(
        ["ollama", "run", model_name],
        input=prompt,
        text=True,
        capture_output=True
    )
    end_time_model = time.time()

    output_text = process.stdout.strip()

    # Log the output and time cost
    elapsed = end_time_model - start_time_model
    logging.info(f"[Row {row_index}] Model: {model_name} | Time: {elapsed:.2f}s | Output: {output_text}")

    return output_text

# ------------------------------------------------------------------------------
# 4) Process each row (skipping header), measure time
# ------------------------------------------------------------------------------
start_time = time.time()
num_rows = len(df)

# 如果只想处理前 5 行（且第 1 行是表头），则可以将下面这行改为：
# for idx in range(1, min(num_rows, 6)):
for idx in range(1, num_rows):
    email_text = df.iloc[idx, 0] if pd.notna(df.iloc[idx, 0]) else ""

    row_start_time = time.time()
    for m_idx, model_name in enumerate(model_list):
        # Call the local model and store the result
        response_text = call_local_model(model_name, email_text, idx)
        df.at[idx, output_col_names[m_idx]] = response_text
    row_end_time = time.time()

    print(f"Processed row {idx}/{num_rows - 1} in {row_end_time - row_start_time:.2f} seconds.")

end_time = time.time()
total_time = end_time - start_time
avg_time_per_row = total_time / (num_rows - 1) if num_rows > 1 else 0

# ------------------------------------------------------------------------------
# 5) Save the updated DataFrame to a new XLSX file
# ------------------------------------------------------------------------------
df.to_excel(output_file, index=False)

# Print summary
print(f"\nProcessing completed (first {num_rows-1} rows).")
print(f"Total execution time: {total_time:.2f} seconds.")
print(f"Average time per row: {avg_time_per_row:.2f} seconds.")
print(f"The updated file is saved to: {output_file}")
print("Logs have been recorded in reply_log.txt.")
