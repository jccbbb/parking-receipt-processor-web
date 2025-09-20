// DOM Elements
const fileInput = document.getElementById('fileInput');
const fileName = document.getElementById('fileName');
const processBtn = document.getElementById('processBtn');
const uploadSection = document.getElementById('uploadSection');
const processingSection = document.getElementById('processingSection');
const resultsSection = document.getElementById('resultsSection');
const errorSection = document.getElementById('errorSection');
const processingMessage = document.getElementById('processingMessage');
const progressFill = document.getElementById('progressFill');
const errorMessage = document.getElementById('errorMessage');
const downloadPdfBtn = document.getElementById('downloadPdfBtn');
const downloadSummaryBtn = document.getElementById('downloadSummaryBtn');
const processAnotherBtn = document.getElementById('processAnotherBtn');
const tryAgainBtn = document.getElementById('tryAgainBtn');

let currentSessionId = null;

// File input change handler
fileInput.addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        fileName.textContent = `Selected: ${file.name}`;
        processBtn.disabled = false;
    } else {
        fileName.textContent = '';
        processBtn.disabled = true;
    }
});

// Process button click handler
processBtn.addEventListener('click', async function() {
    const file = fileInput.files[0];
    if (!file) return;

    // Show processing section
    uploadSection.classList.add('hidden');
    processingSection.classList.remove('hidden');
    resultsSection.classList.add('hidden');
    errorSection.classList.add('hidden');

    // Reset progress
    progressFill.style.width = '0%';
    processingMessage.textContent = 'Uploading file...';

    try {
        // Upload file
        const formData = new FormData();
        formData.append('pdf_file', file);

        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Upload failed');
        }

        currentSessionId = data.session_id;

        // Poll for status
        pollStatus();

    } catch (error) {
        showError(error.message);
    }
});

// Poll for processing status
async function pollStatus() {
    if (!currentSessionId) return;

    try {
        const response = await fetch(`/status/${currentSessionId}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Status check failed');
        }

        // Update progress
        if (data.total > 0) {
            const progress = (data.progress / data.total) * 100;
            progressFill.style.width = `${progress}%`;
        }
        processingMessage.textContent = data.message || 'Processing...';

        if (data.status === 'completed') {
            showResults(data.summary);
        } else if (data.status === 'error') {
            showError(data.message || 'Processing failed');
        } else {
            // Continue polling
            setTimeout(pollStatus, 500);
        }

    } catch (error) {
        showError(error.message);
    }
}

// Show results
function showResults(summary) {
    processingSection.classList.add('hidden');
    resultsSection.classList.remove('hidden');

    // Update stats
    document.getElementById('totalReceipts').textContent = summary.total_receipts;
    document.getElementById('uniqueReceipts').textContent = summary.unique_receipts;
    document.getElementById('duplicatesRemoved').textContent = summary.duplicate_count;
    document.getElementById('totalAmount').textContent = summary.formatted_amount;

    // Show duplicates if any
    const duplicatesList = document.getElementById('duplicatesList');
    const duplicatesContent = document.getElementById('duplicatesContent');

    if (Object.keys(summary.duplicates).length > 0) {
        duplicatesList.classList.remove('hidden');
        duplicatesContent.innerHTML = '';

        for (const [ticket, count] of Object.entries(summary.duplicates)) {
            const li = document.createElement('li');
            li.textContent = `Ticket ${ticket} (${count} instances)`;
            duplicatesContent.appendChild(li);
        }
    } else {
        duplicatesList.classList.add('hidden');
    }
}

// Show error
function showError(message) {
    uploadSection.classList.add('hidden');
    processingSection.classList.add('hidden');
    resultsSection.classList.add('hidden');
    errorSection.classList.remove('hidden');
    errorMessage.textContent = message;
}

// Download handlers
downloadPdfBtn.addEventListener('click', async function() {
    if (!currentSessionId) return;
    downloadFile('pdf');
});

downloadSummaryBtn.addEventListener('click', async function() {
    if (!currentSessionId) return;
    downloadFile('summary');
});

async function downloadFile(type) {
    try {
        const response = await fetch(`/download/${currentSessionId}/${type}`);

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || 'Download failed');
        }

        // Get the blob from response
        const blob = await response.blob();

        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = type === 'pdf' ? 'processed_receipts.pdf' : 'summary.txt';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

    } catch (error) {
        alert(`Download failed: ${error.message}`);
    }
}

// Process another file
processAnotherBtn.addEventListener('click', async function() {
    // Clean up current session
    if (currentSessionId) {
        await fetch(`/cleanup/${currentSessionId}`, {
            method: 'POST'
        });
    }

    // Reset UI
    currentSessionId = null;
    fileInput.value = '';
    fileName.textContent = '';
    processBtn.disabled = true;

    uploadSection.classList.remove('hidden');
    processingSection.classList.add('hidden');
    resultsSection.classList.add('hidden');
    errorSection.classList.add('hidden');
});

// Try again after error
tryAgainBtn.addEventListener('click', function() {
    currentSessionId = null;
    fileInput.value = '';
    fileName.textContent = '';
    processBtn.disabled = true;

    uploadSection.classList.remove('hidden');
    processingSection.classList.add('hidden');
    resultsSection.classList.add('hidden');
    errorSection.classList.add('hidden');
});