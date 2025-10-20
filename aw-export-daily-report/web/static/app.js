// ActivityWatch Daily Review - Timeline View

class ActivityReview {
  constructor() {
    this.data = null;
    this.selectedBlocks = new Set();
    this.deselectedSupporting = new Map();
    this.blockNotes = new Map();
    this.relabeledBlocks = new Map();
    this.asanaTasks = null;
    this.blockTasks = new Map();
    this.settings = null;
    this.init();
  }

  async init() {
    await this.loadSettings();
    await this.loadAsanaTasks();
    await this.loadTimelineData();
    this.setupEventListeners();
    this.initializeTheme();
  }

  async loadSettings() {
    try {
      const response = await fetch('/api/settings');
      if (!response.ok) {
        console.warn('Failed to load settings, using defaults');
        this.settings = {
          user: { timezone: 'Europe/Berlin', email: '' }
        };
        return;
      }
      this.settings = await response.json();
      console.log('Settings loaded:', this.settings);
    } catch (error) {
      console.warn('Error loading settings:', error);
      this.settings = {
        user: { timezone: 'Europe/Berlin', email: '' }
      };
    }
  }

  setupEventListeners() {
    document.getElementById('themeToggle').addEventListener('click', () => this.toggleTheme());
    document.getElementById('datePicker').addEventListener('change', (e) => this.loadDateFromPicker(e.target.value));
    document.getElementById('selectAllBtn').addEventListener('click', () => this.selectAll());
    document.getElementById('deselectAllBtn').addEventListener('click', () => this.deselectAll());
    document.getElementById('submitBtn').addEventListener('click', () => this.showSubmitModal());
    document.getElementById('cancelSubmitBtn').addEventListener('click', () => this.hideSubmitModal());
    document.getElementById('confirmSubmitBtn').addEventListener('click', () => this.submitActivities());
    document.getElementById('closeSuccessBtn').addEventListener('click', () => this.hideSuccessModal());
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

  async loadAsanaTasks() {
    try {
      const response = await fetch('/api/asana/tasks');
      if (!response.ok) {
        console.warn('Failed to load Asana tasks');
        return;
      }
      this.asanaTasks = await response.json();
      console.log('Asana tasks loaded:', this.asanaTasks);
      
      // Re-render timeline to update task dropdowns
      if (this.data) {
        this.renderTimeline();
      }
    } catch (error) {
      console.warn('Error loading Asana tasks:', error);
    }
  }

  async loadTimelineData() {
    try {
      const date = '2025-10-17';
      const response = await fetch(`/api/timeline/${date}`);
      if (!response.ok) throw new Error('Failed to load timeline data');

      this.data = await response.json();
      
      // Update activity date display
      const dateObj = new Date(date);
      const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
      const dayName = dayNames[dateObj.getDay()];
      document.getElementById('activityDate').textContent = `${dayName}, ${date}`;
      
      // Set date picker value and max date (yesterday)
      const yesterday = this.getYesterdayDate();
      document.getElementById('datePicker').value = date;
      document.getElementById('datePicker').max = yesterday;
      
      this.renderTimeline();
      this.showUI();
    } catch (error) {
      console.error('Error loading timeline:', error);
      this.showError(error.message);
    }
  }

  async loadDateFromPicker(date) {
    try {
      const response = await fetch(`/api/timeline/${date}`);
      if (!response.ok) throw new Error('Failed to load timeline data');

      this.data = await response.json();
      
      // Clear previous selections when loading new date
      this.selectedBlocks.clear();
      this.deselectedSupporting.clear();
      this.blockNotes.clear();
      this.relabeledBlocks.clear();
      this.blockTasks.clear();
      
      // Update activity date display
      const dateObj = new Date(date);
      const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
      const dayName = dayNames[dateObj.getDay()];
      document.getElementById('activityDate').textContent = `${dayName}, ${date}`;
      
      this.renderTimeline();
      this.showUI();
    } catch (error) {
      console.error('Error loading timeline:', error);
      this.showError(error.message);
    }
  }

  getYesterdayDate() {
    const now = new Date();
    const dayOfWeek = now.getDay(); // 0 = Sunday, 1 = Monday, etc.
    
    // If today is Monday, go back 3 days to Friday
    // Otherwise go back 1 day to yesterday
    const daysToGoBack = (dayOfWeek === 1) ? 3 : 1;
    
    const targetDate = new Date(Date.UTC(
      now.getUTCFullYear(), 
      now.getUTCMonth(), 
      now.getUTCDate() - daysToGoBack
    ));
    
    return targetDate.toISOString().split('T')[0];
  }

  // Convert UTC timestamp to user's timezone (HH:MM format for UI display)
  formatTimeToUserTimezone(utcTimestamp) {
    // If no timestamp provided, return empty string
    if (!utcTimestamp) return '';

    try {
      const date = new Date(utcTimestamp);
      // Check if date is valid
      if (isNaN(date.getTime())) {
        console.warn('Invalid timestamp:', utcTimestamp);
        return utcTimestamp; // Return original value
      }

      const userTimezone = this.settings?.user?.timezone || 'Europe/Berlin';

      return date.toLocaleTimeString('de-DE', {
        timeZone: userTimezone,
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      });
    } catch (error) {
      console.error('Error converting timestamp:', error);
      return utcTimestamp; // Return original value on error
    }
  }

  // Convert UTC timestamp to UTC ISO format for export (always UTC)
  convertToUTCISO(utcTimestamp) {
    if (!utcTimestamp) return null;

    try {
      const date = new Date(utcTimestamp);
      if (isNaN(date.getTime())) return null;

      // Return as UTC ISO string
      return date.toISOString();
    } catch (error) {
      console.error('Error converting to Berlin ISO:', error);
      return utcTimestamp;
    }
  }

  // Helper to get Berlin timezone offset (+01:00 or +02:00)
  getBerlinOffset(date) {
    const berlinTime = new Date(date.toLocaleString('en-US', { timeZone: 'Europe/Berlin' }));
    const utcTime = new Date(date.toLocaleString('en-US', { timeZone: 'UTC' }));
    const offsetMs = berlinTime - utcTime;
    const offsetHours = Math.floor(offsetMs / (1000 * 60 * 60));
    const offsetMins = Math.abs(Math.floor((offsetMs % (1000 * 60 * 60)) / (1000 * 60)));
    
    const sign = offsetHours >= 0 ? '+' : '-';
    const hours = String(Math.abs(offsetHours)).padStart(2, '0');
    const mins = String(offsetMins).padStart(2, '0');
    
    return `${sign}${hours}:${mins}`;
  }

  renderTimeline() {
    const container = document.getElementById('timelineContainer');
    container.innerHTML = '';

    // Create table structure
    const table = document.createElement('div');
    table.className = 'timeline-table';

    // Table header
    const header = document.createElement('div');
    header.className = 'timeline-header';
    header.innerHTML = `
      <div class="timeline-col-time">TIMELINE</div>
      <div class="timeline-col-summary">SUMMARY</div>
      <div class="timeline-col-logs">LOGS</div>
      <div class="timeline-col-tasks">TASKS</div>
      <div class="timeline-col-notes">NOTES</div>
    `;
    table.appendChild(header);

    // Timeline blocks
    this.data.timeline_blocks.forEach((block, index) => {
      const row = this.createTimelineRow(block, index);
      table.appendChild(row);
    });

    container.appendChild(table);
    this.updateSummary();
  }

  createTimelineRow(block, index) {
    const row = document.createElement('div');
    row.className = 'timeline-row';
    row.dataset.blockIndex = index;

    // Add 'selected' class by default
    block.selected = true;
    this.selectedBlocks.add(index);
    row.classList.add('selected');

    // Timeline column (left) - Convert UTC to Berlin time
    const timeCol = document.createElement('div');
    timeCol.className = 'timeline-col-time';
    
    // Handle missing UTC timestamps (for AFK blocks)
    let startTimeUTC = block.start_time_utc;
    let endTimeUTC = block.end_time_utc;
    
    // If UTC timestamps are missing, reconstruct from date + HH:MM time
    if (!startTimeUTC && block.start_time && this.data.date) {
      startTimeUTC = `${this.data.date}T${block.start_time}:00+00:00`;
    }
    if (!endTimeUTC && block.end_time && this.data.date) {
      endTimeUTC = `${this.data.date}T${block.end_time}:00+00:00`;
    }
    
    const startTime = startTimeUTC ? this.formatTimeToUserTimezone(startTimeUTC) : block.start_time;
    const endTime = endTimeUTC ? this.formatTimeToUserTimezone(endTimeUTC) : block.end_time;
    
    timeCol.innerHTML = `
      <div class="time-range">
        <div class="time-start">${startTime}</div>
        <div class="time-line"></div>
        <div class="time-end">${endTime}</div>
      </div>
    `;

    // Summary column (middle)
    const summaryCol = document.createElement('div');
    summaryCol.className = 'timeline-col-summary';

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.className = 'block-checkbox';
    checkbox.checked = true;
    checkbox.addEventListener('change', (e) => {
      this.toggleBlock(index, e.target.checked);
    });

    const summaryContent = document.createElement('div');
    summaryContent.className = 'summary-content';

    // Check if this is an AFK block and add smart suggestions
    const isAFK = block.is_afk || block.main_activity.raw_app === 'AFK';

    if (isAFK) {
      // Generate smart suggestions based on surrounding blocks
      const suggestions = this.generateSmartSuggestions(index);
      
      // Check if this AFK block is during lunch hours (12:00-15:00)
      const isLunchTime = this.isLunchTime(block);
      
      // Add Lunch option if during lunch hours
      let lunchOption = '';
      if (isLunchTime) {
        lunchOption = '<div class="custom-dropdown-option" data-value="Lunch">Lunch</div>';
      }

      summaryContent.innerHTML = `
        <div class="activity-relabel-wrapper">
          <div class="custom-dropdown" data-block-index="${index}">
            <div class="custom-dropdown-selected">AFK / Inactive</div>
            <div class="custom-dropdown-options">
              <div class="custom-dropdown-option" data-value="AFK">AFK / Inactive</div>
              ${lunchOption}
              ${suggestions.map(s => {
                const escapedValue = s.value.replace(/"/g, '&quot;');
                return `<div class="custom-dropdown-option" data-value="${escapedValue}">${s.label}</div>`;
              }).join('')}
            </div>
          </div>
          <div class="summary-time">Total: <span class="duration-text">${this.formatDuration(block.duration)}</span> (${block.main_activity.percentage}%)</div>
        </div>
      `;

      // Add click listener to toggle dropdown
      const dropdownContainer = summaryContent.querySelector('.custom-dropdown');
      const dropdownSelected = dropdownContainer.querySelector('.custom-dropdown-selected');
      const dropdownOptions = dropdownContainer.querySelector('.custom-dropdown-options');

      dropdownSelected.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdownContainer.classList.toggle('open');
      });

      // Add click listeners to options
      const options = dropdownOptions.querySelectorAll('.custom-dropdown-option');
      options.forEach(option => {
        option.addEventListener('click', (e) => {
          e.stopPropagation();
          const value = option.getAttribute('data-value');
          const label = option.textContent;

          // Update selected display
          dropdownSelected.textContent = label;

          // Close dropdown
          dropdownContainer.classList.remove('open');

          // Trigger relabel
          this.relabelBlock(index, value);
        });
      });

      // Close dropdown when clicking outside
      document.addEventListener('click', (e) => {
        if (!dropdownContainer.contains(e.target)) {
          dropdownContainer.classList.remove('open');
        }
      });
    } else {
      // Get first window title or fallback to app name
      const windowTitle = block.main_activity.windows && block.main_activity.windows.length > 0
        ? block.main_activity.windows[0]
        : block.main_activity.app;
      
      const formattedTitle = this.formatActivityTitle(block.main_activity.app, windowTitle);
      
      summaryContent.innerHTML = `
        <div class="summary-app">${formattedTitle}</div>
        <div class="summary-time">Total: <span class="duration-text">${this.formatDuration(block.duration)}</span> (${block.main_activity.percentage}%)</div>
      `;
    }

