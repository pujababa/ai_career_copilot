document.addEventListener("DOMContentLoaded", () => {
  setupAuthTabs();
  setupLoginValidation();
  setupSidebarToggle();
  setupChatDemo();
  setupAdminApprovals();
  setupSkillAnimation();
  setupCareerRoadmap();
  setupCareerReadinessChart();
  setupPlacementTracker();
  setupCareerQuiz();
});

function setupAuthTabs() {
  const tabsContainer = document.querySelector("[data-auth-tabs]");
  if (!tabsContainer) return;

  const tabs = Array.from(tabsContainer.querySelectorAll("[data-auth-tab]"));
  const panels = Array.from(
    document.querySelectorAll("[data-auth-panel]")
  );

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const target = tab.getAttribute("data-auth-tab");
      tabs.forEach((t) => t.classList.toggle("active", t === tab));
      panels.forEach((panel) => {
        const isMatch =
          panel.getAttribute("data-auth-panel") === target;
        panel.classList.toggle("active", isMatch);
      });
    });
  });

  // Forms submit to Flask backend; no redirect here.
}

function setupLoginValidation() {
  const form = document.querySelector("body.auth-body form[action*='login']");
  if (!form) return;

  const emailInput = document.getElementById("login-email");
  const passwordInput = document.getElementById("login-password");
  const submitButton = form.querySelector('button[type="submit"]');
  const emailError = document.getElementById("login-email-error");
  const passwordError = document.getElementById("login-password-error");

  if (!emailInput || !passwordInput || !submitButton) return;
  const errEl = emailError || document.createElement("p");
  const pwdErrEl = passwordError || document.createElement("p");

  function showError(input, errorEl, message) {
    if (errorEl) {
      input.classList.add("input-error");
      errorEl.textContent = message;
    }
  }

  function clearError(input, errorEl) {
    if (errorEl) {
      input.classList.remove("input-error");
      errorEl.textContent = "";
    }
  }

  form.addEventListener("submit", (event) => {
    let isValid = true;
    clearError(emailInput, emailError);
    clearError(passwordInput, passwordError);

    const emailValue = emailInput.value.trim();
    const passwordValue = passwordInput.value.trim();

    if (!emailValue) {
      showError(emailInput, emailError, "Email is required.");
      isValid = false;
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailValue)) {
      showError(emailInput, emailError, "Enter a valid email address.");
      isValid = false;
    }
    if (!passwordValue) {
      showError(passwordInput, passwordError, "Password is required.");
      isValid = false;
    } else if (passwordValue.length < 6) {
      showError(passwordInput, passwordError, "Password must be at least 6 characters.");
      isValid = false;
    }

    if (!isValid) event.preventDefault();
    else {
      submitButton.disabled = true;
      submitButton.classList.add("btn-loading");
    }
  });

  [emailInput, passwordInput].forEach((input) => {
    input.addEventListener("input", () => {
      const errorEl = input === emailInput ? emailError : passwordError;
      if (errorEl && errorEl.textContent) clearError(input, errorEl);
    });
  });
}

function setupSidebarToggle() {
  const sidebar = document.querySelector("[data-sidebar]");
  const toggle = document.querySelector("[data-sidebar-toggle]");
  if (!sidebar || !toggle) return;

  toggle.addEventListener("click", () => {
    sidebar.classList.toggle("is-open");
  });

  sidebar.addEventListener("click", (event) => {
    if (window.innerWidth > 800) return;
    const target = event.target;
    if (target.tagName === "A" || target.closest("a")) {
      sidebar.classList.remove("is-open");
    }
  });
}

