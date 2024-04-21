async function applyFilters() {
    var onlyAvailable = document.getElementById('availableSpotsCheckbox').checked;
    var selectedType = document.getElementById('type').value;
    var maxPrice = document.getElementById('price').value;
    var startDate = document.getElementById('filterStartDate').value || new Date().toISOString().split('T')[0] + ' 00:00:00';
    var endDate = document.getElementById('filterEndDate').value || new Date().toISOString().split('T')[0] + ' 23:59:59';

    var today = new Date().toISOString().split('T')[0];
    startDate = startDate || today;
    endDate = endDate || today;

    var filterCriteria = {
        type: selectedType || "All", // If no type is selected, use "All" to fetch spots of all types.
        price: maxPrice || "No Max", // Use a special value to indicate no max price filter.
        startDate: startDate,
        endDate: endDate,
        onlyAvailable: onlyAvailable // Add this line to include the checkbox state
    };

    // Use the browser's URL API to update the query parameters without reloading the page
    var queryParams = new URLSearchParams(window.location.search);
    queryParams.set('start_date', startDate);
    queryParams.set('end_date', endDate);
    history.replaceState(null, null, "?" + queryParams.toString());

    try {
        let response = await fetch('/api/filter_parking_spots', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(filterCriteria),
        });

        console.log(response);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Log the full response for debugging
        console.log('Response:', response);
        let data = await response.json();


        console.log(data.filteredSpots);

        // Log the filtered spots for debugging
        console.log('Filtered Spots:', data.filteredSpots);


        if (data.filteredSpots && data.filteredSpots.length > 0) {
            updateMap(data.filteredSpots);
        } else {
            console.log('No spots found with the selected filters.');
            // If no spots are found, it might be useful to indicate this to the user
            alert('No spots found with the selected filters.');
        }
    } catch (error) {
        console.error('Error while applying filters:', error);
        alert('An error occurred while applying filters: ' + error);
    }

}
function createPopupContent(spot, currentStartDate, currentEndDate) {
    // Assume currentStartDate and currentEndDate are available in the scope
    var availableColor = spot.available ? 'green' : 'red';
    var spotTypeIconClass = getSpotTypeIcon(spot.type);
    var priceFormatted = parseFloat(spot.price).toFixed(2);
    var availableText = spot.available ? 'Available' : 'Unavailable';

    // Adjust dates based on availability
    var popupStartDate = spot.available ? currentStartDate : spot.next_available_date;
    var popupEndDate = spot.available ? currentEndDate : spot.next_available_date;

    // Create popup content
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
            <button class="btn btn-danger btn-block" data-id="${spot.id}" data-start-date="${popupStartDate}" data-end-date="${popupEndDate}">Book now</button>
        </div>
    `;
    return popupContent;
}


function updateMap(filteredSpots) {
    clusterGroup.clearLayers();  // Clear existing markers

    // Get current filter dates from the URL
    var queryParams = new URLSearchParams(window.location.search);
    var currentStartDate = queryParams.get('start_date') || new Date().toISOString().split('T')[0];
    var currentEndDate = queryParams.get('end_date') || new Date().toISOString().split('T')[0];

    filteredSpots.forEach(function (spot) {
        if (!spot.lat || !spot.lng) {
            console.error('Invalid spot coordinates:', spot);
            return;
        }

        var isAvailable = spot.hasOwnProperty('isAvailable') ? spot.isAvailable : spot.available;
        var marker = L.marker([spot.lat, spot.lng], { icon: parkingSpotIcon })
            .bindPopup(createPopupContent(spot, currentStartDate, currentEndDate), { maxWidth: "300" });
        clusterGroup.addLayer(marker);
    });

    // Attach the click event listener only if the document is loaded
    if (document.readyState === "complete") {
        attachClickEventToButtons();
    } else {
        document.addEventListener('DOMContentLoaded', attachClickEventToButtons);
    }

    mymap.addLayer(clusterGroup);

    if (filteredSpots.length > 0) {
        var group = new L.featureGroup(filteredSpots.map(spot => L.marker([spot.lat, spot.lng])));
        mymap.fitBounds(group.getBounds());
    } else {
        mymap.setView([48.8566, 2.3522], 13);
    }
}

function attachClickEventToButtons() {
    console.log
    document.querySelectorAll('.btn-danger.btn-block').forEach(function (button) {
        button.addEventListener('click', function (event) {
            var spotId = event.target.getAttribute('data-id');
            var startDate = event.target.getAttribute('data-start-date');
            var endDate = event.target.getAttribute('data-end-date');
            bookSpot(spotId, startDate, endDate);
        });
    });
}
function getSpotTypeIcon(type) {
    if (type) {
        switch (type.toLowerCase()) {
            case 'standard':
                return 'fa-car';
            case 'electric':
                return 'fa-charging-station';
            case 'handicap':
                return 'fa-wheelchair';
            default:
                return ''; // Provide a default icon class if necessary.
        }
    } else {
        console.error("Spot type is undefined:", type);
        return ''; // Provide a default icon class if type is undefined.
    }
}


function updatePriceValue(value) {
    // This will ensure two decimal places are shown in the displayed price
    document.getElementById('priceValue').textContent = '$' + parseFloat(value).toFixed(2);
}
// This function will send a POST request to perform the booking and handle the response.
function bookSpot(spotId, startDate, endDate) {
    // Add a fallback for startDate and endDate if they are null or undefined
    var startDate = document.getElementById('filterStartDate').value || new Date().toISOString().split('T')[0];
    var endDate = document.getElementById('filterEndDate').value || new Date().toISOString().split('T')[0];
    window.location.href = `/book/${spotId}?start_date=${startDate}&end_date=${endDate}`;
}
// This is the redirect function
function redirectToConfirmation() {
    window.location.href = '/confirmation.html';
}


function updateButtonState() {
    var startDateInput = document.getElementById('startDate');
    var endDateInput = document.getElementById('endDate');
    var confirmButton = document.querySelector('.confirm-btn');

    var startDate = startDateInput.value ? new Date(startDateInput.value) : null;
    var endDate = endDateInput.value ? new Date(endDateInput.value) : null;

    // Debugging output
    console.log('Start Date:', startDate);
    console.log('End Date:', endDate);

    // Normalize the current date to midnight for comparison
    var now = new Date();
    now.setHours(0, 0, 0, 0);

    // Check if the start date is today or in the future, and end date is the same or after start date
    var disableButton = !startDate || !endDate || startDate < now || endDate < startDate;


    // More debugging output
    console.log('Button should be disabled:', disableButton);

    confirmButton.disabled = disableButton;
}



// Call this function to attach event listeners and to set the initial button state:
function initializeDateInputsAndButton() {
    var startDateInput = document.getElementById('startDate');
    var endDateInput = document.getElementById('endDate');
    if (startDateInput && endDateInput) {
        startDateInput.addEventListener('change', updateButtonState);
        endDateInput.addEventListener('change', updateButtonState);
        updateButtonState(); // Initial call to set the correct state when the page loads
    }
}


function greyButtonOut() {

    document.addEventListener('DOMContentLoaded', function () {
        var startDateInput = document.getElementById('startDate');
        var endDateInput = document.getElementById('endDate');

        startDateInput.addEventListener('change', updateButtonState);
        endDateInput.addEventListener('change', updateButtonState);

        // Initial button state update
        updateButtonState();
    });
}

function confirmBooking(event) {
    // Prevent the default form submission
    event.preventDefault();

    // Get the form data
    const formData = new FormData(event.target);
    const bookingDetails = {
        spot_id: formData.get('spot_id'),
        start_date: formData.get('start_date'),
        end_date: formData.get('end_date'),
    };

    // Send the form data to the server
    fetch('/confirm_booking', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: new URLSearchParams(bookingDetails)
    })
        .then(response => response.json())
        // Inside the confirmBooking function, after the fetch call
        .then(data => {
            if (data.success) {
                // Assuming you're sending back the spot ID in the response
                window.location.href = `/confirmation?spot_id=${data.spot_id}&start_date=${data.start_date}&end_date=${data.end_date}`;
            } else {
                // Handle the case where booking was not successful
                alert('Booking failed: ' + data.message);
            }
        })

        .catch(error => {
            console.error('Booking error:', error);
            alert('An error occurred during booking.');
        });
}