    summaryCol.appendChild(checkbox);
    summaryCol.appendChild(summaryContent);

    // Logs column (right)
    const logsCol = document.createElement('div');
    logsCol.className = 'timeline-col-logs';

    const logsList = document.createElement('div');
    logsList.className = 'logs-list';

    // Main activity - show once with actual duration
    const mainLogItem = document.createElement('div');
    mainLogItem.className = 'log-item log-main';
    
    // Use first window or app name for title
    const mainWindow = block.main_activity.windows && block.main_activity.windows.length > 0
      ? block.main_activity.windows[0]
      : block.main_activity.app;
    const formattedMainTitle = this.formatActivityTitle(block.main_activity.app, mainWindow);
    
    // Calculate actual duration: block.duration * (percentage / 100)
    const actualDuration = Math.round(block.duration * (parseFloat(block.main_activity.percentage) / 100));
    const durationText = this.formatDuration(actualDuration);
    
    // Create duration span for styling
    const durationSpan = document.createElement('span');
    durationSpan.className = 'duration-text';
    durationSpan.textContent = durationText;
    
    mainLogItem.innerHTML = `• ${formattedMainTitle} `;
    mainLogItem.appendChild(durationSpan);
    logsList.appendChild(mainLogItem);

    // Supporting activities with checkboxes (filter out <1min)
    if (!this.deselectedSupporting.has(index)) {
      this.deselectedSupporting.set(index, new Set());
    }

