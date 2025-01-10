import frappe
import json
from geopy.distance import geodesic
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon


@frappe.whitelist()
def geo_fencing(doc, method):
    try:
        # Fetch employee's office location records
        employee_locations = frappe.get_all(
            "Employee Office Location Table",
            filters={"parent": doc.employee},
            fields=["office_location"]
        )
        
        # Check for missing device location
        if not doc.latitude or not doc.longitude:
            frappe.throw("Device location is missing.")
        
        # Device location as a tuple
        device_location = (doc.latitude, doc.longitude)
        # Flag to check if the device is inside any geofence
        is_within_geofence = False
        if employee_locations:
            for location in employee_locations:
                # Fetch office location details
                map = frappe.get_doc("Office Location", location.office_location)
                office_latitude = map.latitude
                office_longitude = map.longitude
                geofence_radius = map.radius
                
                # Validate geofence details
                if not office_latitude or not office_longitude or not geofence_radius:
                    frappe.msgprint("Office location data is incomplete for one or more records.")
                    continue
                
                # Calculate distance between device and geofence center
                geofence_center = (office_latitude, office_longitude)
                distance = geodesic(geofence_center, device_location).meters
                
                # Check if device is inside this geofence
                if distance <= geofence_radius:
                    is_within_geofence = True
                    frappe.msgprint(f"Prensently Marked {location.office_location}.")
                    break  # Exit loop once a match is found
            
            # Throw an error if the device is outside all geofences
            if not is_within_geofence:
                frappe.throw("You are not in your assigned location.")
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Geo Fencing Error")
        frappe.throw(f"An error occurred during geo-fencing: {e}")
