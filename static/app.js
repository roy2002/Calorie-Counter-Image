// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const previewContainer = document.getElementById('previewContainer');
const imagePreview = document.getElementById('imagePreview');
const analyzeBtn = document.getElementById('analyzeBtn');
const loading = document.getElementById('loading');
const resultContainer = document.getElementById('resultContainer');
const resultBox = document.getElementById('resultBox');
const resetBtn = document.getElementById('resetBtn');
const showEditBtn = document.getElementById('showEditBtn');
const editSection = document.getElementById('editSection');
const editTextarea = document.getElementById('editTextarea');
const reanalyzeBtn = document.getElementById('reanalyzeBtn');
const cancelEditBtn = document.getElementById('cancelEditBtn');
const clearDataBtn = document.getElementById('clearDataBtn');
const weeklyList = document.getElementById('weeklyList');

let selectedFile = null;
let currentEntryId = null;  // Store the current entry ID

// Load weekly summary
async function loadWeeklySummary() {
    try {
        const response = await fetch('/weekly-summary');
        const data = await response.json();
        
        if (data.success && data.data && data.data.length > 0) {
            const today = new Date().toISOString().split('T')[0];
            const daysOfWeek = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
            
            weeklyList.innerHTML = data.data.map(day => {
                const date = new Date(day.date + 'T00:00:00');
                const dayName = daysOfWeek[date.getDay()];
                const isToday = day.date === today;
                
                return `
                    <div class="week-item ${isToday ? 'today' : ''}">
                        <div class="week-date">${dayName}, ${day.date}</div>
                        <div class="week-calories">${day.total_calories} cal</div>
                        <div class="week-meals">${day.entry_count} meal${day.entry_count !== 1 ? 's' : ''}</div>
                    </div>
                `;
            }).join('');
        } else {
            weeklyList.innerHTML = '<div class="no-data">No data yet. Start tracking!</div>';
        }
    } catch (error) {
        console.error('Error loading weekly summary:', error);
        weeklyList.innerHTML = '<div class="no-data">Error loading data</div>';
    }
}

// Load daily stats on page load
async function loadDailyStats() {
    try {
        const response = await fetch('/daily-total');
        const data = await response.json();
        
        if (data.success && data.data) {
            document.getElementById('totalCalories').textContent = data.data.total_calories || 0;
            document.getElementById('entryCount').textContent = data.data.entry_count || 0;
        }
    } catch (error) {
        console.error('Error loading daily stats:', error);
    }
}

// Clear all data
clearDataBtn.addEventListener('click', async () => {
    if (!confirm('⚠️ Are you sure you want to clear ALL data? This cannot be undone!')) {
        return;
    }

    try {
        const response = await fetch('/clear-data', {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            alert('✅ All data cleared successfully!');
            // Reload the page to refresh all data
            location.reload();
        } else {
            alert('❌ Error: ' + (data.error || 'Failed to clear data'));
        }
    } catch (error) {
        alert('❌ Error: ' + error.message);
    }
});

// Click to upload
uploadArea.addEventListener('click', () => {
    fileInput.click();
});

// File selection
fileInput.addEventListener('change', (e) => {
    handleFile(e.target.files[0]);
});

// Drag and drop
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    handleFile(e.dataTransfer.files[0]);
});

function handleFile(file) {
    if (!file || !file.type.startsWith('image/')) {
        alert('Please select a valid image file');
        return;
    }

    selectedFile = file;
    
    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        imagePreview.src = e.target.result;
        uploadArea.style.display = 'none';
        previewContainer.style.display = 'block';
        resultContainer.style.display = 'none';
    };
    reader.readAsDataURL(file);
}