    block.supporting_activities.forEach((support, supportIndex) => {
      // Skip activities under 1 minute (60 seconds)
      if (support.duration < 60) return;

      const supportItem = document.createElement('div');
      supportItem.className = 'log-item log-support-wrapper';

      const supportCheckbox = document.createElement('input');
      supportCheckbox.type = 'checkbox';
      supportCheckbox.className = 'support-checkbox';
      supportCheckbox.checked = true;
      supportCheckbox.dataset.blockIndex = index;
      supportCheckbox.dataset.supportIndex = supportIndex;
      supportCheckbox.addEventListener('change', (e) => {
        e.stopPropagation();
        this.toggleSupporting(index, supportIndex, e.target.checked);
      });

      const supportLabel = document.createElement('span');
      supportLabel.className = 'log-item log-support';

      // Format duration using formatDuration helper for consistent spacing
      const durationText = this.formatDuration(support.duration);

      // Get title from windows array or fallback to app name
      const title = support.windows && support.windows.length > 0
        ? support.windows[0]
        : support.app;

      const formattedTitle = this.formatActivityTitle(support.app, title);
      
      // Add duration wrapped in span for styling
      const durationSpan = document.createElement('span');
      durationSpan.className = 'duration-text';
      durationSpan.textContent = durationText;
      
      supportLabel.innerHTML = `${formattedTitle} `;
      supportLabel.appendChild(durationSpan);

      supportItem.appendChild(supportCheckbox);
      supportItem.appendChild(supportLabel);
      logsList.appendChild(supportItem);
    });

