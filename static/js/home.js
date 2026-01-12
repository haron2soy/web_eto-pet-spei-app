function openStationIdModal() {
    document.getElementById("stationIdModal").style.display = "block";
}

function openStationIdModal() {
    document.getElementById('stationid-modal').style.display = 'block';
}

function closeStationIdModal() {
    document.getElementById('stationid-modal').style.display = 'none';
}

// Close modal if clicked outside of content
window.onclick = function(event) {
    var modal = document.getElementById('stationid-modal');
    if (event.target == modal) {
        modal.style.display = "none";
    }
}

