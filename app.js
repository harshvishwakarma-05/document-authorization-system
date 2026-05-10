const loginView = document.querySelector("#loginView");
const appView = document.querySelector("#appView");
const loginForm = document.querySelector("#loginForm");
const usernameInput = document.querySelector("#username");
const passwordInput = document.querySelector("#password");
const loginMessage = document.querySelector("#loginMessage");
const logoutBtn = document.querySelector("#logoutBtn");
const currentUser = document.querySelector("#currentUser");
const ownerName = document.querySelector("#ownerName");
const documentTitle = document.querySelector("#documentTitle");
const documentFile = document.querySelector("#documentFile");
const fileLabel = document.querySelector("#fileLabel");
const registerBtn = document.querySelector("#registerBtn");
const verifyBtn = document.querySelector("#verifyBtn");
const resultCard = document.querySelector("#resultCard");
const hashOutput = document.querySelector("#hashOutput");
const ledgerList = document.querySelector("#ledgerList");

documentFile.addEventListener("change", () => {
  const file = documentFile.files[0];
  fileLabel.textContent = file ? file.name : "Choose a document";
});

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const response = await apiRequest("/api/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username: usernameInput.value.trim(),
      password: passwordInput.value
    })
  });

  if (!response.ok) {
    loginMessage.textContent = response.data.message || "Login failed.";
    return;
  }

  loginMessage.textContent = "";
  passwordInput.value = "";
  showApp(response.data.username);
  await loadLedger();
});

logoutBtn.addEventListener("click", async () => {
  await apiRequest("/api/logout", { method: "POST" });
  showLogin();
});

registerBtn.addEventListener("click", async () => {
  const formData = getDocumentFormData();
  if (!formData) return;

  const response = await apiRequest("/api/register", {
    method: "POST",
    body: formData
  });

  updateFromResponse(response);
  if (response.ok) {
    await loadLedger();
  }
});

verifyBtn.addEventListener("click", async () => {
  const formData = getDocumentFormData();
  if (!formData) return;

  const response = await apiRequest("/api/verify", {
    method: "POST",
    body: formData
  });

  updateFromResponse(response);
});

async function initialize() {
  const response = await apiRequest("/api/me");
  if (response.ok && response.data.authenticated) {
    showApp(response.data.username);
    await loadLedger();
    return;
  }

  showLogin();
}

function getDocumentFormData() {
  const file = documentFile.files[0];
  if (!ownerName.value.trim() || !documentTitle.value.trim() || !file) {
    showResult("danger", "Missing details", "Please enter owner, title, and select a file.");
    return null;
  }

  const formData = new FormData();
  formData.append("owner", ownerName.value.trim());
  formData.append("title", documentTitle.value.trim());
  formData.append("document", file);