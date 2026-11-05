document.addEventListener('DOMContentLoaded', async () => {
  // Extract hotel ID from URL: /hotels/5/
  const hotelId = window.location.pathname.split('/').filter(Boolean)[1];
  const checkIn = getUrlParam('check_in');
  const checkOut = getUrlParam('check_out');
  const guests = getUrlParam('guests') || 1;

  const container = document.getElementById('hotel-container');

  const res = await fetch(`/api/hotels/${hotelId}/`);
  if (!res.ok) {
    container.innerHTML = '<div class="error-msg">Hotel not found.</div>';
    return;
  }

  const hotel = await res.json();
  document.title = `${hotel.name} — StayEase`;

  // Clone and fill template
  const template = document.getElementById('hotel-template');
  const content = template.content.cloneNode(true);
  container.innerHTML = '';
  container.appendChild(content);

  document.getElementById('hotel-name').textContent = hotel.name;
  document.getElementById('hotel-location').textContent = `📍 ${hotel.address}, ${hotel.city}, ${hotel.state}`;
  document.getElementById('hotel-stars').textContent = stars(hotel.star_rating);
  document.getElementById('hotel-description').textContent = hotel.description;

  if (hotel.image) {
    const img = document.getElementById('hotel-image');
    img.src = hotel.image;
    img.alt = hotel.name;
    img.style.display = 'block';
  }

  const amenitiesList = document.getElementById('hotel-amenities');
  if (hotel.amenities && hotel.amenities.length) {
    amenitiesList.innerHTML = hotel.amenities.map(a => `<span class="amenity-tag">${a}</span>`).join('');
  } else {
    amenitiesList.innerHTML = '<span style="color:var(--text-light);font-size:0.875rem;">No amenities listed.</span>';
  }

  const roomsGrid = document.getElementById('rooms-grid');
  if (!hotel.rooms || hotel.rooms.length === 0) {
    roomsGrid.innerHTML = '<div class="empty-state">No rooms currently available.</div>';
    return;
  }

  // If we came from a search, filter by availability (rooms already filtered server-side via search)
  // Here we show all active rooms from the hotel detail endpoint
  roomsGrid.innerHTML = hotel.rooms.map(room => {
    const bookUrl = checkIn && checkOut
      ? `/booking/?room_id=${room.id}&check_in=${checkIn}&check_out=${checkOut}&guests=${guests}&hotel_id=${hotelId}`
      : null;

    return `
      <div class="room-card">
        <div class="room-card-header">
          <div class="room-card-name">Room ${room.room_number}</div>
          <div class="room-card-type">${room.room_type}</div>
        </div>
        ${room.description ? `<div class="room-card-desc">${room.description}</div>` : ''}
        <div class="room-card-footer">
          <div>
            <div class="room-price">${formatCurrency(room.price_per_night)} <span>/night</span></div>
            <div class="room-occupancy">👥 Up to ${room.max_occupancy} guests</div>
          </div>
          ${bookUrl
            ? `<a href="${bookUrl}" class="btn-primary" style="font-size:0.875rem;padding:0.5rem 1.25rem;">Book</a>`
            : `<span style="font-size:0.8rem;color:var(--text-light);">Select dates to book</span>`
          }
        </div>
      </div>
    `;
  }).join('');
});
