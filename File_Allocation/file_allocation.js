let disk = [];
let totalBlocks = 20;
let isInitialized = false;

// Sequential
let currentStart = null;
let currentFileLength = 0;

// Indexed
let indexBlock = null;
let dataBlocks = [];

// Linked
let linkedList = [];

function switchAllocationType(element) {
  // Update visual state
  document.querySelectorAll('.allocation-type-option').forEach(el => {
    el.classList.remove('active');
  });
  element.classList.add('active');
  
  // Update hidden select
  const value = element.dataset.value;
  document.getElementById('allocationType').value = value;
  
  // Show/hide appropriate panels
  if (value === 'indexed') {
    document.getElementById('sequentialPanel').style.display = 'none';
    document.getElementById('indexedPanel').style.display = 'block';
  } else {
    document.getElementById('sequentialPanel').style.display = 'block';
    document.getElementById('indexedPanel').style.display = 'none';
  }
  
  // Call the handler
  onAllocationChange();
}

function onAllocationChange() {
  // Reset only main file allocation, not the other files
  resetMainFile();
  const type = document.getElementById("allocationType").value;
  setMessage(`Switched to ${type.charAt(0).toUpperCase() + type.slice(1)} allocation. Main file reset.`, 'info');
}

function getInputValues() {
  return {
    allocationType: document.getElementById("allocationType").value,
    totalBlocks: parseInt(document.getElementById("totalBlocks").value),
    startPosition: parseInt(document.getElementById("startPosition").value),
    initialLength: parseInt(document.getElementById("initialLength").value),
    growthSize: parseInt(document.getElementById("growthSize").value),
    indexBlock: parseInt(document.getElementById("indexBlock").value),
    dataBlocks: document.getElementById("dataBlocks").value
      .split(",")
      .map(s => parseInt(s.trim()))
      .filter(n => !isNaN(n)),
    otherFileBlocks: document.getElementById("otherFileBlocks").value
      .split(",")
      .map(s => parseInt(s.trim()))
      .filter(n => !isNaN(n))
  };
}

function setMessage(msg, type = 'success') {
  const messageEl = document.getElementById("message");
  messageEl.className = `message message-${type}`;
  
  let icon = 'info-circle';
  if (type === 'success') icon = 'check-circle';
  if (type === 'error') icon = 'exclamation-circle';
  
  messageEl.innerHTML = `<i class="fas fa-${icon}"></i><span>${msg}</span>`;
  
  // Animation effect
  messageEl.style.animation = 'none';
  setTimeout(() => {
    messageEl.style.animation = 'fadeIn 0.3s ease-in-out';
  }, 10);
}

function renderDisk() {
  const container = document.getElementById("diskGrid");
  container.innerHTML = "";
  
  if (disk.length === 0) {
    container.innerHTML = "<div style='grid-column: 1/-1; text-align:center; padding: 2rem;'>No disk initialized yet</div>";
    return;
  }
  
  disk.forEach((block, i) => {
    const div = document.createElement("div");
    if (i === indexBlock) {
      div.className = "block index-block";
      div.innerHTML = `<i class="fas fa-database"></i><br>${block.id}`;
    } else if (block.allocated && block.isOtherFile) {
      div.className = "block other-file";
      div.innerHTML = `<i class="fas fa-file-alt"></i><br>${block.id}`;
    } else if (block.allocated) {
      div.className = "block allocated";
      div.innerHTML = `<i class="fas fa-file-alt"></i><br>${block.id}`;
    } else {
      div.className = "block free";
      div.innerHTML = `<i class="fas fa-square"></i><br>${block.id}`;
    }
    container.appendChild(div);
  });
}

function checkContiguous(start, length) {
  if (start + length > totalBlocks) return false;
  for (let i = start; i < start + length; i++) {
    if (disk[i].allocated) return false;
  }
  return true;
}

function initializeDisk() {
  const { totalBlocks: tb } = getInputValues();
  if (tb <= 0) {
    setMessage("Please enter a valid number of blocks", "error");
    return;
  }

  totalBlocks = tb;
  disk = Array.from({ length: totalBlocks }, (_, i) => ({
    id: i,
    allocated: false,
    isOtherFile: false
  }));
  isInitialized = true;
  currentStart = null;
  currentFileLength = 0;
  indexBlock = null;
  dataBlocks = [];
  linkedList = [];
  renderDisk();
  setMessage(`Disk initialized with ${totalBlocks} blocks`, "success");
}

