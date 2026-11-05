let bookingId = null;
let expiresAt = null;
let timerInterval = null;

document.addEventListener('DOMContentLoaded', async () => {
  requireAuth();

  const roomId = getUrlParam('room_id');
  const checkIn = getUrlParam('check_in');
  const checkOut = getUrlParam('check_out');
  const guests = getUrlParam('guests') || 1;

  if (!roomId || !checkIn || !checkOut) {
    document.getElementById('booking-summary').innerHTML =
      '<div class="error-msg">Missing booking parameters. <a href="/">Go back to search</a>.</div>';
    return;
  }

  // Calculate nights and show summary before creating the booking
  const nights = Math.round((new Date(checkOut) - new Date(checkIn)) / 86400000);
  const formSection = document.getElementById('booking-form-section');

  // Fetch room details to show summary
  const roomRes = await fetch(`/api/hotels/search/?city=_`); // fallback: get room from hotel
  // Simpler: create the booking directly and show the details from the response
  const res = await apiFetch('/api/bookings/create/', {
    method: 'POST',
    body: JSON.stringify({
      room_id: parseInt(roomId),
      check_in: checkIn,
      check_out: checkOut,
      num_guests: parseInt(guests),
    }),
  });

  if (!res) return; // redirected to login

  const data = await res.json();
  document.getElementById('booking-summary').style.display = 'none';

  if (!res.ok) {
    document.getElementById('booking-summary').style.display = 'block';
    document.getElementById('booking-summary').innerHTML =
      `<div class="error-msg">${data.error || Object.values(data).flat().join(' ')}</div>`;
    return;
  }

  bookingId = data.id;
  expiresAt = new Date(data.expires_at);

  // Populate summary table
  document.getElementById('sum-hotel').textContent = data.hotel_name;
  document.getElementById('sum-room').textContent = `Room ${data.room_number}`;
  document.getElementById('sum-type').textContent = data.room_type;
  document.getElementById('sum-checkin').textContent = formatDate(data.check_in);
  document.getElementById('sum-checkout').textContent = formatDate(data.check_out);
  document.getElementById('sum-guests').textContent = data.num_guests;
  document.getElementById('sum-total').textContent = formatCurrency(data.total_price);

  formSection.style.display = 'block';
  startCountdown();

  document.getElementById('proceed-payment-btn').addEventListener('click', () => {
    window.location.href = `/payment/${bookingId}/`;
  });
});

function startCountdown() {
  timerInterval = setInterval(() => {
    const remaining = Math.max(0, Math.floor((expiresAt - Date.now()) / 1000));
    const m = String(Math.floor(remaining / 60)).padStart(2, '0');
    const s = String(remaining % 60).padStart(2, '0');
    document.getElementById('countdown').textContent = `${m}:${s}`;

    if (remaining === 0) {
      clearInterval(timerInterval);
      document.getElementById('booking-error').style.display = 'block';
      document.getElementById('booking-error').textContent = 'Booking expired. Please search again.';
      document.getElementById('proceed-payment-btn').disabled = true;
      setTimeout(() => window.location.href = '/', 3000);
    }
  }, 1000);
}
