document.getElementById('get-personalized-tips').addEventListener('click', function() {
    fetchRecommendations();
});

document.getElementById('get-personalized-recommendations').addEventListener('click', function() {
    fetchRecommendations();
});

function fetchRecommendations() {
    // Show the container while fetching recommendations
    document.getElementById('personalized-container').style.display = 'block';

    // Fetch recommendations from the backend
    fetch(url)
        .then(response => response.json())
        .then(data => {
            // Update the content of the personalized-content div
            const recommendations = data.recommendations;
            let content = '<ul>';
            
            recommendations.forEach(rec => {
                content += `<li>${rec}</li>`;
            });

            content += '</ul>';
            document.getElementById('personalized-content').innerHTML = content;
        })
        .catch(error => {
            console.error('Error fetching recommendations:', error);
            document.getElementById('personalized-content').innerText = 'Failed to load personalized recommendations.';
        });
}