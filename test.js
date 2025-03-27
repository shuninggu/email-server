import readline from 'readline';
import fetch from 'node-fetch';

// 创建命令行接口
const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

// 调用 Ollama API 的函数
async function askLlama(input) {
    try {
        const response = await fetch('http://localhost:11434/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                model: "llama2",
                prompt: input,
                stream: false
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data.response;
    } catch (error) {
        console.error('Error calling Llama:', error);
        return 'Sorry, I encountered an error.';
    }
}

// 主聊天循环
async function chat() {
    console.log('Welcome to Llama Chat! (Type "exit" to quit)');
    
    while (true) {
        const input = await new Promise(resolve => {
            rl.question('You: ', resolve);
        });

        // 检查是否退出
        if (input.toLowerCase() === 'exit') {
            console.log('Goodbye!');
            rl.close();
            break;
        }

        // 获取 Llama 的响应
        const response = await askLlama(input);
        console.log('\nLlama:', response, '\n');
    }
}

// 启动聊天
chat();