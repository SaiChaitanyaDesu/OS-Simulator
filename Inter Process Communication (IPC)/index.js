// your code goes here
// Tab switching logic
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        // Deactivate all tabs and content
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        
        // Activate clicked tab
        tab.classList.add('active');
        const tabId = tab.getAttribute('data-tab');
        document.getElementById(tabId).classList.add('active');
    });
});

// Utility function to add log messages
function addLog(logId, message) {
    const log = document.getElementById(logId);
    const entry = document.createElement('div');
    entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    log.appendChild(entry);
    log.scrollTop = log.scrollHeight;
}

// Pipes Implementation
document.getElementById('send-pipe').addEventListener('click', () => {
    const input = document.getElementById('pipe-input');
    const data = input.value.trim();
    
    if (data) {
        // Add to process A log
        const processALog = document.getElementById('process-a-log');
        const sentMsg = document.createElement('div');
        sentMsg.className = 'message sent';
        sentMsg.textContent = data;
        processALog.appendChild(sentMsg);
        processALog.scrollTop = processALog.scrollHeight;
        
        // Log the action
        addLog('pipe-log', `Process A wrote data to pipe: "${data}"`);
        
        // Animate data transfer
        const packet = document.getElementById('data-packet');
        packet.style.left = '-20px';
        
        // Force reflow
        void packet.offsetWidth;
        
        // Start animation
        packet.style.left = '100%';
        
        // After animation completes, add to process B log
        setTimeout(() => {
            const processBLog = document.getElementById('process-b-log');
            const receivedMsg = document.createElement('div');
            receivedMsg.className = 'message received';
            receivedMsg.textContent = data;
            processBLog.appendChild(receivedMsg);
            processBLog.scrollTop = processBLog.scrollHeight;
            
            addLog('pipe-log', `Process B read data from pipe: "${data}"`);
        }, 1000);
        
        input.value = '';
    }
});

// Message Passing Implementation
document.getElementById('p1-send').addEventListener('click', () => {
    const messageInput = document.getElementById('p1-message');
    const message = messageInput.value.trim();
    
    if (message) {
        // Add to process 1 message box
        const p1Box = document.getElementById('p1-message-box');
        const msgElement = document.createElement('div');
        msgElement.className = 'message sent';
        msgElement.textContent = message;
        p1Box.appendChild(msgElement);
        p1Box.scrollTop = p1Box.scrollHeight;
        
        // Add to process 2 message box
        setTimeout(() => {
            const p2Box = document.getElementById('p2-message-box');
            const receivedMsg = document.createElement('div');
            receivedMsg.className = 'message received';
            receivedMsg.textContent = message;
            p2Box.appendChild(receivedMsg);
            p2Box.scrollTop = p2Box.scrollHeight;
            
            addLog('message-log', `Message sent from Process 1 to Process 2: "${message}"`);
        }, 500);
        
        messageInput.value = '';
    }
});

document.getElementById('p2-send').addEventListener('click', () => {
    const messageInput = document.getElementById('p2-message');
    const message = messageInput.value.trim();
    
    if (message) {
        // Add to process 2 message box
        const p2Box = document.getElementById('p2-message-box');
        const msgElement = document.createElement('div');
        msgElement.className = 'message sent';
        msgElement.textContent = message;
        p2Box.appendChild(msgElement);
        p2Box.scrollTop = p2Box.scrollHeight;
        
        // Add to process 1 message box
        setTimeout(() => {
            const p1Box = document.getElementById('p1-message-box');
            const receivedMsg = document.createElement('div');
            receivedMsg.className = 'message received';
            receivedMsg.textContent = message;
            p1Box.appendChild(receivedMsg);
            p1Box.scrollTop = p1Box.scrollHeight;
            
            addLog('message-log', `Message sent from Process 2 to Process 1: "${message}"`);
        }, 500);
        
        messageInput.value = '';
    }
});

