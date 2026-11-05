document.addEventListener('DOMContentLoaded', () => {
  // Set minimum date to today
  const today = new Date().toISOString().split('T')[0];
  document.getElementById('check-in').min = today;
  document.getElementById('check-out').min = today;

  document.getElementById('check-in').addEventListener('change', (e) => {
    document.getElementById('check-out').min = e.target.value;
  });

  document.getElementById('search-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    await searchHotels();
  });
});

async function searchHotels() {
  const city = document.getElementById('city').value.trim();
  const checkIn = document.getElementById('check-in').value;
  const checkOut = document.getElementById('check-out').value;
  const guests = document.getElementById('guests').value;

  const resultsSection = document.getElementById('results-section');
  const resultsGrid = document.getElementById('results-grid');
  const resultsHeader = document.getElementById('results-header');

  resultsSection.style.display = 'block';
  resultsGrid.innerHTML = '<div class="loading">Searching for hotels...</div>';
  resultsHeader.textContent = '';

  const params = new URLSearchParams({ city, check_in: checkIn, check_out: checkOut, guests });
  const res = await fetch(`/api/hotels/search/?${params}`);
  const data = await res.json();

  if (!res.ok) {
    resultsGrid.innerHTML = `<div class="error-msg">${data.error || 'Search failed.'}</div>`;
    return;
  }

  if (data.length === 0) {
    resultsHeader.textContent = `No hotels found in ${city} for the selected dates.`;
    resultsGrid.innerHTML = '<div class="empty-state">Try different dates or a different city.</div>';
    return;
  }

  resultsHeader.textContent = `${data.length} hotel${data.length !== 1 ? 's' : ''} found in ${city}`;

  // Store search params in sessionStorage so booking page can read them
  sessionStorage.setItem('search', JSON.stringify({ checkIn, checkOut, guests }));

  resultsGrid.innerHTML = data.map(hotel => `
    <a href="/hotels/${hotel.id}/?check_in=${checkIn}&check_out=${checkOut}&guests=${guests}" class="hotel-card">
      <div class="hotel-card-image">
        ${hotel.image
          ? `<img src="${hotel.image}" alt="${hotel.name}" />`
          : '🏨'}
      </div>
      <div class="hotel-card-body">
        <div class="hotel-card-name">${hotel.name}</div>
        <div class="hotel-card-location">📍 ${hotel.city}, ${hotel.state}</div>
        <div class="stars">${stars(hotel.star_rating)}</div>
        <div class="hotel-card-footer">
          <div class="hotel-card-price">
            ${formatCurrency(hotel.min_price)}
            <span>/night</span>
          </div>
          <div style="font-size:0.8rem;color:var(--text-light);">
            ${hotel.available_rooms.length} room${hotel.available_rooms.length !== 1 ? 's' : ''} available
          </div>
        </div>
      </div>
    </a>
  `).join('');
}
