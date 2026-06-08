# Attendance Request Customization Documentation

## 1. Document Purpose

This document describes the customizations implemented on the ERPNext/HRMS **Attendance Request** DocType. It covers the functional behavior visible to users and the technical implementation details required for support, review, and future maintenance.

## 2. Functional Documentation

### 2.1 Business Objective

The Attendance Request customization controls how employees regularize attendance exceptions. It adds purpose-based tracking, out/in time capture, monthly restrictions for personal work, attachment enforcement for app issues, and validation against existing attendance/check-in records.

### 2.2 Customized Fields

| Field Label | Field Name | Type | Purpose |
| --- | --- | --- | --- |
| Workflow State | `workflow_state` | Link | Stores workflow state for approval tracking. Hidden on the form. |
| Purpose | `custom_purpose` | Select | Captures the reason category for the request. This field is mandatory. |
| App Issue Attachment | `custom_app_issue_attachment` | Attach | Captures supporting proof when the request purpose is App Issue. Visible and mandatory only for App Issue. |
| Add Out Time | `custom_add_out_time` | Button | Allows the employee to record the current out time. |
| Out Time | `custom_out_time` | Data | Stores the recorded out time. |
| Add In Time | `custom_add_in_time` | Button | Allows the employee to record the current in time. |
| In Time | `custom_in_time` | Data | Stores the recorded in time. |
| Remark By Manager | `custom_remark_by_manager` | Small Text | Allows the manager to add remarks during review. |

The standard `explanation` field has also been made mandatory.

### 2.3 Purpose Options

The customized Purpose field supports the following values:

| Purpose | Usage |
| --- | --- |
| Personal Work | Used when the employee leaves for personal work. |
| Company Work | Used when the attendance gap is because of official work. |
| Attendance Missing | Used when attendance was not captured or is incomplete. |
| App Issue | Used when the issue is caused by mobile/app attendance problems. |

### 2.4 User Flow

1. Employee opens a new Attendance Request.
2. Employee selects the employee, date range, shift, and purpose.
3. Employee enters reason and explanation.
4. For App Issue, employee attaches supporting proof.
5. For Personal Work, employee can use Add Out Time and Add In Time buttons to record the time away from work.
6. Request is saved and submitted according to workflow/permission rules.
7. System validates the request before save and submit.
8. If approved/submitted, standard HRMS attendance request processing continues, except where customized validations restrict submission.

### 2.5 Personal Work Rules

The system applies these rules for requests with Purpose = Personal Work:

| Rule | Behavior |
| --- | --- |
| Monthly limit | Employee can create a maximum of 3 Personal Work Attendance Requests in the same calendar month. Cancelled requests are ignored. |
| Submission restriction | Personal Work Attendance Requests cannot be submitted. |
| Out/In time capture | User can click Add Out Time and Add In Time to capture current browser/server time in `HH:mm:ss` format. |
| Half-day marking | If the time difference between Out Time and In Time is more than 30 minutes and up to 4 hours, the form automatically marks Half Day and sets Half Day Date as From Date. |

### 2.6 App Issue Rules

When Purpose = App Issue:

| Rule | Behavior |
| --- | --- |
| Attachment visibility | App Issue Attachment is shown only for App Issue. |
| Attachment mandatory | System blocks submission if no attachment/file is linked to the request. |

### 2.7 Attendance and Check-in Validations

The customization prevents incorrect or duplicate regularization in the following cases:

| Scenario | System Behavior |
| --- | --- |
| Late entry half-day attendance already exists | If an Attendance record exists for the employee/date with `custom_late_entry_early_exit = 1`, the Attendance Request is blocked during save. User is instructed to fill a Leave Application. |
| Submitted overlapping request exists | If another submitted Attendance Request for the same employee overlaps the selected date range, submission is blocked. |
| Both IN and OUT check-ins already exist | If Employee Checkin records with both `IN` and `OUT` log types already exist for a date in the request range, submission is blocked for that date. |

### 2.8 Overlap Handling

The standard Attendance Request overlap validation has been customized. Draft or non-cancelled overlapping requests are detected, but the customization does not throw the standard overlap error at validation time. A stricter overlap check is applied on submit only against already submitted requests.

### 2.9 Attendance Creation Warning Handling

The standard validation that blocks requests when no attendance can be created has been customized. If all request days already have attendance warnings and there is no overwrite action, the customization does not throw the standard blocking error.

## 3. Technical Documentation

### 3.1 Application Files

| Area | File |
| --- | --- |
| Custom field export | `spcon/spcon/custom/attendance_request.json` |
| Client-side form script | `spcon/public/js/attendance_request.js` |
| Server-side event methods | `spcon/public/py/attendance_request.py` |
| Overridden DocType class | `spcon/override/attendance_request.py` |
| Hook registration | `spcon/hooks.py` |

### 3.2 Hook Configuration

The Attendance Request client script is registered through `doctype_js`:

```python
doctype_js = {
    "Attendance Request": "public/js/attendance_request.js",
}
```

The standard HRMS Attendance Request class is overridden:

