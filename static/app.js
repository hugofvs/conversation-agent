const form = document.getElementById("chat-form");
const input = document.getElementById("input");
const messages = document.getElementById("messages");

let sessionId = null;

const STEP_ORDER = ["profile", "food", "anime", "done"];
const STEP_IDS = { profile: "step-profile", food: "step-food", anime: "step-anime" };

function addMessage(role, text) {
  const wrapper = document.createElement("div");
  wrapper.className = role === "user" ? "flex justify-end" : "flex justify-start";

  const bubble = document.createElement("div");
  bubble.className =
    role === "user"
      ? "bg-blue-600 text-white rounded-2xl rounded-br-sm px-4 py-2 max-w-[75%]"
      : "bg-white text-gray-800 rounded-2xl rounded-bl-sm px-4 py-2 max-w-[75%] shadow";

  bubble.textContent = text;
  wrapper.appendChild(bubble);
  messages.appendChild(wrapper);
  messages.scrollTop = messages.scrollHeight;
  return wrapper;
}

function appendSources(wrapper, sources) {
  if (!sources || sources.length === 0) return;

  const container = document.createElement("div");
  container.className = "mt-1 flex justify-start";

  const inner = document.createElement("div");
  inner.className = "text-xs text-gray-400 max-w-[75%]";
  inner.innerHTML = sources
    .map((s) => `<span class="inline-block mr-2">[ ${s.title} ]</span>`)
    .join("");

  container.appendChild(inner);
  messages.appendChild(container);
}

function updateStepProgress(currentStep) {
  const currentIdx = STEP_ORDER.indexOf(currentStep);

  for (const [step, elId] of Object.entries(STEP_IDS)) {
    const el = document.getElementById(elId);
    const stepIdx = STEP_ORDER.indexOf(step);

    // Reset classes
    el.className = "step-pill px-3 py-1 rounded-full text-sm font-medium border";

    if (stepIdx < currentIdx) {
      // Completed
      el.classList.add("bg-green-100", "text-green-700", "border-green-300");
    } else if (stepIdx === currentIdx) {
      // Active
      el.classList.add("bg-blue-100", "text-blue-700", "border-blue-300");
    } else {
      // Pending
      el.classList.add("bg-gray-100", "text-gray-500", "border-gray-300");
    }
  }
}

function setFormEnabled(enabled) {
  input.disabled = !enabled;
  form.querySelector("button").disabled = !enabled;
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;

  addMessage("user", text);
  input.value = "";
  setFormEnabled(false);

  // Show typing indicator
  const typingWrapper = addMessage("assistant", "...");

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, session_id: sessionId }),
    });

    if (!res.ok) {
      const err = await res.text();
      throw new Error(err);
    }

    const data = await res.json();

    // Update session
    sessionId = data.session_id;

    // Update step progress
    updateStepProgress(data.state.current_step);

    // Replace typing indicator with actual message
    const bubble = typingWrapper.querySelector("div");
    bubble.textContent = data.response.message;

    // Show RAG sources if present
    appendSources(typingWrapper, data.response.sources);

    messages.scrollTop = messages.scrollHeight;
  } catch (err) {
    const bubble = typingWrapper.querySelector("div");
    bubble.textContent = "Error: " + err.message;
    bubble.classList.add("text-red-600");
  } finally {
    setFormEnabled(true);
    input.focus();
  }
});