// Shared Memory Implementation
document.getElementById('write-memory').addEventListener('click', () => {
    const index = document.getElementById('memory-index').value;
    const value = document.getElementById('memory-value').value.trim() || '0';
    
    if (value) {
        // Update memory cell
        const cell = document.getElementById(`cell-${index}`);
        cell.textContent = value;
        cell.style.backgroundColor = '#2d3b2d';
        
        setTimeout(() => {
            cell.style.backgroundColor = '#1a1a1a';
        }, 1000);
        
        // Log action in process X
        const processXLog = document.getElementById('process-x-log');
        const logEntry = document.createElement('div');
        logEntry.className = 'message';
        logEntry.textContent = `Wrote "${value}" to address ${index}`;
        processXLog.appendChild(logEntry);
        processXLog.scrollTop = processXLog.scrollHeight;
        
        addLog('shared-memory-log', `Process X wrote "${value}" to shared memory address ${index}`);
        
        document.getElementById('memory-value').value = '';
    }
});

document.getElementById('read-memory').addEventListener('click', () => {
    const index = document.getElementById('read-index').value;
    const cell = document.getElementById(`cell-${index}`);
    const value = cell.textContent;
    
    // Highlight cell being read
    cell.style.backgroundColor = '#2d333b';
    setTimeout(() => {
        cell.style.backgroundColor = '#1a1a1a';
    }, 1000);
    
    // Log action in process Y
    const processYLog = document.getElementById('process-y-log');
    const logEntry = document.createElement('div');
    logEntry.className = 'message';
    logEntry.textContent = `Read "${value}" from address ${index}`;
    processYLog.appendChild(logEntry);
    processYLog.scrollTop = processYLog.scrollHeight;
    
    addLog('shared-memory-log', `Process Y read "${value}" from shared memory address ${index}`);
});

// Semaphores Implementation
let semaphoreOwner = null;

function updateSemaphoreStatus() {
    const light = document.getElementById('semaphore-light');
    const status = document.getElementById('semaphore-status');
    const criticalSection = document.getElementById('critical-section');
    
    if (semaphoreOwner === null) {
        light.classList.remove('green');
        status.textContent = 'Available';
        criticalSection.textContent = 'Resource is currently not being used';
        criticalSection.style.backgroundColor = '#2a2a2a';
    } else {
        light.classList.add('green');
        status.textContent = `Locked by Process ${semaphoreOwner}`;
        criticalSection.textContent = `Process ${semaphoreOwner} is currently using this resource`;
        criticalSection.style.backgroundColor = semaphoreOwner === 1 ? '#2d3b2d' : '#2d333b';
    }
}

document.getElementById('p1-acquire').addEventListener('click', () => {
    if (semaphoreOwner === null) {
        semaphoreOwner = 1;
        updateSemaphoreStatus();
        
        document.getElementById('p1-acquire').disabled = true;
        document.getElementById('p1-release').disabled = false;
        document.getElementById('p2-acquire').disabled = true;
        
        const p1Log = document.getElementById('p1-sem-log');
        const logEntry = document.createElement('div');
        logEntry.className = 'message';
        logEntry.textContent = 'Acquired lock on the shared resource';
        p1Log.appendChild(logEntry);
        p1Log.scrollTop = p1Log.scrollHeight;
        
        addLog('semaphore-log', 'Process 1 acquired the semaphore lock');
    }
});

document.getElementById('p1-release').addEventListener('click', () => {
    if (semaphoreOwner === 1) {
        semaphoreOwner = null;
        updateSemaphoreStatus();
        
        document.getElementById('p1-acquire').disabled = false;
        document.getElementById('p1-release').disabled = true;
        document.getElementById('p2-acquire').disabled = false;
        
        const p1Log = document.getElementById('p1-sem-log');
        const logEntry = document.createElement('div');
        logEntry.className = 'message';
        logEntry.textContent = 'Released lock on the shared resource';
        p1Log.appendChild(logEntry);
        p1Log.scrollTop = p1Log.scrollHeight;
        
        addLog('semaphore-log', 'Process 1 released the semaphore lock');
    }
});

document.getElementById('p2-acquire').addEventListener('click', () => {
    if (semaphoreOwner === null) {
        semaphoreOwner = 2;
        updateSemaphoreStatus();
        
        document.getElementById('p2-acquire').disabled = true;
        document.getElementById('p2-release').disabled = false;
        document.getElementById('p1-acquire').disabled = true;
        
        const p2Log = document.getElementById('p2-sem-log');
        const logEntry = document.createElement('div');
        logEntry.className = 'message';
        logEntry.textContent = 'Acquired lock on the shared resource';
        p2Log.appendChild(logEntry);
        p2Log.scrollTop = p2Log.scrollHeight;
        
        addLog('semaphore-log', 'Process 2 acquired the semaphore lock');
    }
});

