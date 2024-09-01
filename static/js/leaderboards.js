document.addEventListener('DOMContentLoaded', function() {
    const globalButton = document.getElementById('globalButton');
    const friendsButton = document.getElementById('friendsButton');
    const globalLeaderboard = document.getElementById('globalLeaderboard');
    const friendsLeaderboard = document.getElementById('friendsLeaderboard');

    globalButton.addEventListener('click', function() {
        globalLeaderboard.classList.add('active');
        friendsLeaderboard.classList.remove('active');
        globalButton.classList.add('active');
        friendsButton.classList.remove('active');
    });

    friendsButton.addEventListener('click', function() {
        globalLeaderboard.classList.remove('active');
        friendsLeaderboard.classList.add('active');
        globalButton.classList.remove('active');
        friendsButton.classList.add('active');
    });
});