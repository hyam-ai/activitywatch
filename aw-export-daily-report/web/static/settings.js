// Settings Page Manager

class SettingsManager {
  constructor() {
    this.settings = null;
    this.originalSettings = null; // Store original for comparison
    this.hasUnsavedChanges = false;
    this.init();
  }

  async init() {
    this.setupEventListeners();
    this.initializeTheme();
    await this.loadTimezones();
    await this.loadSettings();
  }

  setupEventListeners() {
    // Theme toggle
    document.getElementById('themeToggle').addEventListener('click', () => this.toggleTheme());

    // Work schedule toggle
    document.getElementById('workScheduleEnabled').addEventListener('change', (e) => {
      this.toggleWorkScheduleDetails(e.target.checked);
    });

    // N8N webhook toggle
    document.getElementById('n8nEnabled').addEventListener('change', (e) => {
      this.updateN8NStatus(e.target.checked);
    });

    // Asana toggle
    document.getElementById('asanaEnabled').addEventListener('change', (e) => {
      this.updateAsanaStatus(e.target.checked);
    });

    // Save button
    document.getElementById('saveSettingsBtn').addEventListener('click', () => this.saveSettings());
    
    // Track changes on all form inputs
    this.setupChangeTracking();
  }

  setupChangeTracking() {
    const inputs = document.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
      input.addEventListener('input', () => this.markAsChanged());
    });
  }

  markAsChanged() {
    // Compare current form values with original settings
    const currentFormData = this.collectFormData();
    const hasChanges = !this.settingsAreEqual(currentFormData, this.originalSettings);
    
    if (hasChanges && !this.hasUnsavedChanges) {
      this.hasUnsavedChanges = true;
      document.getElementById('unsavedWarning').style.display = 'block';
    } else if (!hasChanges && this.hasUnsavedChanges) {
      this.markAsSaved();
    }
  }

  markAsSaved() {
    this.hasUnsavedChanges = false;
    document.getElementById('unsavedWarning').style.display = 'none';
  }

  initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    const navLogo = document.getElementById('navLogo');

    if (savedTheme === 'light') {
      document.body.classList.add('light-mode');
      document.querySelector('.theme-icon').textContent = '🌙';
      navLogo.src = '/static/hyam-logo-dark.png';
    } else {
      navLogo.src = '/static/hyam-logo-light.png';
    }
  }

  toggleTheme() {
    const body = document.body;
    const themeIcon = document.querySelector('.theme-icon');
    const navLogo = document.getElementById('navLogo');

    if (body.classList.contains('light-mode')) {
      body.classList.remove('light-mode');
      themeIcon.textContent = '☀';
      navLogo.src = '/static/hyam-logo-light.png';
      localStorage.setItem('theme', 'dark');
    } else {
      body.classList.add('light-mode');
      themeIcon.textContent = '🌙';
      navLogo.src = '/static/hyam-logo-dark.png';
      localStorage.setItem('theme', 'light');
    }
  }

  async loadTimezones() {
    try {
      const response = await fetch('/api/timezones');
      const timezones = await response.json();

      const select = document.getElementById('userTimezone');
      select.innerHTML = '';

      timezones.forEach(tz => {
        const option = document.createElement('option');
        option.value = tz;
        option.textContent = tz;
        select.appendChild(option);
      });
    } catch (error) {
      console.error('Error loading timezones:', error);
    }
  }

  async loadSettings() {
    try {
      const response = await fetch('/api/settings');
      if (!response.ok) throw new Error('Failed to load settings');

      this.settings = await response.json();
      this.originalSettings = JSON.parse(JSON.stringify(this.settings)); // Deep copy
      this.populateForm();
      this.hideLoading();
    } catch (error) {
      console.error('Error loading settings:', error);
      this.showError('Failed to load settings');
    }
  }

  populateForm() {
    // User information
    document.getElementById('userEmail').value = this.settings.user.email || '';
    document.getElementById('userTimezone').value = this.settings.user.timezone || 'Europe/Berlin';

    // Work schedule
    const workScheduleEnabled = this.settings.work_schedule.enabled;
    document.getElementById('workScheduleEnabled').checked = workScheduleEnabled;
    this.toggleWorkScheduleDetails(workScheduleEnabled);

    // Work days
    const days = this.settings.work_schedule.days || [];
    document.querySelectorAll('.checkbox-sm').forEach(checkbox => {
      checkbox.checked = days.includes(checkbox.value);
    });

    // Work times
    document.getElementById('startTime').value = this.settings.work_schedule.start_time || '09:00';
    document.getElementById('endTime').value = this.settings.work_schedule.end_time || '18:00';

    // Integrations
    const n8nEnabled = this.settings.integrations?.n8n?.enabled !== false;
    document.getElementById('n8nEnabled').checked = n8nEnabled;
    document.getElementById('n8nWebhookUrl').value =
      this.settings.integrations.n8n.webhook_url || '';
    
    // Update status badge
    this.updateN8NStatus(n8nEnabled);

    // Asana integration
    const asanaEnabled = this.settings.integrations?.asana?.enabled || false;
    document.getElementById('asanaEnabled').checked = asanaEnabled;
    
    // Update Asana status badge
    this.updateAsanaStatus(asanaEnabled);
  }

  toggleWorkScheduleDetails(enabled) {
    const details = document.getElementById('workScheduleDetails');
    details.style.display = enabled ? 'block' : 'none';
  }

  updateN8NStatus(enabled) {
    const badge = document.getElementById('n8nStatusBadge');
    if (enabled) {
      badge.textContent = 'Enabled';
      badge.className = 'status-badge status-connected';
    } else {
      badge.textContent = 'Disabled';
      badge.className = 'status-badge status-disabled';
    }
  }

  updateAsanaStatus(enabled) {
    const badge = document.getElementById('asanaStatusBadge');
    if (enabled) {
      badge.textContent = 'Enabled';
      badge.className = 'status-badge status-connected';
    } else {
      badge.textContent = 'Disabled';
      badge.className = 'status-badge status-disabled';
    }
  }

  collectFormData() {
    // Collect work days
    const workDays = [];
    document.querySelectorAll('.checkbox-sm:checked').forEach(checkbox => {
      workDays.push(checkbox.value);
    });

    return {
      user: {
        email: document.getElementById('userEmail').value.trim(),
        timezone: document.getElementById('userTimezone').value
      },
      work_schedule: {
        enabled: document.getElementById('workScheduleEnabled').checked,
        days: workDays,
        start_time: document.getElementById('startTime').value,
        end_time: document.getElementById('endTime').value
      },
      integrations: {
        n8n: {
          enabled: document.getElementById('n8nEnabled').checked,
          webhook_url: document.getElementById('n8nWebhookUrl').value.trim()
        },
        asana: {
          enabled: document.getElementById('asanaEnabled').checked,
          personal_access_token: this.settings?.integrations?.asana?.personal_access_token || '',
          cache: this.settings?.integrations?.asana?.cache || { user_gid: '' },
          task_filters: this.settings?.integrations?.asana?.task_filters || {
            match_task_names: [],
            match_sections_containing: ['time-tracking'],
            match_all_tasks: false
          }
        }
      }
    };
  }

  async saveSettings() {
    const saveBtn = document.getElementById('saveSettingsBtn');
    const saveStatus = document.getElementById('saveStatus');

    // Disable button during save
    saveBtn.disabled = true;
    saveStatus.textContent = 'Saving...';
    saveStatus.className = 'save-status saving';

    try {
      const settings = this.collectFormData();

      const response = await fetch('/api/settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings)
      });

      const result = await response.json();

      if (result.success) {
        saveStatus.textContent = '✓ Settings saved successfully';
        saveStatus.className = 'save-status success';
        this.settings = settings;
        this.originalSettings = JSON.parse(JSON.stringify(settings)); // Update original
        
        // Mark as saved (hide warning)
        this.markAsSaved();
        
        // If email changed, notify user that tasks will reload on main page
        if (result.email_changed) {
          saveStatus.textContent = '✓ Settings saved - Asana tasks will reload on main page';
        }

        // Clear success message after 3 seconds
        setTimeout(() => {
          saveStatus.textContent = '';
          saveStatus.className = 'save-status';
        }, 3000);
      } else {
        // Show validation errors
        const errorMsg = result.errors.join(', ');
        saveStatus.textContent = `✗ ${errorMsg}`;
        saveStatus.className = 'save-status error';
      }
    } catch (error) {
      console.error('Error saving settings:', error);
      saveStatus.textContent = '✗ Failed to save settings';
      saveStatus.className = 'save-status error';
    } finally {
      saveBtn.disabled = false;
    }
  }

  hideLoading() {
    document.getElementById('loadingState').style.display = 'none';
    document.getElementById('settingsForm').style.display = 'block';
  }

  showError(message) {
    document.getElementById('loadingState').innerHTML =
      `<p class="text-body error-message">[ ${message} ]</p>`;
  }

  settingsAreEqual(settings1, settings2) {
    // Recursively sort all keys in nested objects for accurate comparison
    const sortKeys = (obj) => {
      if (obj === null || typeof obj !== 'object' || Array.isArray(obj)) {
        return obj;
      }
      return Object.keys(obj)
        .sort()
        .reduce((sorted, key) => {
          sorted[key] = sortKeys(obj[key]);
          return sorted;
        }, {});
    };
    
    return JSON.stringify(sortKeys(settings1)) === JSON.stringify(sortKeys(settings2));
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  new SettingsManager();
});