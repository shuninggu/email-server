// server.js
// Run with: node server.js (ES Module)

import express from 'express';
import cors from 'cors';
import bodyParser from 'body-parser';
import fs from 'fs';
import path from 'path';
import fetch from 'node-fetch'; 
import dotenv from 'dotenv';
import xlsx from 'xlsx'; 

// If using new openai v4 library
import OpenAI from 'openai';

// Load environment variables
dotenv.config();

const app = express();
const PORT = 4000;

// Middleware
app.use(cors());
app.use(bodyParser.json());

// Configure OpenAI with your API key
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// 1) Helper: Local LLM call
async function callLocalLLM(input) {
  /**
   * Calls your local LLM endpoint (llama3.2:3b) and returns its response.
   */
  const prompt = `
You are a helpful email assistant. I have just received the following email. Please generate a reply for me.
Email:
{}
`;

  const response = await fetch('http://localhost:11434/api/generate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: "llama3.2:3b",
      prompt: `${prompt}\n${input}\n generate reply:`,
      stream: false,
      temperature: 0.7,
      top_k: 50,
      top_p: 0.9,
      max_tokens: 200,
    })
  });

  if (!response.ok) {
    throw new Error(`Local LLM error! status: ${response.status}`);
  }

  const data = await response.json();
  return data.response; // The local LLM's reply
}

// 2) Helper: GPT-4 call
async function callGPT4(input) {
  /**
   * Calls the OpenAI GPT-4 API using the official openai library.
   * You need to set OPENAI_API_KEY in your environment.
   */
  try {
    const messages = [
      {
        role: "system",
        content: "You are a helpful email assistant. Generate a reply based on the following email."
      },
      {
        role: "user",
        content: input
      }
    ];

    // Using the new openai v4 library approach
    const response = await openai.chat.completions.create({
      model: "gpt-4",
      messages: messages,
      temperature: 0.7,
      max_tokens: 200,
      top_p: 0.9
    });
    
    // In case you want to inspect the full response:
    // console.log("GPT-4 full response:", JSON.stringify(response, null, 2));

    // Extract the text from the response
    const reply = response.choices[0].message.content;
    return reply;
  } catch (error) {
    console.error("Error calling GPT-4:", error);
    throw error;
  }
}

// Start the server
app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
    console.log(`Saving inputs to ${path.resolve('current_value.txt')}`);
  });

app.post('/save-input', async (req, res) => {
  // The user input from the frontend
  const { input } = req.body;

  // 1) Write user input to local file (optional)
  fs.writeFileSync('current_value.txt', input);
  console.log('Input saved locally:', input);

  // 2) Call local LLM
  const localStart = Date.now();
  let localReply = "";
  try {
    localReply = await callLocalLLM(input);
  } catch (err) {
    console.error("Local LLM call failed:", err);
    localReply = "Local LLM Error";
  }
  const localEnd = Date.now();
  const localElapsed = localEnd - localStart;

  console.log(`Local LLM completed in ${localElapsed} ms`);
  console.log('Local LLM reply:', localReply);

  // 3) Call GPT-4
  const gptStart = Date.now();
  let gptReply = "";
  try {
    gptReply = await callGPT4(input);
  } catch (err) {
    console.error("GPT-4 call failed:", err);
    gptReply = "GPT-4 Error";
  }
  const gptEnd = Date.now();
  const gptElapsed = gptEnd - gptStart;

  console.log(`GPT-4 call completed in ${gptElapsed} ms`);
  console.log('GPT-4 reply:', gptReply);

  // 4) Write to Excel
  const filePath = 'results.xlsx';
  let workbook;
  let worksheet;

  // Check if file exists
  if (fs.existsSync(filePath)) {
    // Read existing workbook from disk
    workbook = xlsx.readFile(filePath);
    worksheet = workbook.Sheets[workbook.SheetNames[0]];
  } else {
    // Create new workbook and worksheet with headers
    workbook = xlsx.utils.book_new();
    worksheet = xlsx.utils.aoa_to_sheet([
      [
        "Input_llama3.2:3b",
        "ReplyEmail_llama3.2:3b",
        "ProcessingTime(ms)_llama3.2:3b",
        "Input_gpt4o",
        "ReplyEmail_gpt4o",
        "ProcessingTime(ms)_gpt4o"
      ]
    ]);
    xlsx.utils.book_append_sheet(workbook, worksheet, 'Results');
  }

  // Determine next row index for appending new data
  const range = xlsx.utils.decode_range(worksheet['!ref']);
  const nextRowIndex = range.e.r + 1;

  // Write local LLM info (3 columns)
  // Column 0: Input to local LLM
  const cellLocalInput = xlsx.utils.encode_cell({ r: nextRowIndex, c: 0 });
  worksheet[cellLocalInput] = { t: 's', v: input };

  // Column 1: Local LLM reply
  const cellLocalReply = xlsx.utils.encode_cell({ r: nextRowIndex, c: 1 });
  worksheet[cellLocalReply] = { t: 's', v: localReply };

  // Column 2: Local LLM processing time
  const cellLocalTime = xlsx.utils.encode_cell({ r: nextRowIndex, c: 2 });
  worksheet[cellLocalTime] = { t: 'n', v: localElapsed };

  // Write GPT-4 info (3 columns)
  // Column 3: Input for GPT-4
  const cellGPTInput = xlsx.utils.encode_cell({ r: nextRowIndex, c: 3 });
  worksheet[cellGPTInput] = { t: 's', v: input };

  // Column 4: GPT-4 reply
  const cellGPTReply = xlsx.utils.encode_cell({ r: nextRowIndex, c: 4 });
  worksheet[cellGPTReply] = { t: 's', v: gptReply };

  // Column 5: GPT-4 processing time
  const cellGPTTime = xlsx.utils.encode_cell({ r: nextRowIndex, c: 5 });
  worksheet[cellGPTTime] = { t: 'n', v: gptElapsed };

  // Update the worksheet range to include the new row
  const newRange = {
    s: { c: 0, r: 0 },
    e: { c: 5, r: nextRowIndex }
  };
  worksheet['!ref'] = xlsx.utils.encode_range(newRange);

  // Write the updated workbook back to disk
  xlsx.writeFile(workbook, filePath);
  console.log(`✅ Successfully logged to Excel: ${filePath}`);

  // 5) Return response to frontend
  return res.json({
    success: true,
    localReply: localReply,
    localTime: localElapsed,
    gptReply: gptReply,
    gptTime: gptElapsed
  });
});