    logsCol.appendChild(logsList);

    // Tasks column
    const tasksCol = document.createElement('div');
    tasksCol.className = 'timeline-col-tasks';

    const tasksDropdownContainer = document.createElement('div');
    tasksDropdownContainer.className = 'custom-dropdown tasks-dropdown';
    tasksDropdownContainer.dataset.blockIndex = index;

    const tasksSelected = document.createElement('div');
    tasksSelected.className = 'custom-dropdown-selected';
    tasksSelected.textContent = 'None';

    const tasksOptions = document.createElement('div');
    tasksOptions.className = 'custom-dropdown-options';

    // Add "None" option
    const noneOption = document.createElement('div');
    noneOption.className = 'custom-dropdown-option';
    noneOption.dataset.value = '';
    noneOption.textContent = 'None';
    tasksOptions.appendChild(noneOption);

    // Add Asana tasks grouped by project
    if (this.asanaTasks) {
      // Add owner header (e.g., "Alican's Tasks")
      const ownerEmail = this.settings?.user?.email || '';
      if (ownerEmail) {
        const ownerName = ownerEmail.split('@')[0]; // Get part before @
        const capitalizedName = ownerName.charAt(0).toUpperCase() + ownerName.slice(1);
        
        const ownerHeader = document.createElement('div');
        ownerHeader.className = 'custom-dropdown-owner-header';
        ownerHeader.textContent = `${capitalizedName}'s Tasks`;
        tasksOptions.appendChild(ownerHeader);
      }
      
      // Add tasks grouped by project
      for (const [projectName, tasks] of Object.entries(this.asanaTasks.tasks_by_project || {})) {
        // Add project header
        const projectHeader = document.createElement('div');
        projectHeader.className = 'custom-dropdown-optgroup-label';
        projectHeader.textContent = projectName;
        tasksOptions.appendChild(projectHeader);
        
        tasks.forEach(task => {
          const option = document.createElement('div');
          option.className = 'custom-dropdown-option';
          option.dataset.value = task.gid;
          option.dataset.taskName = task.name;
          option.textContent = task.name;
          tasksOptions.appendChild(option);
        });
      }
      
      // Add tasks without project
      if (this.asanaTasks.tasks_without_project && this.asanaTasks.tasks_without_project.length > 0) {
        const projectHeader = document.createElement('div');
        projectHeader.className = 'custom-dropdown-optgroup-label';
        projectHeader.textContent = 'No Project';
        tasksOptions.appendChild(projectHeader);
        
        this.asanaTasks.tasks_without_project.forEach(task => {
          const option = document.createElement('div');
          option.className = 'custom-dropdown-option';
          option.dataset.value = task.gid;
          option.dataset.taskName = task.name;
          option.textContent = task.name;
          tasksOptions.appendChild(option);
        });
      }
    }

    tasksDropdownContainer.appendChild(tasksSelected);
    tasksDropdownContainer.appendChild(tasksOptions);

    // Add click listener to toggle dropdown
    tasksSelected.addEventListener('click', (e) => {
      e.stopPropagation();
      tasksDropdownContainer.classList.toggle('open');
    });

