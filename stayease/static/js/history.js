document.addEventListener('DOMContentLoaded', async () => {
  requireAuth();

  const container = document.getElementById('bookings-list');
  const res = await apiFetch('/api/bookings/');

  if (!res) return;

  const data = await res.json();

  if (!res.ok) {
    container.innerHTML = '<div class="error-msg">Failed to load bookings.</div>';
    return;
  }

  const bookings = data.results || data;

  if (!bookings.length) {
    container.innerHTML = `
      <div class="empty-state">
        <p style="font-size:1.1rem;margin-bottom:1rem;">You have no bookings yet.</p>
        <a href="/" class="btn-primary">Search Hotels</a>
      </div>`;
    return;
  }

  container.innerHTML = bookings.map(b => `
    <div class="booking-item">
      <div class="booking-item-info">
        <h4>${b.hotel_name} — Room ${b.room_number} (${b.room_type})</h4>
        <p>${formatDate(b.check_in)} → ${formatDate(b.check_out)} · ${b.num_guests} guest${b.num_guests > 1 ? 's' : ''}</p>
        <p style="margin-top:0.25rem;">${formatCurrency(b.total_price)}</p>
        <div class="booking-ref">${b.reference}</div>
      </div>
      <div class="booking-item-actions">
        <span class="badge badge-${b.status}">${b.status}</span>
        ${b.status === 'pending'
          ? `<a href="/payment/${b.id}/" class="btn-primary" style="font-size:0.8rem;padding:0.4rem 1rem;">Complete Payment</a>`
          : ''}
        ${b.status === 'confirmed'
          ? `<button class="btn-danger" onclick="cancelBooking(${b.id}, this)">Cancel</button>`
          : ''}
      </div>
    </div>
  `).join('');
});

async function cancelBooking(bookingId, btn) {
  if (!confirm('Are you sure you want to cancel this booking? A refund will be initiated if you have paid.')) return;
  btn.disabled = true;
  btn.textContent = 'Cancelling...';

  const res = await apiFetch(`/api/bookings/${bookingId}/cancel/`, { method: 'POST' });
  if (!res) return;

  const data = await res.json();
  if (res.ok) {
    window.location.reload();
  } else {
    alert(data.error || 'Cancellation failed.');
    btn.disabled = false;
    btn.textContent = 'Cancel';
  }
}
