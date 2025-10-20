# Update Checklist for 20 October 2025

## 1. GitHub Setup

- [ ] Fork official ActivityWatch repository on GitHub
- [ ] Clone forked repository locally
- [ ] Verify `aw-export-daily-report/` module is included
- [ ] Push any remaining changes to fork
- [ ] Set up upstream remote for future updates

---

## 2. Settings Page Implementation

### Frontend (`localhost:9999/settings`)

#### User Information Section
- [ ] Email address input field
- [ ] Timezone selector dropdown (common timezones)
- [ ] Save button with validation

#### Integrations Section
- [ ] Asana integration status display
- [ ] Google Calendar integration status display
- [ ] N8N webhook URL configuration field

#### Work Schedule Section
- [ ] Days selector (Mon-Fri checkboxes)
- [ ] Start time input (HH:MM format)
- [ ] End time input (HH:MM format)
- [ ] Enable/disable work hours tracking toggle

### Backend (`web_server.py`)

- [ ] `GET /api/settings` - Load user settings
- [ ] `POST /api/settings` - Save user settings
- [ ] Settings validation logic
- [ ] Config file storage/retrieval

### Files to Create

- [ ] `web/settings.html` - Settings page UI
- [ ] `web/static/settings.js` - Settings page logic
- [ ] `web/static/settings.css` - Settings page styles
- [ ] `aw_export_daily_report/config.py` - Settings management

---

## 3. Timezone Integration

- [ ] Apply user-selected timezone to UI display
- [ ] Apply user-selected timezone to export JSON
- [ ] Apply user-selected timezone to webhook data
- [ ] Update `convertToBerlinISO()` to use dynamic timezone
- [ ] Update `formatTimeToBerlin()` to use dynamic timezone

---

## 4. Integration Setup (Admin Token Approach)

### Asana Integration
- [ ] Fetch tasks by user email using admin token
- [ ] Display connection status in settings
- [ ] Test task retrieval

### Google Calendar Integration
- [ ] Fetch calendar events by user email using admin token
- [ ] Display connection status in settings
- [ ] Test event retrieval

---

## 5. Testing

- [ ] Test settings save/load functionality
- [ ] Test timezone changes in UI
- [ ] Test timezone changes in export
- [ ] Test work schedule filtering
- [ ] Test integration status displays
- [ ] Verify all settings persist after restart

---

## Notes

- Settings stored locally per user in config file
- Admin tokens configured server-side (not visible to users)
- Users only enter: email, timezone, work schedule
- All integrations managed centrally by admin
