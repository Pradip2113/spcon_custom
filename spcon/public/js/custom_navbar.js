// $(document).ready(function () {
//     if ($('.navbar').length) {
//         const companyName =  frappe.defaults.get_default("company") || "";

//         const companyElement = $('<div>', {
//             text: companyName,
//             css: {
//                 'font-weight': 'bold',
//                 'font-size': '16px',
//                 'text-align': 'center',
//                 'margin': '0 auto',
//                 'position': 'absolute',
//                 'left': '48%',
//                 'transform': 'translateX(-50%)',
//             }
//         });

//         $('.navbar').append(companyElement);
//     }
// });

$(document).ready(function () {
    // Check if screen width is greater than mobile size
    if ($(window).width() > 768) {
        if ($('.navbar').length) {
            const companyName = frappe.defaults.get_default("company") || "";

            const companyElement = $('<div>', {
                text: companyName,
                css: {
                    'font-weight': 'bold',
                    'font-size': '16px',
                    'text-align': 'center',
                    'margin': '0 auto',
                    'position': 'absolute',
                    'left': '48%',
                    'transform': 'translateX(-50%)',
                }
            });

            $('.navbar').append(companyElement);
        }
    }
});