document.addEventListener('DOMContentLoaded', async () => {
  requireAuth();

  // Extract booking ID from URL: /payment/5/
  const bookingId = window.location.pathname.split('/').filter(Boolean)[1];

  const res = await apiFetch(`/api/bookings/${bookingId}/`);
  if (!res) return;

  const booking = await res.json();
  document.getElementById('payment-summary').style.display = 'none';

  if (!res.ok) {
    document.getElementById('payment-summary').style.display = 'block';
    document.getElementById('payment-summary').innerHTML = '<div class="error-msg">Booking not found.</div>';
    return;
  }

  if (booking.status === 'confirmed') {
    document.getElementById('payment-section').style.display = 'block';
    document.getElementById('pay-action-row').innerHTML = `
      <div class="success-msg" style="display:block;">
        This booking is already confirmed. <a href="/bookings/history/">View your bookings</a>.
      </div>`;
    fillPaymentSummary(booking);
    return;
  }

  if (booking.status !== 'pending') {
    document.getElementById('payment-summary').style.display = 'block';
    document.getElementById('payment-summary').innerHTML =
      `<div class="error-msg">This booking cannot be paid (status: ${booking.status}).</div>`;
    return;
  }

  fillPaymentSummary(booking);
  document.getElementById('payment-section').style.display = 'block';

  document.getElementById('pay-btn').addEventListener('click', () => initiatePayment(bookingId, booking));
});

function fillPaymentSummary(booking) {
  document.getElementById('pay-reference').textContent = booking.reference;
  document.getElementById('pay-hotel').textContent = booking.hotel_name;
  document.getElementById('pay-checkin').textContent = formatDate(booking.check_in);
  document.getElementById('pay-checkout').textContent = formatDate(booking.check_out);
  document.getElementById('pay-amount').textContent = formatCurrency(booking.total_price);
}

async function initiatePayment(bookingId, booking) {
  const btn = document.getElementById('pay-btn');
  btn.disabled = true;
  btn.textContent = 'Opening payment gateway...';
  hideError('payment-error');

  const res = await apiFetch('/api/payments/create-order/', {
    method: 'POST',
    body: JSON.stringify({ booking_id: parseInt(bookingId) }),
  });

  if (!res) return;
  const data = await res.json();

  if (!res.ok) {
    showError('payment-error', data.error || 'Failed to create payment order.');
    btn.disabled = false;
    btn.textContent = 'Pay Now with Razorpay';
    return;
  }

  const options = {
    key: data.key,
    amount: data.amount,
    currency: data.currency,
    name: 'StayEase',
    description: `Booking for ${booking.hotel_name}`,
    order_id: data.order_id,
    handler: async function (response) {
      await verifyPayment(response);
    },
    prefill: {},
    theme: { color: '#1a3a5c' },
    modal: {
      ondismiss: function () {
        btn.disabled = false;
        btn.textContent = 'Pay Now with Razorpay';
      },
    },
  };

  const rzp = new Razorpay(options);
  rzp.open();
}

async function verifyPayment(response) {
  const btn = document.getElementById('pay-btn');
  btn.textContent = 'Verifying payment...';

  const res = await apiFetch('/api/payments/verify/', {
    method: 'POST',
    body: JSON.stringify({
      razorpay_order_id: response.razorpay_order_id,
      razorpay_payment_id: response.razorpay_payment_id,
      razorpay_signature: response.razorpay_signature,
    }),
  });

  if (!res) return;
  const data = await res.json();

  document.getElementById('pay-action-row').style.display = 'none';

  if (res.ok) {
    showSuccess('payment-success',
      `✓ Payment confirmed! Booking reference: ${data.booking_reference}. Redirecting to your bookings...`
    );
    setTimeout(() => window.location.href = '/bookings/history/', 2500);
  } else {
    showError('payment-error', data.error || 'Payment verification failed. Please contact support.');
    document.getElementById('pay-action-row').style.display = 'flex';
    document.getElementById('pay-btn').disabled = false;
    document.getElementById('pay-btn').textContent = 'Retry Payment';
  }
}
