/**
 * FlyRank Embeddable Widget JS Engine v1.0.0
 * Lightweight, zero-dependency, cross-origin lead capture widget.
 */
(function () {
  // Find current script tag to extract widget ID and API base URL
  const currentScript = document.currentScript || (function () {
    const scripts = document.getElementsByTagName('script');
    return scripts[scripts.length - 1];
  })();

  const scriptSrc = currentScript ? currentScript.src : '';
  const urlObj = new URL(scriptSrc, window.location.href);
  const widgetId = urlObj.searchParams.get('id') || currentScript.getAttribute('data-widget-id') || 'w_demo_123';
  const apiBase = urlObj.origin;

  // Avoid duplicate injection
  if (document.getElementById('flyrank-widget-container-' + widgetId)) {
    return;
  }

  // Create isolated container
  const container = document.createElement('div');
  container.id = 'flyrank-widget-container-' + widgetId;
  container.style.fontFamily = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
  container.style.maxWidth = '420px';
  container.style.margin = '20px auto';
  container.style.padding = '24px';
  container.style.borderRadius = '16px';
  container.style.background = '#ffffff';
  container.style.boxShadow = '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)';
  container.style.border = '1px solid #e2e8f0';
  container.style.color = '#1e293b';
  container.style.boxSizing = 'border-box';

  container.innerHTML = '<div style="text-align:center; padding: 20px; color:#64748b;">Loading widget...</div>';
  
  // Append to script parent or body
  if (currentScript && currentScript.parentNode) {
    currentScript.parentNode.insertBefore(container, currentScript.nextSibling);
  } else {
    document.body.appendChild(container);
  }

  // Fetch widget configuration from public cached endpoint
  fetch(apiBase + '/api/v1/widgets/' + widgetId + '/config')
    .then(function (res) {
      if (!res.ok) throw new Error('Widget configuration not found (HTTP ' + res.status + ')');
      return res.json();
    })
    .then(function (config) {
      renderWidget(config);
    })
    .catch(function (err) {
      container.innerHTML = '<div style="color:#ef4444; font-size:14px; text-align:center;">Failed to load widget: ' + err.message + '</div>';
    });

  function renderWidget(config) {
    const theme = config.theme_color || '#4f46e5';

    container.innerHTML = `
      <div style="margin-bottom: 16px;">
        <h3 style="margin: 0 0 6px 0; font-size: 20px; font-weight: 700; color: #0f172a;">${config.title}</h3>
        <p style="margin: 0; font-size: 14px; color: #64748b; line-height: 1.5;">${config.description}</p>
      </div>

      <form id="flyrank-form-${widgetId}" style="display: flex; flex-direction: column; gap: 12px;">
        <!-- Hidden Honeypot Field for Bot Defense -->
        <input type="text" name="_website_url_hp" style="display:none !important; visibility:hidden;" tabindex="-1" autocomplete="off" />

        <div>
          <label style="display:block; font-size: 13px; font-weight: 600; margin-bottom: 4px; color: #334155;">Full Name *</label>
          <input type="text" name="name" required placeholder="John Doe" style="width: 100%; padding: 10px 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px; box-sizing: border-box; outline: none;" />
        </div>

        <div>
          <label style="display:block; font-size: 13px; font-weight: 600; margin-bottom: 4px; color: #334155;">Email Address *</label>
          <input type="email" name="email" required placeholder="john@example.com" style="width: 100%; padding: 10px 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px; box-sizing: border-box; outline: none;" />
        </div>

        <div>
          <label style="display:block; font-size: 13px; font-weight: 600; margin-bottom: 4px; color: #334155;">Message</label>
          <textarea name="message" rows="3" placeholder="Tell us more..." style="width: 100%; padding: 10px 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px; box-sizing: border-box; outline: none; resize: vertical;"></textarea>
        </div>

        <button type="submit" id="flyrank-submit-btn-${widgetId}" style="background: ${theme}; color: #ffffff; border: none; padding: 12px; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; transition: opacity 0.2s; margin-top: 4px;">
          ${config.button_text || 'Submit'}
        </button>

        <div id="flyrank-msg-${widgetId}" style="display:none; font-size: 13px; text-align: center; padding: 8px; border-radius: 6px; margin-top: 4px;"></div>
      </form>
    `;

    const form = document.getElementById('flyrank-form-' + widgetId);
    const submitBtn = document.getElementById('flyrank-submit-btn-' + widgetId);
    const msgDiv = document.getElementById('flyrank-msg-' + widgetId);

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      submitBtn.disabled = true;
      submitBtn.innerText = 'Submitting...';
      msgDiv.style.display = 'none';

      const formData = new FormData(form);
      const payload = {
        widget_id: widgetId,
        name: formData.get('name'),
        email: formData.get('email'),
        message: formData.get('message'),
        _website_url_hp: formData.get('_website_url_hp') || ''
      };

      fetch(config.submit_url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })
      .then(function (res) {
        if (!res.ok) {
          return res.json().then(function (data) {
            throw new Error(data.error ? data.error.message : 'Submission failed (' + res.status + ')');
          });
        }
        return res.json();
      })
      .then(function (data) {
        form.style.display = 'none';
        container.innerHTML = `
          <div style="text-align: center; padding: 24px 0;">
            <div style="font-size: 40px; margin-bottom: 12px;">🎉</div>
            <h3 style="margin: 0 0 8px 0; font-size: 20px; font-weight: 700; color: #0f172a;">Thank You!</h3>
            <p style="margin: 0; font-size: 14px; color: #64748b;">${data.message || 'Your submission has been received.'}</p>
          </div>
        `;
      })
      .catch(function (err) {
        submitBtn.disabled = false;
        submitBtn.innerText = config.button_text || 'Submit';
        msgDiv.style.display = 'block';
        msgDiv.style.background = '#fef2f2';
        msgDiv.style.color = '#dc2626';
        msgDiv.style.border = '1px solid #fecaca';
        msgDiv.innerText = err.message;
      });
    });
  }
})();
