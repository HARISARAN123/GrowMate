document.addEventListener('DOMContentLoaded', function () {
    const fileInput = document.getElementById('fileInput');
    const preview = document.getElementById('preview');
    const analyzeButton = document.getElementById('analyzeButton');
    const uploadForm = document.getElementById('uploadForm');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const results = document.getElementById('results');

    // Disable the analyze button by default
    analyzeButton.disabled = true;

    // File input change event
    fileInput.addEventListener('change', function () {
        const file = fileInput.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function (e) {
                preview.innerHTML = `<img src="${e.target.result}" alt="Plant Image" style="max-width: 100%; border-radius: 12px;">`;
                analyzeButton.disabled = false;
            };
            reader.readAsDataURL(file);
        }
    });

    // Form submit event
    uploadForm.addEventListener('submit', function (e) {
        e.preventDefault();

        // Display loading spinner
        loadingSpinner.style.display = 'block';
        analyzeButton.disabled = true;

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        // Send file to the server for analysis
        fetch('/analyze', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            loadingSpinner.style.display = 'none';
            analyzeButton.disabled = false;
            displayResults(data);
        })
        .catch(error => {
            loadingSpinner.style.display = 'none';
            analyzeButton.disabled = false;
            alert('Error analyzing the image. Please try again.');
            console.error('Error:', error);
        });
    });

    // Function to display the results
    function displayResults(data) {
        results.style.display = 'block';
        results.innerHTML = '<h3>Results</h3>';

        data.diseases.forEach(disease => {
            const resultItem = document.createElement('div');
            resultItem.classList.add('result-item');
            resultItem.innerHTML = `
                <span class="result-name">${disease.name}</span>
                <span class="result-confidence">${disease.confidence}%</span>
            `;
            results.appendChild(resultItem);
        });
    }
});
