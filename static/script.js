// ================= INBOX ANALYSIS =================

function analyzeEmail(text){

    const summary = document.getElementById("summary");
    summary.style.display = "block";
    summary.innerHTML = "✨ AI analyzing email...";

    fetch("/analyze",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({ text: text })
    })
    .then(r=>r.json())
    .then(data=>{

        summary.innerHTML = `
            <p><strong>Tone:</strong> ${data.tone}</p>
            <p><strong>Professional Version:</strong></p>
            <textarea style="width:100%;height:120px;">${data.rewritten}</textarea>
        `;
    })
    .catch(()=>{
        summary.innerHTML="❌ Failed to analyze email.";
    });
}


// ================= COMPOSER =================

function analyzeCompose(){

    const email = document.getElementById("composeBox").value;
    const res = document.getElementById("composeResult");

    if(!email.trim()){
        alert("ദയവായി ആദ്യം email എഴുതൂ");
        return;
    }

    res.style.display="block";
    res.innerHTML="✨ AI thinking...";

    fetch("/analyze",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({ text: email })
    })
    .then(r=>r.json())
    .then(d=>{

        res.innerHTML=`
        <p><strong>Original Tone:</strong> ${d.tone}</p>

        <p><strong>Tone After Rewrite:</strong> ${d.newtone}</p>

        <p><strong>Professional Email:</strong></p>

        <textarea style="width:100%;height:130px;">${d.rewritten}</textarea>
        `;
    })
    .catch(()=>{
        res.innerHTML="❌ AI error. Try again.";
    });
}
