function applyFilters() {
    var selectedType = document.getElementById('type').value;
    var maxPrice = document.getElementById('price').value;
    var startDate = document.getElementById('filterStartDate').value;
    var endDate = document.getElementById('filterEndDate').value;

    var filterCriteria = {
        type: selectedType,
        price: maxPrice,
        startDate: startDate,
        endDate: endDate,
    };

    fetch('/api/filter_parking_spots', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(filterCriteria),
    })
        .then(response => response.json())
        .then(data => {
            console.log(data.filteredSpots);
            if (data.filteredSpots.length > 0) {
                updateMap(data.filteredSpots);

                // No need to redirect here; handle booking on spot click
            } else {
                console.log('No spots found with the selected filters.');
            }
        })
        .catch((error) => {
            console.error('Error:', error);
        });
}



function getSpotTypeIcon(type) {
    switch (type.toLowerCase()) {
        case 'standard':
            return 'fa-car'; // Replace with the actual Font Awesome icon class
        case 'electric':
            return 'fa-charging-station'; // Replace with the actual Font Awesome icon class
        case 'handicap':
            return 'fa-wheelchair'; // Replace with the actual Font Awesome icon class
        default:
            return ''; // default icon class
    }
}

function updateMap(filteredSpots) {
    clusterGroup.clearLayers();  // Clear existing markers

    // Add new markers from the filteredSpots array
    filteredSpots.forEach(function (spot) {
        var spotTypeIconClass = getSpotTypeIcon(spot.type);
        var priceFormatted = parseFloat(spot.price).toFixed(2);  // Format price here
        var availableText = spot.available ? 'Available' : 'Unavailable';
        var availableColor = spot.available ? 'green' : 'red';
        var popupContent = `
            <div class="popup-content text-center">
                <h3 class="mb-2">${spot.location}</h3>
                <div class="spot-type mb-2">
                    <i class="fas ${spotTypeIconClass}"></i> ${spot.type}
                </div>
                <div class="price mb-3">
                    <i class="fas fa-dollar-sign"></i> ${priceFormatted}
                </div>
                <div style="color: ${availableColor};"> ${availableText}
                </div>
                <button onclick="bookSpot(${spot.id}, '${spot.startDate}', '${spot.endDate}')" class="btn btn-danger btn-block">Book now</button>
            </div>
        `;
        var marker = L.marker([spot.lat, spot.lng], { icon: parkingSpotIcon })
            .bindPopup(popupContent, { maxWidth: "300" });
        clusterGroup.addLayer(marker);
    });

    mymap.addLayer(clusterGroup);

    if (filteredSpots.length > 0) {
        var group = new L.featureGroup(filteredSpots.map(spot => L.marker([spot.lat, spot.lng])));
        mymap.fitBounds(group.getBounds());
    } else {
        // If there are no spots, maybe fit the map to a default view
        mymap.setView([48.8566, 2.3522], 13);
    }
}
function updatePriceValue(value) {
    // This will ensure two decimal places are shown in the displayed price
    document.getElementById('priceValue').textContent = '$' + parseFloat(value).toFixed(2);
}
function bookSpot(spotId, startDate, endDate) {
    // Redirect to book.html with spot ID and date parameters
    window.location.href = `/book/${spotId}?start_date=${encodeURIComponent(startDate)}&end_date=${encodeURIComponent(endDate)}`;
}

