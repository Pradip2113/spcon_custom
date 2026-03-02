import frappe
from datetime import datetime, timedelta

def work_hrs_cal(doc, method):
    if doc.start_time and doc.end_time:
        # Parse time-only strings
        start_time = datetime.strptime(doc.start_time, '%H:%M:%S').time()
        end_time = datetime.strptime(doc.end_time, '%H:%M:%S').time()
        # Convert to timedelta for calculation
        start_delta = datetime.combine(datetime.min, start_time)
        end_delta = datetime.combine(datetime.min, end_time)
        # Handle overnight shifts
        if end_delta < start_delta:
            end_delta += timedelta(days=1)

        # Calculate hours
        hours = (end_delta - start_delta).total_seconds() / 3600
        doc.custom_working_hrs = hours   