    // Add click listeners to options
    const taskOptions = tasksOptions.querySelectorAll('.custom-dropdown-option');
    taskOptions.forEach(option => {
      option.addEventListener('click', (e) => {
        e.stopPropagation();
        const value = option.getAttribute('data-value');
        const taskName = option.getAttribute('data-task-name') || option.textContent;

        // Update selected display
        tasksSelected.textContent = taskName;

        // Close dropdown
        tasksDropdownContainer.classList.remove('open');

        // Store task selection
        if (value) {
          this.blockTasks.set(index, value);
        } else {
          this.blockTasks.delete(index);
        }
      });
    });

    // Prevent page scroll when scrolling inside dropdown
    tasksOptions.addEventListener('wheel', (e) => {
      e.stopPropagation();
      
      const atTop = tasksOptions.scrollTop === 0;
      const atBottom = tasksOptions.scrollTop + tasksOptions.clientHeight >= tasksOptions.scrollHeight;
      
      if ((e.deltaY < 0 && atTop) || (e.deltaY > 0 && atBottom)) {
        e.preventDefault();
      }
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
      if (!tasksDropdownContainer.contains(e.target)) {
        tasksDropdownContainer.classList.remove('open');
      }
    });

    tasksCol.appendChild(tasksDropdownContainer);

    // Notes column (far right)
    const notesCol = document.createElement('div');
    notesCol.className = 'timeline-col-notes';

    const notesTextarea = document.createElement('textarea');
    notesTextarea.className = 'notes-textarea';
    notesTextarea.placeholder = 'Add notes about this activity...';
    notesTextarea.dataset.blockIndex = index;
    notesTextarea.addEventListener('input', (e) => {
      this.blockNotes.set(index, e.target.value);
    });
    notesTextarea.addEventListener('click', (e) => {
      e.stopPropagation();
    });

    notesCol.appendChild(notesTextarea);

    row.appendChild(timeCol);
    row.appendChild(summaryCol);
    row.appendChild(logsCol);
    row.appendChild(tasksCol);
    row.appendChild(notesCol);

