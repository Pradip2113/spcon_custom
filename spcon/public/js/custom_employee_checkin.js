frappe.ui.form.on('Employee Checkin', {
    refresh(frm) {
        // Function to handle the position received
        function onPositionReceived(position) {
            var longitude = position.coords.longitude;
            var latitude = position.coords.latitude;

            // Set the latitude and longitude values on the form
            frm.set_value('longitude', longitude);
            frm.set_value('latitude', latitude);

            console.log('Longitude: ' + longitude);
            console.log('Latitude: ' + latitude);

            // If you want to embed the map using Google Maps iframe
            var mapUrl = `https://maps.google.com/maps?q=${latitude},${longitude}&t=&z=17&ie=UTF8&iwloc=&output=embed`;
            var mapEmbedCode = `
                <div class="mapouter">
                    <div class="gmap_canvas">
                        <iframe width="100%" height="300" id="gmap_canvas" 
                                src="${mapUrl}" frameborder="0" scrolling="no" 
                                marginheight="0" marginwidth="0">
                        </iframe>
                    </div>
                </div>
            `;
            
            // Set the custom location field with the embedded map
            frm.set_df_property('custom_location', 'options', mapEmbedCode);
            frm.refresh_field('custom_location');
        }

        // Function to handle when the position is not received
        function locationNotReceived(positionError) {
            console.log('Error retrieving geolocation:', positionError);
            frappe.msgprint(__('Unable to retrieve your location.'));
        }

        // Check if coordinates are already set in the document
        if (frm.doc.longitude && frm.doc.latitude) {
            var mapUrl = `https://maps.google.com/maps?q=${frm.doc.latitude},${frm.doc.longitude}&t=&z=17&ie=UTF8&iwloc=&output=embed`;
            var mapEmbedCode = `
                <div class="mapouter">
                    <div class="gmap_canvas">
                        <iframe width="100%" height="300" id="gmap_canvas" 
                                src="${mapUrl}" frameborder="0" scrolling="no" 
                                marginheight="0" marginwidth="0">
                        </iframe>
                    </div>
                </div>
            `;
            frm.set_df_property('custom_location', 'options', mapEmbedCode);
            frm.refresh_field('custom_location');
        } else {
            // Request geolocation if not already set
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(onPositionReceived, locationNotReceived, { enableHighAccuracy: true });
            } else {
                frappe.msgprint(__('Geolocation is not supported by your browser.'));
            }
        }
    }
});
