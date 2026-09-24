const form = document.querySelector('#reservation-form');
const result = document.querySelector('#reservation-result');
form?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(form).entries());
  payload.resource_id = Number(payload.resource_id);
  result.textContent = 'Sending request to reservation manager...';
  result.className = 'form-result pending';
  const response = await fetch('/api/reservations', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) });
  const data = await response.json();
  result.textContent = data.message || data.error;
  result.className = `form-result ${response.ok ? 'success' : 'error'}`;
  if (response.ok) form.reset();
});