function allocateOtherFiles() {
  const { otherFileBlocks } = getInputValues();
  
  if (!isInitialized) {
    setMessage("Please initialize the disk first", "error");
    return;
  }
  
  // Validate blocks
  for (let blockId of otherFileBlocks) {
    if (blockId < 0 || blockId >= totalBlocks) {
      setMessage(`Block ${blockId} is out of range`, "error");
      return;
    }
    if (disk[blockId].allocated) {
      setMessage(`Block ${blockId} is already allocated`, "error");
      return;
    }
  }
  
  // Allocate blocks for other files
  for (let blockId of otherFileBlocks) {
    disk[blockId].allocated = true;
    disk[blockId].isOtherFile = true;
  }
  
  renderDisk();
  setMessage(`Allocated ${otherFileBlocks.length} blocks for other files: [${otherFileBlocks.join(", ")}]`, "success");
}

function resetMainFile() {
  // Reset only the main file allocation, not other files
  if (isInitialized) {
    // Clear main file blocks
    disk = disk.map(block => {
      if (block.isOtherFile) return block; // Keep other files
      return { ...block, allocated: false }; // Reset main file blocks
    });
    
    currentStart = null;
    currentFileLength = 0;
    indexBlock = null;
    dataBlocks = [];
    linkedList = [];
    renderDisk();
  }
}

function allocateInitial() {
  const {
    allocationType,
    startPosition,
    initialLength,
    indexBlock: ib,
    dataBlocks: blocks
  } = getInputValues();

  if (!isInitialized) {
    setMessage("Please initialize the disk first", "error");
    return;
  }

  // Reset main file before allocation
  resetMainFile();

  if (allocationType === "sequential") {
    if (!checkContiguous(startPosition, initialLength)) {
      setMessage("Space already allocated or invalid block range", "error");
      return;
    }

    for (let i = startPosition; i < startPosition + initialLength; i++) {
      disk[i].allocated = true;
      disk[i].isOtherFile = false;
    }

    currentStart = startPosition;
    currentFileLength = initialLength;

    setMessage(`Sequential Allocation: Blocks ${startPosition} to ${startPosition + initialLength - 1}`, "success");
  } else if (allocationType === "indexed") {
    if (ib < 0 || ib >= totalBlocks || disk[ib].allocated) {
      return setMessage("Invalid or already allocated index block", "error");
    }

    for (let b of blocks) {
      if (b < 0 || b >= totalBlocks || disk[b].allocated || b === ib) {
        return setMessage(`Invalid or already allocated data block: ${b}`, "error");
      }
    }

    // Allocate index block
    disk[ib].allocated = true;
    disk[ib].isOtherFile = false;
    indexBlock = ib;

    // Allocate data blocks
    dataBlocks = [...blocks];
    for (let b of dataBlocks) {
      disk[b].allocated = true;
      disk[b].isOtherFile = false;
    }

    setMessage(`Indexed Allocation: Index Block ${ib} → [${dataBlocks.join(", ")}]`, "success");
  } else {
    // Linked Allocation - MODIFIED CODE HERE
    // Start from the given startPosition and find subsequent free blocks
    
    // First check if start position is valid
    if (startPosition < 0 || startPosition >= totalBlocks || disk[startPosition].allocated) {
      return setMessage(`Invalid or already allocated start block: ${startPosition}`, "error");
    }
    
    // Start building the linked list from startPosition
    linkedList = [startPosition];
    disk[startPosition].allocated = true;
    disk[startPosition].isOtherFile = false;
    
    // We need initialLength - 1 more blocks (since we already allocated the start block)
    let remainingBlocks = initialLength - 1;
    let currentIndex = startPosition;
    
    // Find remaining blocks by searching forward from the start position
    while (remainingBlocks > 0) {
      // Find the next available block starting from current position + 1
      let nextBlockFound = false;
      for (let i = (currentIndex + 1) % totalBlocks; i !== currentIndex; i = (i + 1) % totalBlocks) {
        if (!disk[i].allocated) {
          disk[i].allocated = true;
          disk[i].isOtherFile = false;
          linkedList.push(i);
          currentIndex = i;
          remainingBlocks--;
          nextBlockFound = true;
          break;
        }
      }
      
      // If we couldn't find another block, break out
      if (!nextBlockFound) {
        return setMessage(`Could only allocate ${initialLength - remainingBlocks} blocks for linked list starting at ${startPosition}`, "error");
      }
      
      // If we've allocated all required blocks, break out
      if (remainingBlocks === 0) {
        break;
      }
    }

    setMessage(`Linked Allocation: Block Chain → ${linkedList.join(" → ")}`, "success");
  }

  renderDisk();
}

