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

      let data;

      try {
        data = JSON.parse(responseText);
      } catch {
        result.innerHTML = `
          <strong>Analyzer Error</strong><br>
          ${responseText}
        `;
        result.className = 'form-result error';
        return;
      }

      // Resource unavailable
      if (data.impact === 'UNAVAILABLE') {
        result.textContent = data.message;
        result.className = 'form-result error';
        return;
      }

      // ==========================================
      // RESERVATION CONFLICT
      // ==========================================
      if (data.conflict) {

        let alternativesHTML = '';

        if (data.alternatives && data.alternatives.length > 0) {

          alternativesHTML = `
            <br>

            <div>
              <strong>Available Alternatives</strong>

              <br><br>

              <div class="alternative-list">

                ${data.alternatives.map(resource => `
                  <div class="alternative-card">

                    <div>
                      <strong>${resource.name}</strong>

                      <br>

                      <small>
                        ${resource.type} ·
                        ${resource.location}
                      </small>
                    </div>

                    <button
                      type="button"
                      class="select-alternative"
                      data-resource-id="${resource.id}">
                      Select
                    </button>

                  </div>
                `).join('')}

              </div>

            </div>
          `;

        } else {

          alternativesHTML = `
            <br><br>

            <strong>
              No alternative resources are available for this time.
            </strong>
          `;
        }

        result.innerHTML = `
          <strong>Reservation Conflict</strong>

          <br><br>

          <strong>Resource:</strong>
          ${data.resource}

          <br>

          <strong>Existing reservations:</strong>
          ${data.existing_reservations}

          <br><br>

          ${data.message}

          ${alternativesHTML}
        `;

        result.className = 'form-result error';

        return;
      }

      // ==========================================
      // NO CONFLICT
      // ==========================================

      analyzedPayload = payload;
      impactChecked = true;

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

      // Display impact analysis
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

      result.className = 'form-result success';

      // Change button text
      const button =
        form.querySelector('button[type="submit"]');

      if (button) {
        button.textContent =
          'Confirm reservation →';
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

  // ==========================================
  // STEP 2: CONFIRM RESERVATION
  // ==========================================

  result.textContent =
    'Sending request to reservation manager...';

  result.className =
    'form-result pending';

  try {

    const response = await fetch(
      '/api/reservations',
      {
        method: 'POST',

        headers: {
          'Content-Type': 'application/json'
        },

        body: JSON.stringify(analyzedPayload)
      }
    );

    const data =
      await response.json();

    result.textContent =
      data.message || data.error;

    result.className =
      `form-result ${
        response.ok ? 'success' : 'error'
      }`;

    if (response.ok) {

      form.reset();

      impactChecked = false;
      analyzedPayload = null;

      const button =
        form.querySelector(
          'button[type="submit"]'
        );

      if (button) {
        button.textContent =
          'Submit reservation →';
      }
    }

  } catch (error) {

    result.textContent =
      error.message;

    result.className =
      'form-result error';
  }
});


// ==========================================
// STEP 3: SELECT ALTERNATIVE RESOURCE
// ==========================================

document.addEventListener('click', (event) => {

  const button =
    event.target.closest('.select-alternative');

  if (!button) {
    return;
  }

  const resourceId =
    Number(button.dataset.resourceId);

  const resourceSelect =
    document.querySelector('#resource_id');

  if (!resourceSelect) {

    result.textContent =
      'Resource selector not found.';

    result.className =
      'form-result error';

    return;
  }

  // Change resource dropdown
  resourceSelect.value =
    String(resourceId);

  // Reset analyzer
  impactChecked = false;
  analyzedPayload = null;

  // Change button
  const submitButton =
    form.querySelector(
      'button[type="submit"]'
    );

  if (submitButton) {

    submitButton.textContent =
      'Check alternative →';
  }

  // Get selected resource name
  const selectedName =
    button
      .closest('.alternative-card')
      ?.querySelector('strong')
      ?.textContent ||
    'alternative resource';

  result.innerHTML = `
    <strong>Alternative Selected</strong>

    <br><br>

    ${selectedName} has been selected.

    <br><br>

    Click
    <strong>Check alternative →</strong>
    to verify its availability and reservation impact.
  `;

  result.className =
    'form-result success';

  // Bring reservation form into view
  form.scrollIntoView({
    behavior: 'smooth',
    block: 'center'
  });

});