function setupChatDemo() {
  const form = document.querySelector("[data-chat-form]");
  const textarea = form?.querySelector("textarea");
  const messages = document.querySelector("[data-chat-messages]");
  const quickPrompts = document.querySelectorAll("[data-demo-prompt]");
  const typingIndicator = document.querySelector("[data-typing-indicator]");

  if (!form || !textarea || !messages) return;

  const apiUrl = form.getAttribute("data-chat-api-url");
  const userInitials = form.getAttribute("data-user-initials") || "U";

  function sendMessage() {
    const text = textarea.value.trim();
    if (!text) return;

    appendMessage(messages, {
      role: "user",
      author: "You",
      initials: userInitials,
      text,
    });

    textarea.value = "";
    autoResizeTextarea(textarea);

    if (typingIndicator) {
      typingIndicator.hidden = false;
    }

    if (apiUrl) {
      fetch(apiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
        credentials: "same-origin",
      })
        .then((res) => res.json())
        .then((data) => {
          setTimeout(() => {
            if (typingIndicator) typingIndicator.hidden = true;
            appendMessage(messages, {
              role: "bot",
              author: "AI Career Copilot",
              initials: "AI",
              text: data.response || "Sorry, something went wrong.",
            });
          }, 1200);
        })
        .catch(() => {
          if (typingIndicator) typingIndicator.hidden = true;
          appendMessage(messages, {
            role: "bot",
            author: "AI Career Copilot",
            initials: "AI",
            text: "Sorry, I couldn't process that. Please try again.",
          });
        });
    } else {
      const demoReply =
        "This is a demo. In a real product, messages would be sent to an AI backend.";
      setTimeout(() => {
        if (typingIndicator) typingIndicator.hidden = true;
        appendMessage(messages, {
          role: "bot",
          author: "AI Career Copilot",
          initials: "AI",
          text: demoReply,
        });
      }, 600);
    }
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    sendMessage();
  });

  textarea.addEventListener("input", () => autoResizeTextarea(textarea));
  autoResizeTextarea(textarea);

  textarea.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  });

  quickPrompts.forEach((button) => {
    button.addEventListener("click", () => {
      const text = button.textContent?.trim() || "";
      if (!text) return;
      textarea.value = text;
      autoResizeTextarea(textarea);
      textarea.focus();
    });
  });
}

function setupAdminApprovals() {
  const table = document.querySelector("[data-pending-approvals]");
  if (!table) return;

  const badge = document.querySelector("[data-pending-count]");

  function updateBadge() {
    const count = table.querySelectorAll("tbody tr[data-pending-user]").length;
    if (!badge) return;
    if (count === 0) {
      badge.textContent = "No pending";
    } else if (count === 1) {
      badge.textContent = "1 pending";
    } else {
      badge.textContent = `${count} pending`;
    }
  }

  table.querySelectorAll("tbody tr[data-pending-user]").forEach((row) => {
    const approveBtn = row.querySelector("[data-approve]");
    const rejectBtn = row.querySelector("[data-reject]");
    const actionsCell = row.querySelector("[data-actions]");

    approveBtn?.addEventListener("click", () => {
      if (!actionsCell) return;
      actionsCell.innerHTML =
        '<span class="pill pill-good">Approved</span>';
      row.removeAttribute("data-pending-user");
      updateBadge();
    });

    rejectBtn?.addEventListener("click", () => {
      row.remove();
      updateBadge();
    });
  });

  updateBadge();
}

function appendMessage(container, { role, author, initials, text }) {
  const message = document.createElement("div");
  message.className = `message ${role === "user" ? "user" : "bot"}`;

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.textContent = (initials || author || "?").slice(0, 2).toUpperCase();

  const content = document.createElement("div");
  content.className = "message-content";

  const authorEl = document.createElement("div");
  authorEl.className = "message-author";
  authorEl.textContent = author || (role === "user" ? "You" : "AI Career Copilot");

  const paragraph = document.createElement("p");
  paragraph.textContent = text;

  content.appendChild(authorEl);
  content.appendChild(paragraph);

  message.appendChild(avatar);
  message.appendChild(content);

  container.appendChild(message);
  container.scrollTop = container.scrollHeight;
}

function autoResizeTextarea(textarea) {
  textarea.style.height = "auto";
  textarea.style.height = textarea.scrollHeight + "px";
}