app.post('/save-selected', async (req, res) => {
    // The user input from the frontend
    // const { input } = req.body;

    const { input, timestamp } = req.body;
     // Save the selected text to a file
     fs.appendFileSync('selected_text.txt', 
        `\n[${timestamp}] Selected Text: ${input}`
    );
    
    console.log('Received selected text:', input);
  
    // 1) Write user input to local file (optional)
    fs.writeFileSync('current_value.txt', input);
    console.log('Input saved locally:', input);
  
    // 2) Call local LLM
    const localStart = Date.now();
    let localReply = "";
    try {
      localReply = await callLocalLLM(input);
    } catch (err) {
      console.error("Local LLM call failed:", err);
      localReply = "Local LLM Error";
    }
    const localEnd = Date.now();
    const localElapsed = localEnd - localStart;
  
    console.log(`Local LLM completed in ${localElapsed} ms`);
    console.log('Local LLM reply:', localReply);
  
    // 3) Call GPT-4
    const gptStart = Date.now();
    let gptReply = "";
    try {
      gptReply = await callGPT4(input);
    } catch (err) {
      console.error("GPT-4 call failed:", err);
      gptReply = "GPT-4 Error";
    }
    const gptEnd = Date.now();
    const gptElapsed = gptEnd - gptStart;
  
    console.log(`GPT-4 call completed in ${gptElapsed} ms`);
    console.log('GPT-4 reply:', gptReply);
  
    // 4) Write to Excel
    const filePath = 'results.xlsx';
    let workbook;
    let worksheet;
  
    // Check if file exists
    if (fs.existsSync(filePath)) {
      // Read existing workbook from disk
      workbook = xlsx.readFile(filePath);
      worksheet = workbook.Sheets[workbook.SheetNames[0]];
    } else {
      // Create new workbook and worksheet with headers
      workbook = xlsx.utils.book_new();
      worksheet = xlsx.utils.aoa_to_sheet([
        [
          "Input_llama3.2:3b",
          "ReplyEmail_llama3.2:3b",
          "ProcessingTime(ms)_llama3.2:3b",
          "Input_gpt4o",
          "ReplyEmail_gpt4o",
          "ProcessingTime(ms)_gpt4o"
        ]
      ]);
      xlsx.utils.book_append_sheet(workbook, worksheet, 'Results');
    }
  
    // Determine next row index for appending new data
    const range = xlsx.utils.decode_range(worksheet['!ref']);
    const nextRowIndex = range.e.r + 1;
  
    // Write local LLM info (3 columns)
    // Column 0: Input to local LLM
    const cellLocalInput = xlsx.utils.encode_cell({ r: nextRowIndex, c: 0 });
    worksheet[cellLocalInput] = { t: 's', v: input };
  
    // Column 1: Local LLM reply
    const cellLocalReply = xlsx.utils.encode_cell({ r: nextRowIndex, c: 1 });
    worksheet[cellLocalReply] = { t: 's', v: localReply };
  
    // Column 2: Local LLM processing time
    const cellLocalTime = xlsx.utils.encode_cell({ r: nextRowIndex, c: 2 });
    worksheet[cellLocalTime] = { t: 'n', v: localElapsed };
  
    // Write GPT-4 info (3 columns)
    // Column 3: Input for GPT-4
    const cellGPTInput = xlsx.utils.encode_cell({ r: nextRowIndex, c: 3 });
    worksheet[cellGPTInput] = { t: 's', v: input };
  
    // Column 4: GPT-4 reply
    const cellGPTReply = xlsx.utils.encode_cell({ r: nextRowIndex, c: 4 });
    worksheet[cellGPTReply] = { t: 's', v: gptReply };
  
    // Column 5: GPT-4 processing time
    const cellGPTTime = xlsx.utils.encode_cell({ r: nextRowIndex, c: 5 });
    worksheet[cellGPTTime] = { t: 'n', v: gptElapsed };
  
    // Update the worksheet range to include the new row
    const newRange = {
      s: { c: 0, r: 0 },
      e: { c: 5, r: nextRowIndex }
    };
    worksheet['!ref'] = xlsx.utils.encode_range(newRange);
  
    // Write the updated workbook back to disk
    xlsx.writeFile(workbook, filePath);
    console.log(`✅ Successfully logged to Excel: ${filePath}`);
  
    // 5) Return response to frontend
    return res.json({
      success: true,
      localReply: localReply,
      localTime: localElapsed,
      gptReply: gptReply,
      gptTime: gptElapsed
    });
});

