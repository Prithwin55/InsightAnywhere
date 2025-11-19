const BASE_URL = 'http://localhost:5000';

const activeSessions = new Map();

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'REGISTER_SESSION') {
    activeSessions.set(message.sessionId, Date.now());
    console.log('Session registered:', message.sessionId);
    sendResponse({ success: true });
  }
  
  if (message.type === 'CLEAR_SESSION') {
    clearSession(message.sessionId);
    sendResponse({ success: true });
  }
  
  return true;
});

chrome.runtime.onConnect.addListener((port) => {
  console.log('Popup connected');
  
  port.onDisconnect.addListener(() => {
    console.log('Popup disconnected - clearing sessions');
    
    activeSessions.forEach((timestamp, sessionId) => {
      clearSession(sessionId);
    });
    
    activeSessions.clear();
  });
});

async function clearSession(sessionId) {
  if (!sessionId) return;
  
  try {
    const response = await fetch(`${BASE_URL}/clear/${sessionId}`, {
      method: 'DELETE'
    });
    
    if (response.ok) {
      console.log('Session cleared successfully:', sessionId);
      activeSessions.delete(sessionId);
    } else {
      console.error(' Failed to clear session:', sessionId);
    }
  } catch (error) {
    console.error(' Error clearing session:', sessionId, error);
  }
}