function setupSkillAnimation() {
  const skillRows = document.querySelectorAll(
    "#skill-gap .skill-row[data-skill-target]"
  );
  if (!skillRows.length) return;

  function animate() {
    skillRows.forEach((row) => {
      const bar = row.querySelector("[data-skill-bar]");
      const target = parseInt(
        row.getAttribute("data-skill-target") || "0",
        10
      );
      if (!bar || isNaN(target)) return;
      bar.style.transition = "width 0.9s ease-out";
      bar.style.width = `${target}%`;
    });
  }

  if (document.readyState === "complete") {
    requestAnimationFrame(animate);
  } else {
    window.addEventListener("load", animate, { once: true });
  }
}

function setupCareerRoadmap() {
  const select = document.querySelector("[data-roadmap-select]");
  const stepsContainer = document.querySelector("[data-roadmap-steps]");
  const titleEl = document.querySelector("[data-roadmap-title]");
  const introEl = document.querySelector("[data-roadmap-intro]");
  const badgeEl = document.querySelector("[data-roadmap-badge]");

  if (!select || !stepsContainer || !titleEl || !introEl || !badgeEl) return;

  const ROADMAPS = {
    "data-scientist": {
      title: "Data Scientist roadmap",
      intro:
        "Foundational path for students moving into applied data science roles.",
      steps: [
        "Learn Python basics and data types.",
        "Study statistics and probability for data work.",
        "Practice data analysis with Pandas and NumPy.",
        "Learn machine learning fundamentals and common algorithms.",
        "Build 2–3 end-to-end portfolio projects.",
        "Apply for internships and entry-level roles.",
      ],
    },
    "web-developer": {
      title: "Web Developer roadmap",
      intro:
        "Front-end focused path with a gradual introduction to back-end concepts.",
      steps: [
        "Learn HTML, CSS, and responsive layouts.",
        "Master JavaScript fundamentals and the DOM.",
        "Build static websites and small interactive projects.",
        "Learn basic backend concepts (HTTP, APIs, JSON).",
        "Create a personal portfolio site with multiple projects.",
        "Apply for internships or freelance opportunities.",
      ],
    },
    "ai-engineer": {
      title: "AI Engineer roadmap",
      intro:
        "Path for students who want to work on deploying and integrating AI systems.",
      steps: [
        "Build strong Python and software engineering fundamentals.",
        "Learn linear algebra, calculus, and probability for ML.",
        "Study deep learning frameworks (PyTorch or TensorFlow).",
        "Experiment with pretrained models and fine-tuning.",
        "Learn how to deploy models with APIs and simple cloud services.",
        "Contribute to open-source or build a capstone AI project.",
      ],
    },
    "software-developer": {
      title: "Software Developer roadmap",
      intro:
        "Generalist path focused on problem solving and building real applications.",
      steps: [
        "Learn one primary programming language in depth.",
        "Study data structures and algorithms for interviews.",
        "Understand version control (Git) and collaboration workflows.",
        "Build small CLI or web apps to solidify concepts.",
        "Learn basic system design and architecture patterns.",
        "Apply for internships and participate in coding interviews.",
      ],
    },
  };

  function renderRoadmap(key) {
    const config = ROADMAPS[key];
    stepsContainer.innerHTML = "";

    if (!config) {
      titleEl.textContent = "Pick a goal to see your roadmap";
      introEl.textContent =
        "Choose a career goal on the left to generate a personalised, high-level roadmap with concrete learning steps.";
      badgeEl.textContent = "Interactive · Demo only";
      return;
    }

    titleEl.textContent = config.title;
    introEl.textContent = config.intro;
    badgeEl.textContent = "Generated · Demo only";

    config.steps.forEach((step, index) => {
      const li = document.createElement("li");
      li.className = "roadmap-step";

      const icon = document.createElement("div");
      icon.className = "roadmap-step-icon";
      icon.textContent = index + 1;

      const text = document.createElement("div");
      text.textContent = step;

      li.appendChild(icon);
      li.appendChild(text);

      stepsContainer.appendChild(li);
    });
  }

  select.addEventListener("change", () => {
    const value = select.value;
    renderRoadmap(value);
  });
}

