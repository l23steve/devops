const ws = new WebSocket(`ws://${location.host}/ws`);
const chatInput = document.getElementById('chat-input');
const chatLog = document.getElementById('chat-log');
const terminalLog = document.getElementById('terminal-log');

ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.type === 'chat_message') {
        const p = document.createElement('p');
        p.textContent = msg.content;
        chatLog.appendChild(p);
        chatLog.scrollTop = chatLog.scrollHeight;
    } else if (msg.type === 'terminal_data') {
        terminalLog.textContent += msg.content;
        terminalLog.scrollTop = terminalLog.scrollHeight;
    }
};

chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        const text = chatInput.value;
        ws.send(JSON.stringify({type: 'chat_message', content: text}));
        chatInput.value = '';
    }
});
