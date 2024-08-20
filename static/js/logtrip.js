document.addEventListener('DOMContentLoaded', function () {
    const sourceAddress = document.getElementById('source-input');
    const sourceResults = document.getElementById('source-results');
    const destAddress = document.getElementById('destination-input');
    const destResults = document.getElementById('destination-results');
    const dateInput = document.getElementById('date');
    
    // Set the max attribute to today's date
    const today = new Date().toISOString().split('T')[0];
    dateInput.setAttribute('max', today);

    // Add event listeners for autocomplete as before
    async function fetchPredictions(input, resultsContainer, setCoordinates) {
        const searchText = input.value.trim();
        if (searchText.length > 2) {
            try {
                const response = await fetch(`https://api.olamaps.io/places/v1/autocomplete?input=${encodeURIComponent(searchText)}&api_key=upIsbo0X7RjH2SfHjy2eYpm8TWdynT6vFDCpA85y`);
                const data = await response.json();
                const predictions = data.predictions || [];
                resultsContainer.innerHTML = '';
                resultsContainer.style.display = predictions.length > 0 ? 'block' : 'none';
                predictions.forEach((prediction) => {
                    const listItem = document.createElement('li');
                    listItem.textContent = prediction.description;
                    listItem.addEventListener('click', () => {
                        input.value = prediction.description;
                        setCoordinates(prediction.geometry.location.lat, prediction.geometry.location.lng);
                        resultsContainer.style.display = 'none';
                    });
                    resultsContainer.appendChild(listItem);
                });
            } catch (error) {
                console.error("Error fetching predictions:", error);
            }
        } else {
            resultsContainer.style.display = 'none';
        }
    }

    sourceAddress.addEventListener('input', () => {
        fetchPredictions(sourceAddress, sourceResults, (lat, lng) => {
            document.getElementById('source-lat').value = lat;
            document.getElementById('source-lng').value = lng;
        });
    });

    destAddress.addEventListener('input', () => {
        fetchPredictions(destAddress, destResults, (lat, lng) => {
            document.getElementById('dest-lat').value = lat;
            document.getElementById('dest-lng').value = lng;
        });
    });
});
