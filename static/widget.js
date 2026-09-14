/**
 * FlyRank Widget v1.0
 * Embeddable lead-capture widget
 */
(function() {
  'use strict';

  const WIDGET_VERSION = 'v1';

  function getWidgetId() {
    const scripts = document.querySelectorAll('script[src*="widget"]');
    for (const script of scripts) {
      const url = new URL(script.src);
      const id = url.searchParams.get('id');
      if (id) return id;
    }
    return null;
  }

  function getBaseUrl() {
    const scripts = document.querySelectorAll('script[src*="widget"]');
    for (const script of scripts) {
      const url = new URL(script.src);
      return url.origin;
    }
    return window.location.origin;
  }

  function createContainer(widgetId) {
    const container = document.createElement('div');
    container.id = `flyrank-widget-${widgetId}`;
    container.className = 'flyrank-widget';
    container.setAttribute('data-widget-id', widgetId);
    return container;
  }

  function renderForm(container, config) {
    container.innerHTML = '';

    const form = document.createElement('form');
    form.className = 'flyrank-form';
    form.setAttribute('data-widget-id', config.id);

    const title = document.createElement('h3');
    title.className = 'flyrank-title';
    title.textContent = config.title;
    form.appendChild(title);

    const fields = config.form_config?.fields || [
      { name: 'name', type: 'text', placeholder: 'Your Name', required: true },
      { name: 'email', type: 'email', placeholder: 'Your Email', required: true },
      { name: 'message', type: 'textarea', placeholder: 'Your Message', required: false }
    ];

    fields.forEach(field => {
      const wrapper = document.createElement('div');
      wrapper.className = 'flyrank-field';

      let input;
      if (field.type === 'textarea') {
        input = document.createElement('textarea');
      } else {
        input = document.createElement('input');
        input.type = field.type || 'text';
      }

      input.name = field.name;
      input.placeholder = field.placeholder || '';
      input.required = field.required || false;
      input.className = 'flyrank-input';

      wrapper.appendChild(input);
      form.appendChild(wrapper);
    });

    const honeypot = document.createElement('input');
    honeypot.type = 'text';
    honeypot.name = 'honeypot';
    honeypot.className = 'flyrank-honeypot';
    honeypot.style.cssText = 'position:absolute;left:-9999px;opacity:0;';
    honeypot.tabIndex = -1;
    honeypot.autocomplete = 'off';
    form.appendChild(honeypot);

    const submitBtn = document.createElement('button');
    submitBtn.type = 'submit';
    submitBtn.textContent = config.button_text || 'Submit';
    submitBtn.className = 'flyrank-submit';
    form.appendChild(submitBtn);

    const status = document.createElement('div');
    status.className = 'flyrank-status';
    status.style.display = 'none';
    form.appendChild(status);

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      await handleSubmit(form, config, status, submitBtn);
    });

    container.appendChild(form);
  }

  async function handleSubmit(form, config, status, submitBtn) {
    const formData = new FormData(form);
    const honeypot = formData.get('honeypot');

    if (honeypot) {
      showStatus(status, 'success', 'Thank you for your submission!');
      form.reset();
      return;
    }

    const submissionData = {};
    formData.forEach((value, key) => {
      if (key !== 'honeypot' && value) {
        submissionData[key] = value;
      }
    });

    submitBtn.disabled = true;
    submitBtn.textContent = 'Submitting...';

    try {
      const baseUrl = getBaseUrl();
      const response = await fetch(`${baseUrl}/api/v1/submissions/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          widget_id: config.id,
          submission_data: submissionData,
          honeypot: honeypot || null,
        }),
      });

      if (response.ok) {
        showStatus(status, 'success', 'Thank you for your submission!');
        form.reset();
      } else {
        const error = await response.json();
        showStatus(status, 'error', error.detail || 'Submission failed. Please try again.');
      }
    } catch (error) {
      showStatus(status, 'error', 'Network error. Please try again.');
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = config.button_text || 'Submit';
    }
  }

  function showStatus(element, type, message) {
    element.style.display = 'block';
    element.className = `flyrank-status flyrank-status-${type}`;
    element.textContent = message;
    setTimeout(() => {
      element.style.display = 'none';
    }, 5000);
  }

  async function loadWidget(widgetId) {
    const baseUrl = getBaseUrl();
    try {
      const response = await fetch(`${baseUrl}/api/v1/widgets/${widgetId}/config`);
      if (!response.ok) {
        throw new Error('Widget not found');
      }
      const config = await response.json();
      const container = createContainer(widgetId);
      document.body.appendChild(container);
      renderForm(container, config);
    } catch (error) {
      console.error('FlyRank widget error:', error);
    }
  }

  const widgetId = getWidgetId();
  if (widgetId) {
    loadWidget(widgetId);
  }
})();
