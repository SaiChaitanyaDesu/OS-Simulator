        // DOM Elements
        const algorithmSelect = document.getElementById('algorithm');
        const frameCountInput = document.getElementById('frame-count');
        const referenceStringInput = document.getElementById('reference-string');
        const modifiedBitsInput = document.getElementById('modified-bits');
        const modifiedBitContainer = document.getElementById('modified-bit-container');
        const errorMessage = document.getElementById('error-message');
        const initializeBtn = document.getElementById('initialize-btn');
        const resetBtn = document.getElementById('reset-btn');
        const stepBtn = document.getElementById('step-btn');
        const simulationContainer = document.getElementById('simulation-container');
        const pageFramesContainer = document.getElementById('page-frames');
        const statsContainer = document.getElementById('stats');
        const stepInfo = document.getElementById('step-info');

        // Simulation state
        let simulationState = {
            algorithm: 'second-chance',
            frameCount: 3,
            referenceString: [],
            modifiedBits: [],
            currentStep: 0,
            frames: [], // Will store page numbers
            referenceBits: [], // For second chance
            modifiedFrameBits: [], // For enhanced second chance
            pointer: 0,
            hits: 0,
            misses: 0
        };

        // Event Listeners
        algorithmSelect.addEventListener('change', function() {
            const algorithm = algorithmSelect.value;
            if (algorithm === 'enhanced-second-chance') {
                modifiedBitContainer.style.display = 'block';
            } else {
                modifiedBitContainer.style.display = 'none';
            }
        });

        initializeBtn.addEventListener('click', initializeSimulation);
        resetBtn.addEventListener('click', resetSimulation);
        stepBtn.addEventListener('click', stepSimulation);

        // Functions
        function initializeSimulation() {
            // Get inputs
            const algorithm = algorithmSelect.value;
            const frameCount = parseInt(frameCountInput.value);
            const referenceString = referenceStringInput.value.split(',').map(val => val.trim()).filter(val => val !== '');
            const modifiedBits = modifiedBitsInput.value.split(',').map(val => parseInt(val.trim())).filter(val => val === 0 || val === 1);
            
            // Validation
            errorMessage.textContent = '';
            errorMessage.style.display = 'none';
            
            if (frameCount < 1 || frameCount > 10) {
                errorMessage.textContent = 'Number of frames must be between 1 and 10';
                errorMessage.style.display = 'block';
                return;
            }
            
            if (referenceString.length === 0) {
                errorMessage.textContent = 'Reference string cannot be empty';
                errorMessage.style.display = 'block';
                return;
            }
            
            // Check if all reference string values are valid
            if (!referenceString.every(val => !isNaN(parseInt(val)))) {
                errorMessage.textContent = 'Reference string must contain only numbers';
                errorMessage.style.display = 'block';
                return;
            }
            
            // Check modified bits for enhanced second chance
            if (algorithm === 'enhanced-second-chance') {
                if (modifiedBits.length === 0) {
                    errorMessage.textContent = 'Modified bits string cannot be empty for Enhanced Second Chance';
                    errorMessage.style.display = 'block';
                    return;
                }
                
                if (modifiedBits.length !== referenceString.length) {
                    errorMessage.textContent = 'Modified bits must have the same length as reference string';
                    errorMessage.style.display = 'block';
                    return;
                }
            }
            
            // Initialize simulation state
            simulationState = {
                algorithm,
                frameCount,
                referenceString: referenceString.map(val => parseInt(val)),
                modifiedBits: algorithm === 'enhanced-second-chance' ? modifiedBits : Array(referenceString.length).fill(0),
                currentStep: 0,
                frames: Array(frameCount).fill(null),
                referenceBits: Array(frameCount).fill(0),
                modifiedFrameBits: Array(frameCount).fill(0),
                pointer: 0,
                hits: 0,
                misses: 0
            };
            
            // Update the UI
            updateUI();
            
            // Show simulation container
            simulationContainer.style.display = 'block';
            resetBtn.disabled = false;
            initializeBtn.disabled = true;
            
            // Disable inputs
            algorithmSelect.disabled = true;
            frameCountInput.disabled = true;
            referenceStringInput.disabled = true;
            modifiedBitsInput.disabled = true;
            
            // Enable step button
            stepBtn.disabled = false;
            
            // Create frames
            createFrames();
            
            // Update stats
            updateStats();
            
            stepInfo.textContent = 'Simulation initialized. Click Step to begin.';
        }

        function resetSimulation() {
            // Re-enable inputs
            algorithmSelect.disabled = false;
            frameCountInput.disabled = false;
            referenceStringInput.disabled = false;
            modifiedBitsInput.disabled = false;
            
            // Hide simulation container
            simulationContainer.style.display = 'none';
            resetBtn.disabled = true;
            initializeBtn.disabled = false;
            
            // Clear error message
            errorMessage.textContent = '';
            errorMessage.style.display = 'none';
        }

        function createFrames() {
            pageFramesContainer.innerHTML = '';
            
            for (let i = 0; i < simulationState.frameCount; i++) {
                const frameDiv = document.createElement('div');
                frameDiv.className = 'frame';
                if (i === simulationState.pointer) {
                    frameDiv.className += ' pointer';
                }
                
                const titleDiv = document.createElement('div');
                titleDiv.className = 'frame-title';
                titleDiv.innerHTML = `<i class="fas fa-memory"></i> Frame ${i}`;
                
                const contentDiv = document.createElement('div');
                contentDiv.className = 'frame-content';
                contentDiv.textContent = simulationState.frames[i] !== null ? simulationState.frames[i] : '-';
                
                const bitDisplay = document.createElement('div');
                bitDisplay.className = 'bit-display';
                
                const refBit = document.createElement('div');
                refBit.className = 'bit';
                refBit.innerHTML = `R:${simulationState.referenceBits[i]}`;
                bitDisplay.appendChild(refBit);
                
                if (simulationState.algorithm === 'enhanced-second-chance') {
                    const modBit = document.createElement('div');
                    modBit.className = 'bit';
                    modBit.innerHTML = `M:${simulationState.modifiedFrameBits[i]}`;
                    bitDisplay.appendChild(modBit);
                }
                
                frameDiv.appendChild(titleDiv);
                frameDiv.appendChild(contentDiv);
                frameDiv.appendChild(bitDisplay);
                pageFramesContainer.appendChild(frameDiv);
            }
        }

        function updateStats() {
            document.getElementById('current-reference').textContent = simulationState.currentStep;
            document.getElementById('total-references').textContent = simulationState.referenceString.length;
            document.getElementById('current-page').textContent = 
                simulationState.currentStep < simulationState.referenceString.length ? 
                simulationState.referenceString[simulationState.currentStep] : '-';
            document.getElementById('hits').textContent = simulationState.hits;
            document.getElementById('misses').textContent = simulationState.misses;
            document.getElementById('hit-ratio').textContent = 
                simulationState.currentStep > 0 ? 
                `${Math.round((simulationState.hits / simulationState.currentStep) * 100)}%` : '0%';
            document.getElementById('pointer-position').textContent = simulationState.pointer;
        }

        function updateUI() {
            createFrames();
            updateStats();
        }

        function stepSimulation() {
            if (simulationState.currentStep >= simulationState.referenceString.length) {
                stepBtn.disabled = true;
                stepInfo.innerHTML = '<i class="fas fa-check-circle"></i> Simulation complete!';
                return;
            }
            
            const page = simulationState.referenceString[simulationState.currentStep];
            const modifiedBit = simulationState.modifiedBits[simulationState.currentStep];
            let status = 'Miss';
            let action = '';
            
            // Check if page is already in frames
            const frameIndex = simulationState.frames.indexOf(page);
            
            if (frameIndex !== -1) {
                // Page hit
                status = 'Hit';
                simulationState.hits++;
                simulationState.referenceBits[frameIndex] = 1;
                
                if (simulationState.algorithm === 'enhanced-second-chance' && modifiedBit === 1) {
                    simulationState.modifiedFrameBits[frameIndex] = 1;
                }
                
                action = `Set reference bit to 1 for page ${page} in frame ${frameIndex}`;
                stepInfo.innerHTML = `Page ${page} is already in frame ${frameIndex}. Setting reference bit to 1. <span class="hit-indicator"><i class="fas fa-check-circle"></i> Hit</span>`;
            } else {
                // Page miss
                simulationState.misses++;
                
                // Check if there's an empty frame
                const emptyFrameIndex = simulationState.frames.indexOf(null);
                
                if (emptyFrameIndex !== -1) {
                    // Add to empty frame
                    simulationState.frames[emptyFrameIndex] = page;
                    simulationState.referenceBits[emptyFrameIndex] = 1;
                    
                    if (simulationState.algorithm === 'enhanced-second-chance' && modifiedBit === 1) {
                        simulationState.modifiedFrameBits[emptyFrameIndex] = 1;
                    } else if (simulationState.algorithm === 'enhanced-second-chance') {
                        simulationState.modifiedFrameBits[emptyFrameIndex] = 0;
                    }
                    
                    action = `Placed page ${page} in empty frame ${emptyFrameIndex}`;
                    stepInfo.innerHTML = `Page ${page} placed in empty frame ${emptyFrameIndex}. <span class="miss-indicator"><i class="fas fa-times-circle"></i> Miss</span>`;
                } else {
                    // Need to replace a page
                    if (simulationState.algorithm === 'second-chance') {
                        // Second Chance Algorithm
                        let loopCount = 0;
                        while (true) {
                            // If the current page has a reference bit of 1, give it a second chance
                            if (simulationState.referenceBits[simulationState.pointer] === 1) {
                                simulationState.referenceBits[simulationState.pointer] = 0;
                                simulationState.pointer = (simulationState.pointer + 1) % simulationState.frameCount;
                                action += `Frame ${simulationState.pointer-1 >= 0 ? simulationState.pointer-1 : simulationState.frameCount-1} has reference bit 1, setting to 0 and moving pointer. `;
                                loopCount++;
                                if (loopCount >= simulationState.frameCount * 2) {
                                    // Safety check to prevent infinite loop
                                    break;
                                }
                            } else {
                                // Found a victim
                                const victimPage = simulationState.frames[simulationState.pointer];
                                simulationState.frames[simulationState.pointer] = page;
                                simulationState.referenceBits[simulationState.pointer] = 1;
                                
                                action += `Replaced page ${victimPage} in frame ${simulationState.pointer} with page ${page}`;
                                stepInfo.innerHTML = `Replaced page ${victimPage} in frame ${simulationState.pointer} with page ${page}. <span class="miss-indicator"><i class="fas fa-times-circle"></i> Miss</span>`;
                                
                                // Move pointer for next replacement
                                simulationState.pointer = (simulationState.pointer + 1) % simulationState.frameCount;
                                break;
                            }
                        }
                    } else {
                        // Enhanced Second Chance Algorithm
                        let found = false;
                        // First pass: look for (0,0) - not referenced, not modified
                        for (let i = 0; i < simulationState.frameCount && !found; i++) {
                            const checkIndex = (simulationState.pointer + i) % simulationState.frameCount;
                            if (simulationState.referenceBits[checkIndex] === 0 && simulationState.modifiedFrameBits[checkIndex] === 0) {
                                const victimPage = simulationState.frames[checkIndex];
                                simulationState.frames[checkIndex] = page;
                                simulationState.referenceBits[checkIndex] = 1;
                                simulationState.modifiedFrameBits[checkIndex] = modifiedBit;
                                
                                action = `Found (0,0) in frame ${checkIndex}, replaced page ${victimPage} with page ${page}`;
                                stepInfo.innerHTML = `Found (0,0) in frame ${checkIndex}, replaced page ${victimPage} with page ${page}. <span class="miss-indicator"><i class="fas fa-times-circle"></i> Miss</span>`;
                                
                                simulationState.pointer = (checkIndex + 1) % simulationState.frameCount;
                                found = true;
                            }
                        }
                        
                        // Second pass: look for (0,1) - not referenced, modified
                        if (!found) {
                            for (let i = 0; i < simulationState.frameCount && !found; i++) {
                                const checkIndex = (simulationState.pointer + i) % simulationState.frameCount;
                                if (simulationState.referenceBits[checkIndex] === 0 && simulationState.modifiedFrameBits[checkIndex] === 1) {
                                    const victimPage = simulationState.frames[checkIndex];
                                    simulationState.frames[checkIndex] = page;
                                    simulationState.referenceBits[checkIndex] = 1;
                                    simulationState.modifiedFrameBits[checkIndex] = modifiedBit;
                                    
                                    action = `Found (0,1) in frame ${checkIndex}, replaced page ${victimPage} with page ${page}`;
                                    stepInfo.innerHTML = `Found (0,1) in frame ${checkIndex}, replaced page ${victimPage} with page ${page}. <span class="miss-indicator"><i class="fas fa-times-circle"></i> Miss</span>`;
                                    
                                    simulationState.pointer = (checkIndex + 1) % simulationState.frameCount;
                                    found = true;
                                }
                            }
                        }
                        
                        // Third pass: look for (1,0) - referenced, not modified
                        // but first clear reference bits and look again
                        if (!found) {
                            for (let i = 0; i < simulationState.frameCount; i++) {
                                simulationState.referenceBits[i] = 0;
                            }
                            action += "Cleared all reference bits. ";
                            
                            for (let i = 0; i < simulationState.frameCount && !found; i++) {
                                const checkIndex = (simulationState.pointer + i) % simulationState.frameCount;
                                if (simulationState.modifiedFrameBits[checkIndex] === 0) {
                                    const victimPage = simulationState.frames[checkIndex];
                                    simulationState.frames[checkIndex] = page;
                                    simulationState.referenceBits[checkIndex] = 1;
                                    simulationState.modifiedFrameBits[checkIndex] = modifiedBit;
                                    
                                    action += `Found (1,0) in frame ${checkIndex}, replaced page ${victimPage} with page ${page}`;
                                    stepInfo.innerHTML = `Found (1,0) in frame ${checkIndex} after clearing reference bits, replaced page ${victimPage} with page ${page}. <span class="miss-indicator"><i class="fas fa-times-circle"></i> Miss</span>`;
                                    
                                    simulationState.pointer = (checkIndex + 1) % simulationState.frameCount;
                                    found = true;
                                }
                            }
                        }
                        
                        // Fourth pass: look for (1,1) - referenced, modified
                        // Reference bits already cleared in previous pass
                        if (!found) {
                            const checkIndex = simulationState.pointer;
                            const victimPage = simulationState.frames[checkIndex];
                            simulationState.frames[checkIndex] = page;
                            simulationState.referenceBits[checkIndex] = 1;
                            simulationState.modifiedFrameBits[checkIndex] = modifiedBit;
                            
                            action += `Found (1,1) in frame ${checkIndex}, replaced page ${victimPage} with page ${page}`;
                            stepInfo.innerHTML = `Found (1,1) in frame ${checkIndex} after clearing reference bits, replaced page ${victimPage} with page ${page}. <span class="miss-indicator"><i class="fas fa-times-circle"></i> Miss</span>`;
                            
                            simulationState.pointer = (checkIndex + 1) % simulationState.frameCount;
                        }
                    }
                }
            }
            
            // Add visual effect to show which frame was changed
            setTimeout(() => {
                const frames = document.querySelectorAll('.frame');
                if (frameIndex !== -1) {
                    frames[frameIndex].classList.add('pulse');
                    setTimeout(() => frames[frameIndex].classList.remove('pulse'), 500);
                } else if (simulationState.frames.indexOf(page) !== -1) {
                    const newFrameIndex = simulationState.frames.indexOf(page);
                    frames[newFrameIndex].classList.add('pulse');
                    setTimeout(() => frames[newFrameIndex].classList.remove('pulse'), 500);
                }
            }, 50);
            
            // Increment step
            simulationState.currentStep++;
            
            // Update UI
            updateUI();
        }

        window.addEventListener('scroll', function() {
            const navbar = document.querySelector('.navbar');
            if (window.scrollY > 10) {
              navbar.classList.add('scrolled');
            } else {
              navbar.classList.remove('scrolled');
            }
        });