const chatContainer = document.getElementById('chatContainer');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');

let pageData = null;
let isYouTube = false;
let videoId = null;
let sessionId = null;
let port = null;

const BASE_URL = 'http://localhost:5000';
const YOUTUBE_INIT_API = `${BASE_URL}/youtube`;
const PAGE_INIT_API = `${BASE_URL}/page`;
const ASK_API = `${BASE_URL}/ask`;

async function init() {
  port = chrome.runtime.connect({ name: 'popup' });
  
  addMessage('system', 'Loading page content...');
  
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (tab.url.includes('youtube.com/watch')) {
      isYouTube = true;
      videoId = extractYouTubeId(tab.url);
      
      const response = await fetch(YOUTUBE_INIT_API, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ videoId: videoId })
      });
      
      const data = await response.json();
      sessionId = data.sessionId;
      
      chrome.runtime.sendMessage({
        type: 'REGISTER_SESSION',
        sessionId: sessionId
      });
      
      addMessage('system', `YouTube video detected: ${videoId}`);
    } else {
      const [result] = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        function: getPageContent
      });
      pageData = result.result;
      
      const response = await fetch(PAGE_INIT_API, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pageData: pageData })
      });
      
      const data = await response.json();
      sessionId = data.sessionId;
      

      chrome.runtime.sendMessage({
        type: 'REGISTER_SESSION',
        sessionId: sessionId
      });
      
      addMessage('system', 'Page content loaded successfully!');
    }
    
    addMessage('assistant', 'Hi! I\'m ready to help. What would you like to know?');
  } catch (error) {
    addMessage('system', 'Error loading content: ' + error.message);
  }
}

function extractYouTubeId(url) {
  const match = url.match(/[?&]v=([^&]+)/);
  return match ? match[1] : null;
}

function getPageContent() {
  return {
    title: document.title,
    url: window.location.href,
    content: document.body.innerText,
    description: document.querySelector('meta[name="description"]')?.content || ''
  };
}

function addMessage(type, text) {
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${type}`;
  
  const contentDiv = document.createElement('div');
  contentDiv.className = 'message-content';
  contentDiv.textContent = text;
  
  messageDiv.appendChild(contentDiv);
  chatContainer.appendChild(messageDiv);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

function showTyping() {
  const typingDiv = document.createElement('div');
  typingDiv.className = 'message assistant';
  typingDiv.id = 'typing';
  
  const contentDiv = document.createElement('div');
  contentDiv.className = 'message-content';
  contentDiv.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
  
  typingDiv.appendChild(contentDiv);
  chatContainer.appendChild(typingDiv);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

function removeTyping() {
  const typing = document.getElementById('typing');
  if (typing) typing.remove();
}

async function sendMessage() {
  const message = messageInput.value.trim();
  if (!message) return;

  addMessage('user', message);
  messageInput.value = '';
  sendBtn.disabled = true;
  
  showTyping();

  try {
    const response = await fetch(ASK_API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sessionId: sessionId,
        message: message
      })
    });

    const data = await response.json();
    removeTyping();
    
    const reply = data.reply || data.message || 'No response received';
    addMessage('assistant', reply);
    
  } catch (error) {
    removeTyping();
    addMessage('system', 'Error: ' + error.message);
  }
  
  sendBtn.disabled = false;
}

sendBtn.addEventListener('click', sendMessage);
messageInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') sendMessage();
});

init();