document.getElementById('p2-release').addEventListener('click', () => {
    if (semaphoreOwner === 2) {
        semaphoreOwner = null;
        updateSemaphoreStatus();
        
        document.getElementById('p2-acquire').disabled = false;
        document.getElementById('p2-release').disabled = true;
        document.getElementById('p1-acquire').disabled = false;
        
        const p2Log = document.getElementById('p2-sem-log');
        const logEntry = document.createElement('div');
        logEntry.className = 'message';
        logEntry.textContent = 'Released lock on the shared resource';
        p2Log.appendChild(logEntry);
        p2Log.scrollTop = p2Log.scrollHeight;
        
        addLog('semaphore-log', 'Process 2 released the semaphore lock');
    }
});

// Message Queues Implementation
// Message Queues Implementation
const messageQueue = [];
let autoConsumeInterval = null;

document.getElementById('enqueue').addEventListener('click', () => {
    const message = document.getElementById('queue-message').value.trim();
    const priority = parseInt(document.getElementById('message-priority').value);
    
    if (message) {
        // Create message object
        const msgObj = {
            id: Date.now(),
            text: message,
            priority: priority,
            timestamp: new Date().toLocaleTimeString()
        };
        
        // Add to queue
        messageQueue.push(msgObj);
        
        // Sort by priority (higher numbers come first)
        messageQueue.sort((a, b) => b.priority - a.priority);
        
        updateQueueDisplay();
        
        // Log in producer process
        const producerLog = document.getElementById('producer-log');
        const logEntry = document.createElement('div');
        logEntry.className = 'message sent';
        logEntry.textContent = `Sent: "${message}" (Priority: ${priority})`;
        producerLog.appendChild(logEntry);
        producerLog.scrollTop = producerLog.scrollHeight;
        
        addLog('queue-log', `Producer added message to queue: "${message}" with priority ${priority}`);
        
        document.getElementById('queue-message').value = '';
    }
});

document.getElementById('dequeue').addEventListener('click', () => {
    if (messageQueue.length > 0) {
        const msg = messageQueue.shift();
        updateQueueDisplay();
        
        // Log in consumer process
        const consumerLog = document.getElementById('consumer-log');
        const logEntry = document.createElement('div');
        logEntry.className = 'message received';
        logEntry.textContent = `Received: "${msg.text}" (Priority: ${msg.priority})`;
        consumerLog.appendChild(logEntry);
        consumerLog.scrollTop = consumerLog.scrollHeight;
        
        addLog('queue-log', `Consumer received message from queue: "${msg.text}"`);
    } else {
        addLog('queue-log', 'Consumer attempted to receive message, but queue is empty');
    }
});

// Auto-consume functionality
document.getElementById('auto-consume').addEventListener('change', function() {
    if (this.checked) {
        autoConsumeInterval = setInterval(() => {
            if (messageQueue.length > 0) {
                document.getElementById('dequeue').click();
            }
        }, 2000);
        
        addLog('queue-log', 'Auto-consume enabled');
    } else {
        clearInterval(autoConsumeInterval);
        addLog('queue-log', 'Auto-consume disabled');
    }
});

function updateQueueDisplay() {
    const queueElement = document.getElementById('message-queue');
    const queueCount = document.getElementById('queue-count');
    
    queueElement.innerHTML = '';
    queueCount.textContent = `(${messageQueue.length})`;
    
    messageQueue.forEach(msg => {
        const mailElement = document.createElement('div');
        mailElement.className = 'mail';
        let priorityLabel = '';
        
        switch(msg.priority) {
            case 1:
                priorityLabel = 'Low';
                break;
            case 2:
                priorityLabel = 'Medium';
                break;
            case 3:
                priorityLabel = 'High';
                break;
            default:
                priorityLabel = 'Unknown';
        }
        
        mailElement.textContent = `[${msg.timestamp}] (${priorityLabel}) ${msg.text}`;
        queueElement.appendChild(mailElement);
    });
}

// Initialize semaphore status on page load
updateSemaphoreStatus();