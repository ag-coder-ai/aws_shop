function getCSRF() {
    return document.querySelector("[name=csrfmiddlewaretoken]")?.value || "";
}

async function post(url, body = {}) {

    const res = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": getCSRF()
        },
        body: new URLSearchParams(body)
    });

    return await res.json();
}

function showToast(msg, type = "success") {
    console.log(msg); // temporary safe fallback
}