let counter = 0;
let lock = false;

function log(message) {
  const logArea = document.getElementById('log');
  const entry = document.createElement('p');
  entry.textContent = message;
  logArea.appendChild(entry);
}

function updateCounterDisplay() {
  document.getElementById('counter').innerText = counter;
}

function acquireLock(threadName, callback) {
  const tryAcquire = () => {
    if (!lock) {
      lock = true;
      log(`${threadName} acquired lock`);
      callback(() => {
        lock = false;
        log(`${threadName} released lock`);
      });
    } else {
      log(`${threadName} waiting for lock...`);
      setTimeout(tryAcquire, 500); // Retry after 0.5s
    }
  };
  tryAcquire();
}

function thread(name) {
  acquireLock(name, (release) => {
    log(`${name} is accessing shared resource`);
    setTimeout(() => {
      counter++;
      updateCounterDisplay();
      log(`${name} incremented counter to ${counter}`);
      release();
    }, 1000); // simulate delay while using resource
  });
}

function startThreads() {
  log(`\n--- Starting threads ---`);
  thread("Thread A");
  thread("Thread B");
}