function setupCareerReadinessChart() {
  const canvas = document.getElementById("career-readiness-chart");
  const circleFill = document.getElementById("readiness-circle-fill");
  const scoreValue = document.getElementById("readiness-score-value");

  if (!canvas) return;

  if (circleFill && scoreValue) {
    const READINESS_SCORE = 75;
    const circumference = 2 * Math.PI * 52;
    const offset = circumference - (READINESS_SCORE / 100) * circumference;
    circleFill.setAttribute("stroke-dashoffset", String(offset));
    scoreValue.textContent = `${READINESS_SCORE}%`;
  }

  if (typeof Chart === "undefined") return;

  const skillData = {
    Python: 70,
    "Machine Learning": 40,
    "Data Structures": 60,
    SQL: 50,
    Communication: 80,
  };

  const labels = Object.keys(skillData);
  const values = Object.values(skillData);
  const colors = [
    "rgba(79, 70, 229, 0.85)",
    "rgba(129, 140, 248, 0.85)",
    "rgba(56, 189, 248, 0.85)",
    "rgba(34, 197, 94, 0.85)",
    "rgba(249, 115, 22, 0.85)",
  ];
  const hoverColors = [
    "rgba(79, 70, 229, 1)",
    "rgba(129, 140, 248, 1)",
    "rgba(56, 189, 248, 1)",
    "rgba(34, 197, 94, 1)",
    "rgba(249, 115, 22, 1)",
  ];

  new Chart(canvas, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Readiness %",
          data: values,
          backgroundColor: colors,
          hoverBackgroundColor: hoverColors,
          borderRadius: 8,
          borderSkipped: false,
        },
      ],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "rgba(15, 23, 42, 0.95)",
          titleColor: "#e5e7eb",
          bodyColor: "#9ca3af",
          borderColor: "rgba(148, 163, 184, 0.4)",
          borderWidth: 1,
          padding: 12,
          callbacks: {
            label: (ctx) => ` ${ctx.raw}% readiness`,
          },
        },
      },
      scales: {
        x: {
          min: 0,
          max: 100,
          grid: { color: "rgba(148, 163, 184, 0.15)" },
          ticks: {
            color: "#9ca3af",
            font: { size: 11 },
            callback: (v) => v + "%",
          },
        },
        y: {
          grid: { display: false },
          ticks: {
            color: "#e5e7eb",
            font: { size: 12 },
          },
        },
      },
      animation: {
        duration: 800,
      },
    },
  });
}

const PLACEMENT_STORAGE_KEY = "placement-tracker-checked";
const PLACEMENT_MESSAGES = {
  0: "Start your placement journey! Every step counts.",
  1: "Good start! Keep going.",
  2: "You're making progress. Stay focused!",
  3: "Great! You are getting closer to placement readiness.",
  4: "Excellent progress! You're almost there.",
  5: "Almost done! One more to go.",
  6: "Congratulations! You're placement ready! 🎉",
};

