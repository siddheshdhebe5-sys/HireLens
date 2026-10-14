/**
 * ResumeAI - Frontend Interactive Logic
 */

// Dropzone Drag & Drop Handling
document.addEventListener('DOMContentLoaded', () => {
    const dropzone = document.getElementById('resume-dropzone');
    const fileInput = document.getElementById('resume_file');

    if (dropzone && fileInput) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, () => dropzone.classList.add('dragover'), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, () => dropzone.classList.remove('dragover'), false);
        });

        dropzone.addEventListener('drop', handleDrop, false);
    }
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) {
        const fileInput = document.getElementById('resume_file');
        fileInput.files = files;
        handleFileSelected(fileInput);
    }
}

function handleFileSelected(input) {
    if (input.files && input.files[0]) {
        const file = input.files[0];
        const validExtensions = ['pdf', 'docx'];
        const ext = file.name.split('.').pop().toLowerCase();

        if (!validExtensions.includes(ext)) {
            alert('Please select a valid PDF or DOCX file.');
            input.value = '';
            return;
        }

        if (file.size > 5 * 1024 * 1024) {
            alert('File size exceeds 5MB limit. Please upload a smaller file.');
            input.value = '';
            return;
        }

        // Display selected file info
        const dropContent = document.getElementById('dropzone-content');
        const selectedBox = document.getElementById('selected-file-box');
        const fileNameEl = document.getElementById('selected-file-name');
        const fileSizeEl = document.getElementById('selected-file-size');

        if (dropContent && selectedBox) {
            dropContent.style.display = 'none';
            selectedBox.style.display = 'flex';
            fileNameEl.textContent = file.name;
            fileSizeEl.textContent = formatBytes(file.size);
        }
    }
}

function removeSelectedFile(event) {
    if (event) {
        event.stopPropagation();
    }
    const fileInput = document.getElementById('resume_file');
    const dropContent = document.getElementById('dropzone-content');
    const selectedBox = document.getElementById('selected-file-box');

    if (fileInput) fileInput.value = '';
    if (dropContent) dropContent.style.display = 'block';
    if (selectedBox) selectedBox.style.display = 'none';
}

function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// Manual Textarea Toggle
function toggleManualPaste() {
    const pasteContainer = document.getElementById('paste-container');
    const toggleIcon = document.getElementById('toggle-icon');
    if (!pasteContainer) return;

    if (pasteContainer.style.display === 'none' || pasteContainer.style.display === '') {
        pasteContainer.style.display = 'block';
        if (toggleIcon) toggleIcon.textContent = '▾';
    } else {
        pasteContainer.style.display = 'none';
        if (toggleIcon) toggleIcon.textContent = '▸';
    }
}

// Counters
function updateResumeCounter() {
    const text = document.getElementById('resume_text')?.value || '';
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    const chars = text.length;

    const wordEl = document.getElementById('resume-word-count');
    const charEl = document.getElementById('resume-char-count');
    if (wordEl) wordEl.textContent = `${words} words`;
    if (charEl) charEl.textContent = `${chars} characters`;
}

function updateJobCounter() {
    const text = document.getElementById('job_description')?.value || '';
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    const chars = text.length;

    const wordEl = document.getElementById('job-word-count');
    const charEl = document.getElementById('job-char-count');
    if (wordEl) wordEl.textContent = `${words} words`;
    if (charEl) charEl.textContent = `${chars} characters`;
}

// Load Safe Sample Data for Quick Demonstrations
function loadSampleData() {
    if (typeof SAMPLE_CANDIDATE_TEXT !== 'undefined' && typeof SAMPLE_JOB_TEXT !== 'undefined') {
        const resumeInput = document.getElementById('resume_text');
        const jobInput = document.getElementById('job_description');
        const pasteContainer = document.getElementById('paste-container');
        const toggleIcon = document.getElementById('toggle-icon');

        // Show manual textarea
        if (pasteContainer) pasteContainer.style.display = 'block';
        if (toggleIcon) toggleIcon.textContent = '▾';

        // Clear file input if any
        removeSelectedFile();

        // Populate sample text
        if (resumeInput) resumeInput.value = SAMPLE_CANDIDATE_TEXT;
        if (jobInput) jobInput.value = SAMPLE_JOB_TEXT;

        updateResumeCounter();
        updateJobCounter();

        // Scroll to form
        document.getElementById('analyzer-form')?.scrollIntoView({ behavior: 'smooth' });
    }
}

