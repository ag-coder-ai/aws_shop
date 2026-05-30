// COPY ORDER ID
function copyOrderId(orderId){
    navigator.clipboard.writeText(orderId);
    alert("Copied: " + orderId);
}


// CANCEL ORDER
async function cancelOrder(orderId){

    if(!confirm("Cancel this order?")) return;

    const res = await fetch(`/orders/cancel/${orderId}/`, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCSRFToken()
        }
    });

    const data = await res.json();
    alert(data.message);

    if(data.success){
        location.reload();
    }
}


// RETURN REQUEST
async function requestReturn(orderId){

    const reason = document.getElementById("returnReason").value;
    const comment = document.getElementById("returnComment").value;

    const res = await fetch(`/orders/return/${orderId}/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": getCSRFToken()
        },
        body: new URLSearchParams({
            reason,
            comment
        })
    });

    const data = await res.json();
    alert(data.message);

    if(data.success){
        location.reload();
    }
}


// CSRF helper
function getCSRFToken(){
    return document.cookie
        .split("; ")
        .find(row => row.startsWith("csrftoken="))
        ?.split("=")[1];
}