app.post('/restore', async (req, res) => {
    const { selectedText, timestamp } = req.body;
    
    try {
        // Save the selected text to a file
        fs.appendFileSync('selected_text.txt', 
            `\n[${timestamp}] Selected Text: ${selectedText}`
        );
        
        console.log('Received selected text:', selectedText);
        
        // Restore privacy information
        const restoredText = restorePrivacyInfo(selectedText);
        
        res.json({ 
            success: true, 
            message: 'Selected text processed successfully',
            restoredText: restoredText
        });
    } catch (error) {
        console.error('Error processing selected text:', error);
        res.status(500).json({ 
            success: false, 
            message: 'Error processing selected text',
            error: error.message
        });
    }
});

function restorePrivacyInfo(selectedText) {
    try {
        console.log('Processing selected text:', selectedText);
        
        // Read privacy_storage.json
        const privacyData = JSON.parse(fs.readFileSync('privacy_storage.json', 'utf8'));
        console.log('Loaded privacy data:', privacyData);
        
        let restoredText = selectedText;

        // Iterate through each record in privacy_storage.json
        privacyData.forEach(record => {
            const { key, originalValue, replacedValue } = record;
            console.log(`Checking for replaced value: ${replacedValue}`);
            
            // Create a regular expression to match the replaced value
            const regex = new RegExp(`\\b${replacedValue}\\b`, 'g');
            
            // If the replaced value is found, restore it to the original value
            if (restoredText.match(regex)) {
                console.log(`Found match: ${replacedValue} -> ${originalValue}`);
                restoredText = restoredText.replace(regex, originalValue);
            }
        });

        console.log('Restored text:', restoredText);
        return restoredText;

    } catch (error) {
        console.error('Error restoring privacy info:', error);
        return selectedText; // If an error occurs, return the original selected text
    }
}

function generateReplacedText(originalText, formattedResult) {
    try {
        console.log('Original text:', originalText);
        console.log('Formatted result:', formattedResult);

        // Read privacy_storage.json
        const privacyData = JSON.parse(fs.readFileSync('privacy_storage.json', 'utf8'));
        console.log('Privacy data loaded:', privacyData);

        let replacedText = originalText;

        // Parse formattedResult if it's a string
        let parsedResult = formattedResult;
        if (typeof formattedResult === 'string') {
            try {
                parsedResult = JSON.parse(formattedResult);
                console.log('Parsed formatted result:', parsedResult);
            } catch (error) {
                console.error('Error parsing formattedResult:', error);
                return originalText;
            }
        }

        // Iterate through each record in privacy_storage.json
        privacyData.forEach(record => {
            const { key, originalValue, replacedValue } = record;
            console.log(`Processing replacement: ${key} - Original: ${originalValue} - Replace with: ${replacedValue}`);
            
            // Create a regular expression to match the original value
            const regex = new RegExp(`\\b${originalValue}\\b`, 'g');
            
            // Replace sensitive information in the text
            const previousText = replacedText;
            replacedText = replacedText.replace(regex, replacedValue);
            
            if (previousText !== replacedText) {
                console.log(`Replaced "${originalValue}" with "${replacedValue}"`);
            }
        });

        console.log('Final replaced text:', replacedText);
        return replacedText;

    } catch (error) {
        console.error('Error generating replaced text:', error);
        return originalText; // If an error occurs, return the original text
    }
}

  