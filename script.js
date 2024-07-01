document.addEventListener('DOMContentLoaded', function () {
    fetch('http://localhost:5000/stations2')
        .then(response => response.json())
        .then(data => {
            const stationsContainer = document.getElementById('stations-container');
            data.forEach(station => {
                const stationDiv = document.createElement('div');
                stationDiv.className = 'station';
                stationDiv.innerHTML = `
                    <h2>${station.AddressInfo.Title}</h2>
                    <p>Address: ${station.AddressInfo.AddressLine1}</p>
                    <p>City: ${station.AddressInfo.Town}</p>
                    <p>State: ${station.AddressInfo.StateOrProvince}</p>
                    <p>Pincode: ${station.AddressInfo.Postcode}</p>
                    <p>Latitude: ${station.AddressInfo.Latitude}</p>
                    <p>Longitude: ${station.AddressInfo.Longitude}</p>
                `;
                stationsContainer.appendChild(stationDiv);
            });
        })
        .catch(error => {
            console.error('Error fetching the stations:', error);
        });
});
