// Toggle between Login and Signup forms
function toggleForms() {
    document.getElementById('loginForm').classList.toggle('active');
    document.getElementById('signupForm').classList.toggle('active');
}

async function submitSignup() {
    const username = document.getElementById("signupUsername").value;
    const email = document.getElementById("signupEmail").value;
    const password = document.getElementById("signupPass").value;

    if (!username || !email || !password) {
        alert("Please fill in all fields");
        return;
    }

    try {
        const response = await fetch("http://127.0.0.1:8000/signup", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                username: username,
                email: email,
                password: password   // ✅ FIXED
            })
        });

        const data = await response.json();

        if (response.ok) {
            alert("Account created! Please login.");
            toggleForms();
        } else {
            alert("Signup Failed: " + data.detail);
        }

    } catch (error) {
        console.error("Error:", error);
        alert("Could not connect to server.");
    }
}

async function submitLogin() {
    const email = document.getElementById("loginEmail").value;
    const password = document.getElementById("loginPass").value;

    if (!email || !password) {
        alert("Please fill in all fields");
        return;
    }

    try {
        const response = await fetch("http://127.0.0.1:8000/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                email: email,
                password: password   // ✅ FIXED
            })
        });

        const data = await response.json();

        if (response.ok) {
            localStorage.setItem("user", JSON.stringify(data));
            window.location.href = "main.html";
        } else {
            alert("Login Failed: " + data.detail);
        }

    } catch (error) {
        console.error("Error:", error);
        alert("Could not connect to server.");
    }
}

/* developer signup with dev type */
async function submitsignup() {
    const username = document.getElementById("signupName").value;
    const devType = document.getElementById("signupDevType").value;
    const email = document.getElementById("signupEmail").value;
    const password = document.getElementById("signupPass").value;

    if (!username || !email || !password || !devType) {
        alert("Please fill in all fields");
        return;
    }

    try {
        const response = await fetch("http://127.0.0.1:8000/dev/signup", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                username: username,
                which_dev: devType,
                email: email,
                password: password
            })
        });

        const data = await response.json();

        if (response.ok) {
            alert("Developer account created! Please login.");
            toggleForms();
        } else {
            alert("Signup Failed: " + data.detail);
        }

    } catch (error) {
        console.error(error);
        alert("Could not connect to server.");
    }
}

/* ======================
   DEV LOGIN
====================== */
async function submitlogin() {
    const email = document.getElementById("loginEmail").value;
    const password = document.getElementById("loginPass").value;

    if (!email || !password) {
        alert("Please fill in all fields");
        return;
    }

    try {
        const response = await fetch("http://127.0.0.1:8000/dev/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        const data = await response.json();

        if (response.ok) {
            localStorage.setItem("user", JSON.stringify(data));
            localStorage.setItem("role", "developer"); // 👈 useful later
            window.location.href = "dev_main.html";
        } else {
            alert("Login Failed: " + data.detail);
        }

    } catch (error) {
        console.error(error);
        alert("Could not connect to server.");
    }
}