function setupPlacementTracker() {
  const checkboxes = document.querySelectorAll(".placement-checkbox");
  const progressFill = document.getElementById("placement-progress-fill");
  const progressCount = document.getElementById("placement-progress-count");
  const progressPercent = document.getElementById("placement-progress-percent");
  const motivationEl = document.getElementById("placement-motivation");

  if (!checkboxes.length || !progressFill) return;

  function getStored() {
    try {
      const raw = localStorage.getItem(PLACEMENT_STORAGE_KEY);
      if (!raw) return [];
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }

  function saveStored(checked) {
    try {
      localStorage.setItem(PLACEMENT_STORAGE_KEY, JSON.stringify(checked));
    } catch (_) {}
  }

  function updateUI() {
    const checked = Array.from(checkboxes)
      .map((cb, i) => (cb.checked ? i : null))
      .filter((i) => i !== null);
    const count = checked.length;
    const total = checkboxes.length;
    const percent = total ? Math.round((count / total) * 100) : 0;

    progressFill.style.width = `${percent}%`;
    progressFill.style.transition = "width 0.4s ease-out";
    if (progressCount) progressCount.textContent = `${count} / ${total}`;
    if (progressPercent) progressPercent.textContent = `${percent}%`;
    if (motivationEl)
      motivationEl.textContent = PLACEMENT_MESSAGES[count] ?? PLACEMENT_MESSAGES[0];

    saveStored(checked);
  }

  function syncItemState() {
    checkboxes.forEach((cb) => {
      const item = cb.closest(".placement-checklist-item");
      if (item) item.classList.toggle("checked", cb.checked);
    });
  }

  const stored = getStored();
  checkboxes.forEach((cb, i) => {
    cb.checked = stored.includes(i);
    cb.addEventListener("change", () => {
      syncItemState();
      updateUI();
    });
  });
  syncItemState();
  updateUI();
}

const CAREER_RESULTS = {
  "software-developer": {
    title: "Software Developer",
    description:
      "Based on your interest in logical problem-solving and building software, a career as a Software Developer could be a great fit. You'll design, build, and maintain applications that solve real-world problems.",
    skills: ["Programming (Java, Python, JavaScript)", "Data Structures & Algorithms", "Version Control (Git)", "Testing & Debugging", "System Design Basics"],
  },
  "data-scientist": {
    title: "Data Scientist",
    description:
      "Your interest in data analysis and AI suggests you'd thrive as a Data Scientist. You'll extract insights from data, build predictive models, and help organizations make data-driven decisions.",
    skills: ["Python / R", "Statistics & Probability", "Machine Learning", "SQL & Data Processing", "Data Visualization"],
  },
  "frontend-developer": {
    title: "Frontend Developer",
    description:
      "Your interest in UI design and building websites points toward Frontend Development. You'll create engaging, responsive interfaces that users interact with daily.",
    skills: ["HTML, CSS, JavaScript", "React or Vue.js", "Responsive Design", "UI/UX Fundamentals", "Accessibility"],
  },
};

function setupCareerQuiz() {
  const form = document.querySelector("[data-quiz-form]");
  const resultCard = document.getElementById("quiz-result-card");
  const resultTitle = document.getElementById("quiz-result-title");
  const resultDesc = document.getElementById("quiz-result-desc");
  const resultSkills = document.getElementById("quiz-result-skills");

  if (!form || !resultCard) return;

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const q1 = form.querySelector('input[name="q1"]:checked')?.value ?? "no";
    const q2 = form.querySelector('input[name="q2"]:checked')?.value ?? "no";
    const q3 = form.querySelector('input[name="q3"]:checked')?.value ?? "no";
    const q4 = form.querySelector('input[name="q4"]:checked')?.value ?? "no";
    const q5 = form.querySelector('input[name="q5"]:checked')?.value ?? "no";

    const score = (v) => (v === "yes" ? 2 : v === "maybe" ? 1 : 0);
    const s1 = score(q1);
    const s2 = score(q2);
    const s3 = score(q3);
    const s4 = score(q4);
    const s5 = score(q5);

    const softwareScore = s1 + s5;
    const frontendScore = s2 + s5;
    const dataScore = s3 + s4;

    let careerKey = "software-developer";
    const max = Math.max(softwareScore, frontendScore, dataScore);
    if (max === dataScore && dataScore > 0) careerKey = "data-scientist";
    else if (max === frontendScore && frontendScore > 0) careerKey = "frontend-developer";
    else if (max === softwareScore && softwareScore > 0) careerKey = "software-developer";

    const career = CAREER_RESULTS[careerKey];
    resultTitle.textContent = career.title;
    resultDesc.textContent = career.description;
    resultSkills.innerHTML = career.skills.map((s) => `<li>${s}</li>`).join("");

    resultCard.hidden = false;
    resultCard.style.animation = "none";
    resultCard.offsetHeight;
    resultCard.style.animation = "quizResultFadeIn 0.5s ease-out forwards";
    resultCard.scrollIntoView({ behavior: "smooth", block: "start" });
  });
}

