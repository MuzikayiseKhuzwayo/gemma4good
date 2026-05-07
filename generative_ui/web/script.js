const feed = document.getElementById('feed');
const input = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const closeBtn = document.getElementById('close-btn');

const viewHome = document.getElementById('view-home');
const viewIntent = document.getElementById('view-intent');
const homeClock = document.getElementById('home-clock-large');

function updateTime() {
    const now = new Date();
    let hours = now.getHours();
    let minutes = now.getMinutes();
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? hours : 12; 
    minutes = minutes < 10 ? '0' + minutes : minutes;
    
    const timeStr = `${hours}:${minutes}`;
    if(homeClock) homeClock.innerText = timeStr;
    
    document.querySelectorAll('.time').forEach(el => {
        el.innerText = timeStr;
    });
}
setInterval(updateTime, 1000);
updateTime();

// View Toggling
viewHome.addEventListener('click', () => {
    viewHome.classList.remove('active');
    viewIntent.classList.add('active');
    setTimeout(() => input.focus(), 500);
});

closeBtn.addEventListener('click', () => {
    viewIntent.classList.remove('active');
    viewHome.classList.add('active');
});

// Chat Logic
function addMessage(text, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'system'}`;
    
    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'bubble';
    
    const textP = document.createElement('p');
    textP.innerText = text;
    
    bubbleDiv.appendChild(textP);
    messageDiv.appendChild(bubbleDiv);
    
    feed.appendChild(messageDiv);
    feed.scrollTop = feed.scrollHeight;
}

async function simulateAOSResponse(intent) {
    // Show typing state
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system';
    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'bubble';
    const textP = document.createElement('p');
    textP.innerText = "Latent Kernel Reasoning...";
    bubbleDiv.appendChild(textP);
    messageDiv.appendChild(bubbleDiv);
    feed.appendChild(messageDiv);
    feed.scrollTop = feed.scrollHeight;

    try {
        const response = await fetch('http://127.0.0.1:8000/api/intent', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ intent: intent })
        });
        
        const data = await response.json();
        
        // Remove typing placeholder
        feed.removeChild(messageDiv);
        
        data.responses.forEach(resText => {
            addMessage(resText, false);
        });
        
    } catch (error) {
        feed.removeChild(messageDiv);
        addMessage("[AOS Connection Error] Could not reach the Latent Kernel backend.", false);
        console.error('Error:', error);
    }
}

function handleSend() {
    const text = input.value.trim();
    if (text) {
        addMessage(text, true);
        input.value = '';
        simulateAOSResponse(text);
    }
}

sendBtn.addEventListener('click', handleSend);
input.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        handleSend();
    }
});

async function loadHistory() {
    try {
        const response = await fetch('http://127.0.0.1:8000/api/history');
        const data = await response.json();
        
        if (data.history && data.history.length > 0) {
            // Keep the very first system message, clear the rest if any
            // Actually, we can just append to the feed
            data.history.forEach(msg => {
                addMessage(msg.text, msg.role === 'user');
            });
        }
    } catch (error) {
        console.error('Could not load history:', error);
    }
}

// Load history when the script runs
loadHistory();