```python
override_doctype_class = {
    "Attendance Request": "spcon.override.attendance_request.CustomAttendanceRequest",
}
```

Document events are registered as follows:

```python
doc_events = {
    "Attendance Request": {
        "before_save": [
            "spcon.public.py.attendance_request.purpose_limit",
            "spcon.public.py.attendance_request.validate_late_entry_attendance",
        ],
        "on_submit": [
            "spcon.public.py.attendance_request.attendance_submit",
            "spcon.public.py.attendance_request.made_attachment_required",
            "spcon.public.py.attendance_request.validate_attendance_request",
        ],
    },
}
```

### 3.3 Client-side Logic

File: `spcon/public/js/attendance_request.js`

| Event/Button | Technical Behavior |
| --- | --- |
| `refresh` | Hides Add Out Time button if `custom_out_time` already exists. Hides Add In Time button if `custom_in_time` already exists. |
| `custom_add_out_time` | Sets `custom_out_time` to `frappe.datetime.now_time()` and hides the Add Out Time button. |
| `custom_add_in_time` | Requires Out Time first. Sets `custom_in_time` to current time, hides the Add In Time button, then applies half-day logic. |
| `apply_half_day_rule` | Parses Out/In times using Moment.js, calculates duration, handles midnight crossing, and marks Half Day when Personal Work duration is above 30 minutes and up to 240 minutes. |

### 3.4 Server-side Event Methods

File: `spcon/public/py/attendance_request.py`

| Method | Event | Purpose |
| --- | --- | --- |
| `purpose_limit` | `before_save` | Counts Personal Work requests for the employee in the selected month and blocks save if the count is already 3 or more. |
| `validate_late_entry_attendance` | `before_save` | Blocks request if same-date attendance already exists as half-day due to late entry/early exit. |
| `attendance_submit` | `on_submit` | Blocks submission if another submitted Attendance Request overlaps the same employee and date range. |
| `made_attachment_required` | `on_submit` | Blocks App Issue submission if no File attachment is linked to the document. |
| `validate_attendance_request` | `on_submit` | Blocks submission if both IN and OUT Employee Checkin records already exist for any requested date. Also blocks Personal Work submission. |

### 3.5 Overridden Class Behavior

File: `spcon/override/attendance_request.py`

The custom class `CustomAttendanceRequest` extends the standard HRMS `AttendanceRequest` class.

Customized methods:

| Method | Standard Behavior Changed |
| --- | --- |
| `validate_request_overlap` | Detects overlapping non-cancelled requests but does not throw the standard overlap error. |
| `validate_no_attendance_to_create` | Suppresses the standard error when every request day already has attendance warnings and no overwrite action is available. |

### 3.6 Data Dependencies

The customization depends on these DocTypes and fields:

| DocType | Field/Condition Used |
| --- | --- |
| Attendance Request | `employee`, `from_date`, `to_date`, `custom_purpose`, `custom_out_time`, `custom_in_time`, `docstatus` |
| Attendance | `employee`, `attendance_date`, `custom_late_entry_early_exit` |
| Employee Checkin | `employee`, `log_type`, `time` |
| File | `attached_to_doctype`, `attached_to_name` |

### 3.7 Validation Timing

| Validation | Trigger |
| --- | --- |
| Personal Work monthly limit | Before Save |
| Late entry/early exit attendance check | Before Save |
| Submitted overlapping request check | On Submit |
| App Issue attachment check | On Submit |
| Existing IN/OUT check-in check | On Submit |
| Personal Work submit block | On Submit |

## 4. Acceptance Test Scenarios

| Scenario | Expected Result |
| --- | --- |
| Create Personal Work request when employee already has 3 Personal Work requests in the month | Save is blocked. |
| Create Personal Work request with fewer than 3 existing monthly requests | Save is allowed. |
| Submit Personal Work request | Submission is blocked. |
| Select App Issue without attachment and submit | Submission is blocked. |
| Select App Issue with attachment and submit | Submission passes attachment validation. |
| Create request for date with late-entry half-day Attendance record | Save is blocked. |
| Submit request overlapping another submitted request | Submission is blocked. |
| Submit request when both IN and OUT check-ins exist for same date | Submission is blocked. |
| Click Add Out Time | Current time is stored in Out Time and button is hidden. |
| Click Add In Time without Out Time | User receives message to add Out Time first. |
| Personal Work duration above 30 minutes and up to 4 hours | Half Day is checked and Half Day Date is set to From Date. |

## 5. Deployment Notes

1. Ensure the `spcon` app is installed on the target site.
2. Run migration so custom fields and property setters sync:

```bash
bench --site <site-name> migrate
```

3. Clear cache and reload Desk assets if client-side changes are not visible:

```bash
bench --site <site-name> clear-cache
bench build --app spcon
```

4. Verify that the hooks in `spcon/hooks.py` are active and that the HRMS app is installed.

## 6. Known Notes

Personal Work requests are allowed to be saved within the monthly limit but are blocked during submission. This means they can remain as draft records for tracking or review, depending on the operational workflow.

The customized overlap behavior intentionally suppresses the standard validation error during normal validation and enforces submitted-request overlap only during submission.
