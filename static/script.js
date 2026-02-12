// ================= INBOX ANALYSIS =================

function analyzeEmail() {

    const summaryBox = document.getElementById("summary");

    // Get visible mail content
    const mailElement = document.querySelector(".email-body");

    if (!mailElement) {
        alert("No mail content found");
        return;
    }

    const mailText = mailElement.innerText;
    const mailHtml = mailElement.innerHTML;

    summaryBox.style.display = "block";
    summaryBox.innerHTML = "✨ AI analyzing email...";

    fetch("/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            text: mailText,
            html: mailHtml
        })
    })
    .then(r => r.json())
    .then(data => {

        summaryBox.innerHTML = `
            <p><strong>Summary:</strong></p>
            <p>${data.summary}</p>

            <hr>

            <p><strong>Tone:</strong> ${data.tone}</p>
        `;
    })
    .catch(() => {
        summaryBox.innerHTML = "❌ Failed to analyze email.";
    });
}


// ================= COMPOSER =================

function analyzeCompose() {

    const email = document.getElementById("composeBox").value;
    const res = document.getElementById("composeResult");

    if (!email.trim()) {
        alert("ദയവായി ആദ്യം email എഴുതൂ");
        return;
    }

    res.style.display = "block";
    res.innerHTML = "✨ AI thinking...";

    fetch("/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            text: email
        })
    })
    .then(r => r.json())
    .then(d => {

        res.innerHTML = `
            <p><strong>Summary:</strong></p>
            <p>${d.summary}</p>

            <hr>

            <p><strong>Tone:</strong> ${d.tone}</p>
        `;
    })
    .catch(() => {
        res.innerHTML = "❌ AI error. Try again.";
    });
}
