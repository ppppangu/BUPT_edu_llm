// Main JavaScript for Landing Page

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

/**
 * Initialize the application
 */
function initializeApp() {
    updateStats();
    renderProjects();
    startHealthChecks();
}

/**
 * Update platform statistics
 */
function updateStats() {
    const stats = CONFIG.stats;

    // Animate counting for stats
    animateValue('stat-projects', 0, stats.activeProjects, 1500);

    // Set uptime with animation delay
    setTimeout(() => {
        document.getElementById('stat-uptime').textContent = stats.systemUptime;
    }, 500);

    // Set data processed with animation delay
    setTimeout(() => {
        document.getElementById('stat-data').textContent = stats.dataProcessed;
    }, 1000);
}

/**
 * Animate number counting
 */
function animateValue(elementId, start, end, duration) {
    const element = document.getElementById(elementId);
    if (!element) return;

    const range = end - start;
    const increment = range / (duration / 16); // 60 FPS
    let current = start;

    const timer = setInterval(() => {
        current += increment;
        if (current >= end) {
            element.textContent = end;
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(current);
        }
    }, 16);
}

/**
 * Render project cards dynamically
 */
function renderProjects() {
    const container = document.getElementById('projects-container');
    if (!container) return;

    container.innerHTML = '';

    CONFIG.projects.forEach((project, index) => {
        const card = createProjectCard(project, index);
        container.appendChild(card);
    });
}

/**
 * Create a project card element
 */
function createProjectCard(project, index) {
    const card = document.createElement('div');
    card.className = 'project-card';
    card.style.animationDelay = `${index * 0.1}s`;

    const statusClass = project.status === 'online' ? '' : 'offline';
    const statusText = project.status === 'online' ? 'ONLINE' : 'OFFLINE';

    card.innerHTML = `
        <div class="project-header">
            <span class="project-icon">${project.icon}</span>
            <div class="project-status ${statusClass}">
                <span class="project-status-dot"></span>
                <span>${statusText}</span>
            </div>
        </div>

        <h3 class="project-title">${project.name}</h3>
        <p class="project-description">${project.description}</p>

        <div class="project-meta">
            <div class="meta-item">
                <span>📦</span>
                <span>${project.metadata.version}</span>
            </div>
            <div class="meta-item">
                <span>🔄</span>
                <span>${project.metadata.lastUpdate}</span>
            </div>
            <div class="meta-item">
                <span>⚡</span>
                <span>${project.metadata.uptime}</span>
            </div>
        </div>

        <div class="project-tags">
            ${project.tags.map(tag => `<span class="project-tag">${tag}</span>`).join('')}
        </div>

        <a href="${project.path}" class="project-link" ${project.status === 'offline' ? 'style="pointer-events: none; opacity: 0.5;"' : ''}>
            <span>访问项目</span>
            <span>→</span>
        </a>
    `;

    return card;
}

/**
 * Start health check for all projects
 */
function startHealthChecks() {
    // Initial health check
    performHealthChecks();

    // Periodic health checks every 30 seconds
    setInterval(performHealthChecks, 30000);
}

/**
 * Perform health checks on all projects
 */
async function performHealthChecks() {
    for (const project of CONFIG.projects) {
        if (CONFIG.healthCheckEndpoints[project.id]) {
            try {
                const response = await fetch(CONFIG.healthCheckEndpoints[project.id], {
                    method: 'GET',
                    timeout: 5000
                });

                if (response.ok) {
                    updateProjectStatus(project.id, 'online');
                } else {
                    updateProjectStatus(project.id, 'offline');
                }
            } catch (error) {
                // If health check fails, mark as offline
                updateProjectStatus(project.id, 'offline');
            }
        }
    }
}

/**
 * Update project status in the UI
 */
function updateProjectStatus(projectId, status) {
    const projectIndex = CONFIG.projects.findIndex(p => p.id === projectId);
    if (projectIndex === -1) return;

    CONFIG.projects[projectIndex].status = status;

    // Re-render projects if status changed
    renderProjects();
}

/**
 * Add smooth scroll behavior to all internal links
 */
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

/**
 * Add intersection observer for animations on scroll
 */
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe all project cards
document.querySelectorAll('.project-card').forEach(card => {
    observer.observe(card);
});

/**
 * Console easter egg
 */
console.log('%c🎓 BUPT EDU LLM Platform', 'font-size: 20px; font-weight: bold; color: #ff9500;');
console.log('%cWelcome to the Data Intelligence Hub!', 'font-size: 14px; color: #00d4aa;');
console.log('%cBuilt with ❤️ for education and research', 'font-size: 12px; color: #9ba3b4;');
