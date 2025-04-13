import pandas as pd
import time
import os
import openai

# Set your OpenAI API key from the environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# File paths
input_file = "enron.xlsx"             # Input Excel file
output_file = "enron_output.xlsx"     # Output Excel file

# Define the prompt template:
# The system should extract all private values (names, emails, phone numbers, etc.) in JSON array format.
PROMPT_TEMPLATE = """You are an expert in extracting private values from email texts.
Given the following email text, identify all private values present such as personal names, email addresses, phone numbers, and any sensitive identifiers.
Please respond with a JSON array in the following format (e.g., ["Randy", "Patti S", "Phillip"]).
Email:
{}
====================
"""

# Specify the GPT-4o model (update the model name if necessary)
model_gpt4o = "gpt-4o"

# Name of the column where detected private values will be stored
col_private_values = "Detected_Private_Values"

# ------------------------------------------------------------------------------
# 1) Read the Excel file
# ------------------------------------------------------------------------------
df = pd.read_excel(input_file, dtype=str)

# If the output column does not exist, add it.
if col_private_values not in df.columns:
    df[col_private_values] = ""

# ------------------------------------------------------------------------------
# 2) Define a function to call the OpenAI Chat API
# ------------------------------------------------------------------------------
def call_openai_chat(model_name: str, content: str) -> str:
    """
    Calls the OpenAI Chat API and returns the response text.
    """
    try:
        response = openai.ChatCompletion.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are ChatGPT."},
                {"role": "user", "content": content}
            ],
            temperature=0.0,  # Set to 0 for more deterministic outputs
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error calling OpenAI model {model_name}: {e}")
        return ""

# ------------------------------------------------------------------------------
# 3) Process each row and detect private values
# ------------------------------------------------------------------------------
start_time = time.time()
num_rows = len(df)

for idx in range(num_rows):
    # Get the email text from the first column
    email_text = df.iloc[idx, 0]
    if not isinstance(email_text, str):
        email_text = ""
    
    # Build the prompt with the email text.
    prompt_text = PROMPT_TEMPLATE.format(email_text)
    
    # Call GPT-4o with the prompt
    row_start_time = time.time()
    detected_values = call_openai_chat(model_gpt4o, prompt_text)
    
    # Save the detected private values to the new column.
    df.at[idx, col_private_values] = detected_values
    
    row_end_time = time.time()
    print(f"Processed row {idx+1}/{num_rows} in {row_end_time - row_start_time:.2f} seconds.")

# ------------------------------------------------------------------------------
# 4) Save the results to an Excel file
# ------------------------------------------------------------------------------
df.to_excel(output_file, index=False)
total_time = time.time() - start_time
print(f"\nFinished processing {num_rows} rows in {total_time:.2f} seconds.")
print(f"Output saved to {output_file}")
