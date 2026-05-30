/* =========================================
   AUTO REFRESH TRACKING STATUS
========================================= */

async function refreshTrackingStatus() {

    try {

        const orderId = window.location.pathname
            .split("/")
            .filter(Boolean)
            .pop();

        const res = await fetch(
            `/orders/track-api/${orderId}/`
        );

        const data = await res.json();

        // STOP IF CANCELLED

        if (data.status === "CANCELLED") {
            location.reload();
            return;
        }

        // UPDATE UI

        const courier = document.getElementById(
            "courierPartner"
        );

        const tracking = document.getElementById(
            "trackingNumber"
        );

        const delivery = document.getElementById(
            "estimatedDelivery"
        );

        if(courier){
            courier.innerText =
                data.courier_partner || "Not Assigned Yet";
        }

        if(tracking){
            tracking.innerText =
                data.tracking_number || "Pending";
        }

        if(delivery){
            delivery.innerText =
                data.estimated_delivery || "Updating Soon";
        }

    }

    catch (err) {

        console.log(
            "Tracking refresh failed",
            err
        );

    }

}


/* =========================================
   REFRESH EVERY 30 SECONDS
========================================= */

setInterval(() => {

    refreshTrackingStatus();

}, 30000);