// Analyze button
analyzeBtn.addEventListener('click', async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('image', selectedFile);

    previewContainer.style.display = 'none';
    loading.style.display = 'block';
    resultContainer.style.display = 'none';

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        loading.style.display = 'none';
        resultContainer.style.display = 'block';

        if (data.success) {
            resultBox.className = 'result-box success';
            
            // Store the entry ID for future edits
            currentEntryId = data.entry_id;
            
            // Display analysis with calorie info
            let resultText = data.analysis;
            resultText += '\n\n━━━━━━━━━━━━━━━━━━━━━━';
            resultText += `\n🍽️  This Meal: ${data.calories} calories`;
            resultText += `\n📊 Today's Total: ${data.daily_total} calories`;
            resultText += `\n📝 Meals Today: ${data.entry_count}`;
            
            resultBox.textContent = resultText;
            
            // Update daily stats display
            document.getElementById('totalCalories').textContent = data.daily_total;
            document.getElementById('entryCount').textContent = data.entry_count;
            
            // Refresh weekly summary
            loadWeeklySummary();
            
            // Show edit button
            showEditBtn.style.display = 'block';
            editSection.style.display = 'none';
        } else {
            resultBox.className = 'result-box error';
            resultBox.textContent = 'Error: ' + (data.error || 'Unknown error occurred');
            showEditBtn.style.display = 'none';
        }
    } catch (error) {
        loading.style.display = 'none';
        resultContainer.style.display = 'block';
        resultBox.className = 'result-box error';
        resultBox.textContent = 'Error: ' + error.message;
        showEditBtn.style.display = 'none';
    }
});

// Show edit section
showEditBtn.addEventListener('click', () => {
    editSection.style.display = 'block';
    showEditBtn.style.display = 'none';
    editTextarea.value = '';
    editTextarea.focus();
});

// Cancel edit
cancelEditBtn.addEventListener('click', () => {
    editSection.style.display = 'none';
    showEditBtn.style.display = 'block';
    editTextarea.value = '';
});

// Reanalyze with corrected items
reanalyzeBtn.addEventListener('click', async () => {
    const correctedItems = editTextarea.value.trim();
    
    if (!correctedItems) {
        alert('Please enter the corrected food items');
        return;
    }

    if (!currentEntryId) {
        alert('Error: No entry ID found. Please analyze an image first.');
        return;
    }

    editSection.style.display = 'none';
    loading.style.display = 'block';
    resultContainer.style.display = 'none';

    try {
        const response = await fetch('/reanalyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                corrected_items: correctedItems,
                entry_id: currentEntryId  // Pass the entry ID to update
            })
        });

        const data = await response.json();
        loading.style.display = 'none';
        resultContainer.style.display = 'block';

        if (data.success) {
            resultBox.className = 'result-box success';
            
            // Keep the same entry ID (it was updated, not created new)
            currentEntryId = data.entry_id;
            
            // Display corrected analysis
            let resultText = '✅ Corrected Analysis:\n\n' + data.analysis;
            resultText += '\n\n━━━━━━━━━━━━━━━━━━━━━━';
            resultText += `\n🍽️  This Meal: ${data.calories} calories`;
            resultText += `\n📊 Today's Total: ${data.daily_total} calories`;
            resultText += `\n📝 Meals Today: ${data.entry_count}`;
            resultText += '\n\n💡 Tip: The meal count stayed the same - we updated your previous entry!';
            
            resultBox.textContent = resultText;
            
            // Update daily stats display
            document.getElementById('totalCalories').textContent = data.daily_total;
            document.getElementById('entryCount').textContent = data.entry_count;
            
            // Refresh weekly summary
            loadWeeklySummary();
            
            // Show edit button again (in case user wants to edit again)
            showEditBtn.style.display = 'block';
            editSection.style.display = 'none';
        } else {
            resultBox.className = 'result-box error';
            resultBox.textContent = 'Error: ' + (data.error || 'Unknown error occurred');
            showEditBtn.style.display = 'none';
        }
    } catch (error) {
        loading.style.display = 'none';
        resultContainer.style.display = 'block';
        resultBox.className = 'result-box error';
        resultBox.textContent = 'Error: ' + error.message;
        showEditBtn.style.display = 'none';
    }
});

// Reset button
resetBtn.addEventListener('click', () => {
    selectedFile = null;
    currentEntryId = null;  // Clear entry ID
    fileInput.value = '';
    uploadArea.style.display = 'block';
    previewContainer.style.display = 'none';
    resultContainer.style.display = 'none';
    editSection.style.display = 'none';
    showEditBtn.style.display = 'none';
});

// Load stats and weekly summary when page loads
loadDailyStats();
loadWeeklySummary();
