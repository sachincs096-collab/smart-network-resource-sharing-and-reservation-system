const form = document.querySelector('#reservation-form');
const result = document.querySelector('#reservation-result');

let impactChecked = false;
let analyzedPayload = null;

form?.addEventListener('submit', async (event) => {
  event.preventDefault();

  const payload = Object.fromEntries(new FormData(form).entries());
  payload.resource_id = Number(payload.resource_id);

  // STEP 1: Analyze reservation
  if (!impactChecked) {
    result.textContent = 'Analyzing reservation impact...';
    result.className = 'form-result pending';

    try {
      const response = await fetch('/api/reservation-impact', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          resource_id: payload.resource_id,
          reservation_date: payload.reservation_date,
          start_time: payload.start_time,
          end_time: payload.end_time
        })
      });

      const responseText = await response.text();

      if (!response.ok) {
        result.innerHTML = `
          <strong>Analyzer Error</strong><br>
          ${responseText}
        `;
        result.className = 'form-result error';
        return;
      }

      const data = JSON.parse(responseText);

      // Resource unavailable
      if (data.impact === 'UNAVAILABLE') {
        result.textContent = data.message;
        result.className = 'form-result error';
        return;
      }

      // Reservation conflict
      if (data.conflict) {
        result.innerHTML = `
          <strong>Reservation Conflict</strong><br><br>
          Resource: ${data.resource}<br>
          Existing reservations: ${data.existing_reservations}<br><br>
          ${data.message}
        `;

        result.className = 'form-result error';
        return;
      }

      // Save data for final confirmation
      analyzedPayload = payload;
      impactChecked = true;

      // Impact description
      let impactDescription;

      if (data.impact === 'HIGH') {
        impactDescription =
          'This reservation will significantly increase resource usage.';
      } else if (data.impact === 'MEDIUM') {
        impactDescription =
          'This reservation will moderately increase resource usage.';
      } else {
        impactDescription =
          'This reservation has a low impact on resource usage.';
      }

      // Display analysis
      result.innerHTML = `
        <div>
          <strong>Reservation Impact Analysis</strong>
          <br><br>

          <strong>Resource:</strong>
          ${data.resource}
          <br>

          <strong>Existing reservations:</strong>
          ${data.existing_reservations}
          <br>

          <strong>Utilization before:</strong>
          ${data.utilization_before}%
          <br>

          <strong>Utilization after:</strong>
          ${data.utilization_after}%
          <br>

          <strong>Impact:</strong>
          ${data.impact}
          <br><br>

          ${impactDescription}
        </div>
      `;

      // Show alternative resource
      if (data.alternative) {
        result.innerHTML += `
          <br>
          <div>
            <strong>Alternative Resource</strong>
            <br>
            ${data.alternative.name}
            <br>
            <small>
              ${data.alternative.type} ·
              ${data.alternative.location}
            </small>
          </div>
        `;
      }

     

      result.className = 'form-result success';

      // Change main button text
      const button = form.querySelector('button[type="submit"]');

      if (button) {
        button.textContent = 'Confirm reservation →';
      }

    } catch (error) {
      result.innerHTML = `
        <strong>Analyzer Error</strong><br>
        ${error.message}
      `;

      result.className = 'form-result error';
    }

    return;
  }

  // STEP 2: Confirm reservation
  result.textContent = 'Sending request to reservation manager...';
  result.className = 'form-result pending';

  try {
    const response = await fetch('/api/reservations', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(analyzedPayload)
    });

    const data = await response.json();

    result.textContent = data.message || data.error;

    result.className =
      `form-result ${response.ok ? 'success' : 'error'}`;

    if (response.ok) {
      form.reset();

      impactChecked = false;
      analyzedPayload = null;

      const button = form.querySelector('button[type="submit"]');

      if (button) {
        button.textContent = 'Submit reservation →';
      }
    }

  } catch (error) {
    result.textContent = error.message;
    result.className = 'form-result error';
  }
});