function growFile() {
  const { allocationType, growthSize } = getInputValues();

  if (!isInitialized) {
    return setMessage("Please initialize the disk first", "error");
  }

  if (allocationType === "sequential") {
    if (currentStart === null) {
      return setMessage("File not allocated yet (sequential)", "error");
    }

    if (checkContiguous(currentStart + currentFileLength, growthSize)) {
      for (
        let i = currentStart + currentFileLength;
        i < currentStart + currentFileLength + growthSize;
        i++
      ) {
        disk[i].allocated = true;
        disk[i].isOtherFile = false;
      }
      currentFileLength += growthSize;
      renderDisk();
      return setMessage(`Growth successful to block ${currentStart + currentFileLength - 1}`, "success");
    }

    // Need to relocate the file
    let foundNewLocation = false;
    for (let i = 0; i <= totalBlocks - (currentFileLength + growthSize); i++) {
      if (checkContiguous(i, currentFileLength + growthSize)) {
        // Found a new location
        // First remove the current allocation
        for (let j = currentStart; j < currentStart + currentFileLength; j++) {
          if (!disk[j].isOtherFile) { // Make sure we don't clear other files
            disk[j].allocated = false;
          }
        }
        
        // Now allocate at the new location
        for (let j = i; j < i + currentFileLength + growthSize; j++) {
          disk[j].allocated = true;
          disk[j].isOtherFile = false;
        }
        
        currentStart = i;
        currentFileLength += growthSize;
        renderDisk();
        foundNewLocation = true;
        return setMessage(`Relocation successful: File now occupies blocks ${i} to ${i + currentFileLength - 1}`, "success");
      }
    }

    if (!foundNewLocation) {
      return setMessage("Growth failed: No suitable space available for relocation", "error");
    }
  } else if (allocationType === "indexed") {
    let newBlocks = [];
    for (let i = 0; i < totalBlocks && newBlocks.length < growthSize; i++) {
      if (!disk[i].allocated && i !== indexBlock) newBlocks.push(i);
    }

    if (newBlocks.length < growthSize) {
      return setMessage("Not enough free blocks for indexed allocation growth", "error");
    }

    for (let b of newBlocks) {
      disk[b].allocated = true;
      disk[b].isOtherFile = false;
      dataBlocks.push(b);
    }

    renderDisk();
    return setMessage(`Indexed Allocation: Index Block ${indexBlock} → [${dataBlocks.join(", ")}]`, "success");
  } else {
    // Linked allocation
    let available = disk.map((b, i) => b.allocated ? -1 : i).filter(i => i !== -1);
    if (available.length < growthSize) {
      return setMessage("Not enough free blocks for linked growth", "error");
    }

    let newLinks = available.slice(0, growthSize);
    for (let b of newLinks) {
      disk[b].allocated = true;
      disk[b].isOtherFile = false;
    }
    linkedList.push(...newLinks);

    renderDisk();
    return setMessage(`Linked Allocation Growth: Chain now → ${linkedList.join(" → ")}`, "success");
  }
}

function reset() {
  disk = [];
  currentStart = null;
  currentFileLength = 0;
  indexBlock = null;
  dataBlocks = [];
  linkedList = [];
  isInitialized = false;
  renderDisk();
  setMessage("Disk reset successfully", "info");
}

// Initialize with default message
document.addEventListener('DOMContentLoaded', function() {
  renderDisk();
});