    return row;
  }

  toggleBlock(index, selected) {
    const row = document.querySelector(`.timeline-row[data-block-index="${index}"]`);

    if (selected) {
      this.selectedBlocks.add(index);
      row.classList.add('selected');
      
      // Re-select all supporting activities
      const supportCheckboxes = row.querySelectorAll('.support-checkbox');
      supportCheckboxes.forEach(checkbox => {
        checkbox.checked = true;
        const supportIndex = parseInt(checkbox.dataset.supportIndex);
        if (this.deselectedSupporting.has(index)) {
          this.deselectedSupporting.get(index).delete(supportIndex);
        }
      });
    } else {
      this.selectedBlocks.delete(index);
      row.classList.remove('selected');
      
      // Deselect all supporting activities
      const supportCheckboxes = row.querySelectorAll('.support-checkbox');
      supportCheckboxes.forEach(checkbox => {
        checkbox.checked = false;
        const supportIndex = parseInt(checkbox.dataset.supportIndex);
        if (!this.deselectedSupporting.has(index)) {
          this.deselectedSupporting.set(index, new Set());
        }
        this.deselectedSupporting.get(index).add(supportIndex);
      });
    }

    this.updateSummary();
  }

  toggleSupporting(blockIndex, supportIndex, selected) {
    if (!this.deselectedSupporting.has(blockIndex)) {
      this.deselectedSupporting.set(blockIndex, new Set());
    }

    if (selected) {
      this.deselectedSupporting.get(blockIndex).delete(supportIndex);
    } else {
      this.deselectedSupporting.get(blockIndex).add(supportIndex);
    }
  }

  generateSmartSuggestions(index) {
    const blocks = this.data.timeline_blocks;
    const seen = new Set(); // Track unique activities

    // Find previous non-AFK block
    let prevBlock = null;
    for (let i = index - 1; i >= 0; i--) {
      if (!blocks[i].is_afk && blocks[i].main_activity.raw_app !== 'AFK') {
        prevBlock = blocks[i];
        break;
      }
    }

    // Find next non-AFK block
    let nextBlock = null;
    for (let i = index + 1; i < blocks.length; i++) {
      if (!blocks[i].is_afk && blocks[i].main_activity.raw_app !== 'AFK') {
        nextBlock = blocks[i];
        break;
      }
    }

    const suggestions = [];

    // Add previous block's activity
    if (prevBlock) {
      const prevApp = prevBlock.main_activity.app;
      const prevWindow = prevBlock.main_activity.primary_window;
      if (!seen.has(prevApp)) {
        seen.add(prevApp);
        suggestions.push({
          label: `${prevApp}`,
          value: JSON.stringify({
            app: prevApp,
            raw_app: prevBlock.main_activity.raw_app,
            primary_window: prevWindow
          })
        });
      }
    }

    // Add next block's activity
    if (nextBlock) {
      const nextApp = nextBlock.main_activity.app;
      const nextWindow = nextBlock.main_activity.primary_window;
      if (!seen.has(nextApp)) {
        seen.add(nextApp);
        suggestions.push({
          label: `${nextApp}`,
          value: JSON.stringify({
            app: nextApp,
            raw_app: nextBlock.main_activity.raw_app,
            primary_window: nextWindow
          })
        });
      }
    }

    return suggestions;
  }

  isLunchTime(block) {
    // Get start time in user's timezone
    let startTimeUserTZ;
    
    if (block.start_time_utc) {
      // Convert UTC timestamp to user timezone
      startTimeUserTZ = this.formatTimeToUserTimezone(block.start_time_utc);
    } else if (block.start_time && this.data.date) {
      // Reconstruct UTC timestamp and convert
      const utcTimestamp = `${this.data.date}T${block.start_time}:00+00:00`;
      startTimeUserTZ = this.formatTimeToUserTimezone(utcTimestamp);
    } else {
      return false;
    }
    
    if (!startTimeUserTZ) return false;
    
    const [hours, minutes] = startTimeUserTZ.split(':').map(Number);
    const timeInMinutes = hours * 60 + minutes;
    
    // 12:00 = 720 minutes, 15:00 = 900 minutes
    return timeInMinutes >= 720 && timeInMinutes < 900;
  }

  relabelBlock(index, value) {
    if (value === 'AFK') {
      // Remove relabeling
      this.relabeledBlocks.delete(index);
    } else if (value === 'Lunch') {
      // Handle Lunch as a special case (simple string, not JSON)
      this.relabeledBlocks.set(index, {
        app: 'Lunch',
        raw_app: 'Lunch',
        primary_window: 'Lunch'
      });
    } else {
      // Parse the JSON value and store relabeling
      try {
        const activityData = JSON.parse(value);
        this.relabeledBlocks.set(index, activityData);
      } catch (e) {
        console.error('Failed to parse activity data:', value, e);
        return;
      }
    }

    // Update the visual display
    this.updateBlockDisplay(index);
  }

  updateBlockDisplay(index) {
    const row = document.querySelector(`.timeline-row[data-block-index="${index}"]`);
    if (!row) return;

    // Update row class to show it's been relabeled
    if (this.relabeledBlocks.has(index)) {
      row.classList.add('relabeled');
    } else {
      row.classList.remove('relabeled');
    }
    
    // Update summary to reflect the relabeling
    this.updateSummary();
  }

  selectAll() {
    this.selectedBlocks.clear();
    this.data.timeline_blocks.forEach((block, index) => {
      this.selectedBlocks.add(index);
      const checkbox = document.querySelector(`.timeline-row[data-block-index="${index}"] .block-checkbox`);
      const row = document.querySelector(`.timeline-row[data-block-index="${index}"]`);
      if (checkbox) checkbox.checked = true;
      if (row) row.classList.add('selected');
    });
    this.updateSummary();
  }

  deselectAll() {
    this.selectedBlocks.clear();
    this.data.timeline_blocks.forEach((block, index) => {
      const checkbox = document.querySelector(`.timeline-row[data-block-index="${index}"] .block-checkbox`);
      const row = document.querySelector(`.timeline-row[data-block-index="${index}"]`);
      if (checkbox) checkbox.checked = false;
      if (row) row.classList.remove('selected');
    });
    this.updateSummary();
  }

  updateSummary() {
    let totalTime = 0;
    let count = 0;

    this.selectedBlocks.forEach(index => {
      const block = this.data.timeline_blocks[index];
      
      // Skip AFK blocks that haven't been relabeled
      const isAFK = block.is_afk || block.main_activity.raw_app === 'AFK';
      const hasRelabel = this.relabeledBlocks.has(index);
      
      if (isAFK && !hasRelabel) {
        return; // Skip un-relabeled AFK
      }
      
      // Skip blocks relabeled as "Lunch"
      const relabelData = this.relabeledBlocks.get(index);
      if (relabelData && relabelData.app === 'Lunch') {
        return; // Skip lunch blocks
      }
      
      totalTime += block.duration;
      count++;
    });

    document.getElementById('selectedTime').textContent = this.formatDuration(totalTime);
    document.getElementById('selectedCount').textContent = count;

    // Update total time in hero section
    document.getElementById('totalTime').textContent = this.formatDuration(this.data.total_active_time);
  }

  formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  }

  formatActivityTitle(appName, windowTitle) {
    // Extract browser from app name (e.g., "Timely - Hours (Google Chrome)" -> "Google Chrome")
    const browserMatch = appName.match(/\(([^)]+)\)$/);
    const browser = browserMatch ? browserMatch[1] : null;

    if (browser) {
      // Browser-based activity
      // Extract app/page name from app field (e.g., "Timely - Hours (Google Chrome)" -> "Timely - Hours")
      const appPart = appName.replace(/\s*\([^)]+\)$/, '');
      
      // Try to extract app name and feature from title or app part
      // Title format is usually "Feature - AppName" or just "AppName"
      let appNameClean = '';
      let feature = '';
      
      if (windowTitle) {
        const titleParts = windowTitle.split(' - ');
        if (titleParts.length >= 2) {
          // "Hours - Timely" -> feature: "Hours", app: "Timely"
          feature = titleParts[0];
          appNameClean = titleParts[titleParts.length - 1];
        } else {
          // Just app name
          appNameClean = windowTitle;
        }
      }
      
      // If we couldn't get app name from title, use from app field
      if (!appNameClean) {
        const appParts = appPart.split(' - ');
        appNameClean = appParts[appParts.length - 1] || appPart;
      }
      
      // Format: Browser - AppName - Feature (or just Browser - AppName if no feature)
      if (feature && feature !== appNameClean) {
        return `${browser} - ${appNameClean} - ${feature}`;
      } else {
        return `${browser} - ${appNameClean}`;
      }
    } else {
      // Non-browser activity (e.g., "Claude", "TIDAL")
      // Format: AppName - Feature (if available from window title)
      if (windowTitle && windowTitle !== appName) {
        return `${appName} - ${windowTitle}`;
      } else {
        return appName;
      }
    }
  }

  showSubmitModal() {
    let totalTime = 0;
    let count = 0;

    this.selectedBlocks.forEach(index => {
      totalTime += this.data.timeline_blocks[index].duration;
      count++;
    });

    document.getElementById('modalSelectedCount').textContent = count;
    document.getElementById('modalSelectedTime').textContent = this.formatDuration(totalTime);
    document.getElementById('submitModal').style.display = 'flex';
  }

  hideSubmitModal() {
    document.getElementById('submitModal').style.display = 'none';
  }

  async submitActivities() {
    try {
      const selectedData = this.collectSelectedData();
      const exportData = this.formatForExport(selectedData);

      // Log export data for inspection
      console.log('=== EXPORT DATA ===');
      console.log(JSON.stringify(exportData, null, 2));
      console.log('==================');

      const response = await fetch('/api/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(exportData)
      });

      if (!response.ok) throw new Error('Submission failed');

      this.hideSubmitModal();
      this.showSuccessModal();
    } catch (error) {
      alert('Error submitting activities: ' + error.message);
    }
  }

  formatForExport(data) {
    const activities = data.timeline_blocks.map(block => {
      // Handle missing UTC timestamps (for relabeled AFK blocks)
      let startTimeUTC = block.start_time_utc;
      let endTimeUTC = block.end_time_utc;
      
      // If UTC timestamps are missing, reconstruct from date + HH:MM time
      if (!startTimeUTC && block.start_time && data.date) {
        startTimeUTC = `${data.date}T${block.start_time}:00+00:00`;
      }
      if (!endTimeUTC && block.end_time && data.date) {
        endTimeUTC = `${data.date}T${block.end_time}:00+00:00`;
      }
      
      const activity = {
        activity: block.main_activity.app,
        start_time_utc: this.convertToUTCISO(startTimeUTC),
        end_time_utc: this.convertToUTCISO(endTimeUTC),
        duration_seconds: block.duration
      };

      // Add notes if present
      if (block.notes && block.notes.trim()) {
        activity.notes = block.notes.trim();
      }

      // Transform supporting activities into sub_tasks (filter out <1min like UI)
      activity.sub_tasks = block.supporting_activities
        .filter(support => support.duration >= 60)
        .map(support => {
          const title = support.windows && support.windows.length > 0
            ? support.windows[0]
            : support.app;

          // Handle missing UTC timestamps for supporting activities too
          let supportStartUTC = support.start_time_utc;
          let supportEndUTC = support.end_time_utc;
          
          if (!supportStartUTC && support.start_time && data.date) {
            supportStartUTC = `${data.date}T${support.start_time}:00+00:00`;
          }
          if (!supportEndUTC && support.end_time && data.date) {
            supportEndUTC = `${data.date}T${support.end_time}:00+00:00`;
          }

          return {
            app: support.app,
            title: title,
            start_time_utc: this.convertToUTCISO(supportStartUTC),
            end_time_utc: this.convertToUTCISO(supportEndUTC),
            duration_seconds: support.duration
          };
        });

      return activity;
    });

    return {
      metadata: {
        email: this.settings?.user?.email || "",
        date: data.date,
        timezone: "UTC"
      },
      timeline: activities
    };
  }

  collectSelectedData() {
    const selectedBlocks = [];

    this.selectedBlocks.forEach(index => {
      const block = { ...this.data.timeline_blocks[index] };

      // Skip AFK blocks that haven't been relabeled
      const isAFK = block.is_afk || block.main_activity.raw_app === 'AFK';
      if (isAFK && !this.relabeledBlocks.has(index)) {
        console.log(`Skipping AFK block ${index} - not relabeled`);
        return; // Skip this block
      }
      
      // Skip blocks relabeled as "Lunch"
      const relabelData = this.relabeledBlocks.get(index);
      if (relabelData && relabelData.app === 'Lunch') {
        console.log(`Skipping block ${index} - labeled as Lunch`);
        return; // Skip lunch blocks
      }

      // If block was relabeled, update its main activity
      if (this.relabeledBlocks.has(index)) {
        const relabelData = this.relabeledBlocks.get(index);
        block.main_activity = {
          app: relabelData.app,
          raw_app: relabelData.raw_app,
          primary_window: relabelData.primary_window
        };
        block.is_afk = false; // Mark as no longer AFK
        block.relabeled = true; // Flag for submission processing
      }

      // Filter out deselected supporting activities
      if (this.deselectedSupporting.has(index)) {
        const deselected = this.deselectedSupporting.get(index);
        block.supporting_activities = block.supporting_activities.filter((_, supportIndex) => {
          return !deselected.has(supportIndex);
        });
      }

      // Build notes with task name on top (if selected) followed by user notes
      let combinedNotes = '';

      // Add task name if selected
      if (this.blockTasks.has(index)) {
        const taskGid = this.blockTasks.get(index);
        console.log(`Block ${index} has task GID:`, taskGid);
        // Find task name from asanaTasks
        let taskName = '';
        if (this.asanaTasks) {
          // Search in tasks_by_project
          for (const tasks of Object.values(this.asanaTasks.tasks_by_project || {})) {
            const task = tasks.find(t => t.gid === taskGid);
            if (task) {
              taskName = task.name;
              console.log(`Found task name:`, taskName);
              break;
            }
          }
          // Search in tasks_without_project if not found
          if (!taskName && this.asanaTasks.tasks_without_project) {
            const task = this.asanaTasks.tasks_without_project.find(t => t.gid === taskGid);
            if (task) {
              taskName = task.name;
              console.log(`Found task name (no project):`, taskName);
            }
          }
        }
        if (taskName) {
          combinedNotes = taskName;
          console.log(`Setting combinedNotes to:`, combinedNotes);
        }
      }

      // Add user notes if available
      if (this.blockNotes.has(index)) {
        const userNotes = this.blockNotes.get(index);
        if (combinedNotes) {
          combinedNotes += ' ' + userNotes;
        } else {
          combinedNotes = userNotes;
        }
      }

      // Set combined notes if any content exists
      if (combinedNotes) {
        block.notes = combinedNotes;
      }

      selectedBlocks.push(block);
    });

    return {
      date: this.data.date,
      total_time: selectedBlocks.reduce((sum, b) => sum + b.duration, 0),
      timeline_blocks: selectedBlocks
    };
  }

  showSuccessModal() {
    document.getElementById('successModal').style.display = 'flex';
  }

  hideSuccessModal() {
    document.getElementById('successModal').style.display = 'none';
  }

  showUI() {
    document.getElementById('loadingState').style.display = 'none';
    document.getElementById('errorState').style.display = 'none';
    document.getElementById('timelineContainer').style.display = 'block';
    document.getElementById('actionBar').style.display = 'flex';
  }

  showError(message) {
    document.getElementById('loadingState').style.display = 'none';
    document.getElementById('errorState').style.display = 'block';
    document.getElementById('timelineContainer').style.display = 'none';
    document.getElementById('actionBar').style.display = 'none';
    
    document.getElementById('errorMessage').textContent = message;
  }

  async loadSelectedDate() {
    const datePicker = document.getElementById('datePicker');
    const selectedDate = datePicker.value;

    if (!selectedDate) {
      alert('Please select a date');
      return;
    }

    try {
      // Hide error, show loading
      document.getElementById('errorState').style.display = 'none';
      document.getElementById('loadingState').style.display = 'block';

      const response = await fetch(`/api/timeline/${selectedDate}`);
      if (!response.ok) throw new Error(`No data found for ${selectedDate}`);

      this.data = await response.json();
      this.renderTimeline();

      // Update date display to show selected date
      document.getElementById('reviewDate').textContent = selectedDate;

      this.showUI();
    } catch (error) {
      this.showError(error.message);
    }
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  new ActivityReview();
});