// Form Submit Validation & Loading Animation
function handleFormSubmit(e) {
    const fileInput = document.getElementById('resume_file');
    const resumeText = document.getElementById('resume_text')?.value.trim() || '';
    const jobText = document.getElementById('job_description')?.value.trim() || '';

    const hasFile = fileInput && fileInput.files && fileInput.files.length > 0;
    const hasResumeText = resumeText.length >= 20;

    if (!hasFile && !hasResumeText) {
        alert('Please upload a PDF/DOCX resume file or paste your resume text to continue.');
        return false;
    }

    if (jobText.length < 20) {
        alert('Please paste the complete job description (at least 20 characters) to analyze against.');
        return false;
    }

    // Show loading overlay
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.display = 'flex';
        animateLoadingSteps();
    }

    return true;
}

function animateLoadingSteps() {
    const steps = [
        { title: "Parsing Resume Document...", desc: "Extracting sections, contact info, and education..." },
        { title: "Identifying Core Skills...", desc: "Scanning technical tools, languages, and soft competencies..." },
        { title: "Computing Alignment Score...", desc: "Evaluating TF-IDF semantic overlap and keyword alignment..." }
    ];

    let currentStep = 0;
    const titleEl = document.getElementById('loading-step-title');
    const descEl = document.getElementById('loading-step-desc');

    const interval = setInterval(() => {
        currentStep++;
        if (currentStep < steps.length) {
            if (titleEl) titleEl.textContent = steps[currentStep].title;
            if (descEl) descEl.textContent = steps[currentStep].desc;
        } else {
            clearInterval(interval);
        }
    }, 900);
}

// Copy to Clipboard Helpers
function copyToClipboard(elementId, buttonElement) {
    const el = document.getElementById(elementId);
    if (!el) return;

    const textToCopy = el.innerText || el.textContent;
    navigator.clipboard.writeText(textToCopy).then(() => {
        const originalHTML = buttonElement.innerHTML;
        buttonElement.innerHTML = `<span>✓ Copied!</span>`;
        buttonElement.classList.add('btn-success-temporary');

        setTimeout(() => {
            buttonElement.innerHTML = originalHTML;
            buttonElement.classList.remove('btn-success-temporary');
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy text: ', err);
    });
}

function copyText(text, buttonElement) {
    navigator.clipboard.writeText(text).then(() => {
        const originalText = buttonElement.textContent;
        buttonElement.textContent = '✓ Copied';
        setTimeout(() => {
            buttonElement.textContent = originalText;
        }, 2000);
    });
}

// ==========================================================================
// Mobile Navigation Toggle
// ==========================================================================
function toggleMobileMenu() {
    const nav = document.getElementById('site-nav');
    const toggle = document.getElementById('mobile-menu-toggle');
    if (!nav) return;
    const isOpen = nav.classList.toggle('mobile-open');
    toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    // Prevent body scroll when menu is open
    document.body.style.overflow = isOpen ? 'hidden' : '';
}

// Close mobile menu when clicking a nav link
document.addEventListener('DOMContentLoaded', () => {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            const nav = document.getElementById('site-nav');
            if (nav && nav.classList.contains('mobile-open')) {
                nav.classList.remove('mobile-open');
                document.body.style.overflow = '';
            }
        });
    });
});

// ==========================================================================
// Password Show / Hide Toggle
// ==========================================================================
function togglePasswordVisibility(inputId, buttonEl) {
    const input = document.getElementById(inputId);
    if (!input) return;
    const isHidden = input.type === 'password';
    input.type = isHidden ? 'text' : 'password';
    // Update icon
    const svg = buttonEl.querySelector('svg');
    if (svg) {
        if (isHidden) {
            // Eye-off icon
            svg.innerHTML = '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/>';
        } else {
            // Eye icon
            svg.innerHTML = '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>';
        }
    }
}

// ==========================================================================
// Admin Sidebar Mobile Toggle
// ==========================================================================
function toggleAdminSidebar() {
    const sidebar = document.getElementById('admin-sidebar');
    if (!sidebar) return;
    sidebar.classList.toggle('mobile-visible');
}

// Clean up any client storage when logging out
document.addEventListener('DOMContentLoaded', () => {
    const logoutBtns = document.querySelectorAll('#nav-logout-btn, #admin-nav-logout, .admin-nav-logout, #profile-link-logout');
    logoutBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            try {
                localStorage.clear();
                sessionStorage.clear();
            } catch (e) {}
        });
    });
});

