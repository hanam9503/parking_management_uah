// ============================================
// PARKING MANAGEMENT SYSTEM - MAIN JS
// ============================================

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Parking Management System Initialized');
    
    // Initialize all components
    initCounterAnimations();
    initTooltips();
    initConfirmDialogs();
    initAutoRefresh();
    initRealTimeClock();
    initSearchFilters();
    initFormValidation();
});

// ============================================
// COUNTER ANIMATIONS
// ============================================
function initCounterAnimations() {
    const counters = document.querySelectorAll('.counter, .text-3xl, .text-4xl, .text-5xl');
    
    counters.forEach(counter => {
        const target = parseInt(counter.innerText) || 0;
        if (target === 0) return;
        
        const duration = 1000; // 1 second
        const step = target / (duration / 16); // 60fps
        let current = 0;
        
        const timer = setInterval(() => {
            current += step;
            if (current >= target) {
                counter.innerText = target;
                clearInterval(timer);
            } else {
                counter.innerText = Math.floor(current);
            }
        }, 16);
    });
}

// ============================================
// TOOLTIPS
// ============================================
function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', function() {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.innerText = this.getAttribute('data-tooltip');
            tooltip.style.cssText = `
                position: absolute;
                background: #1f2937;
                color: white;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 14px;
                z-index: 9999;
                pointer-events: none;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            `;
            
            document.body.appendChild(tooltip);
            
            const rect = this.getBoundingClientRect();
            tooltip.style.top = (rect.top - tooltip.offsetHeight - 8) + 'px';
            tooltip.style.left = (rect.left + rect.width / 2 - tooltip.offsetWidth / 2) + 'px';
            
            this.tooltipElement = tooltip;
        });
        
        element.addEventListener('mouseleave', function() {
            if (this.tooltipElement) {
                this.tooltipElement.remove();
                this.tooltipElement = null;
            }
        });
    });
}

// ============================================
// CONFIRM DIALOGS
// ============================================
function initConfirmDialogs() {
    const deleteButtons = document.querySelectorAll('a[onclick*="confirm"]');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const confirmed = confirm('⚠️ Bạn có chắc chắn muốn xóa? Hành động này không thể hoàn tác.');
            if (!confirmed) {
                e.preventDefault();
                return false;
            }
        });
    });
}

// ============================================
// AUTO REFRESH
// ============================================
function initAutoRefresh() {
    // Auto refresh parking dashboard every 30 seconds
    if (window.location.pathname.includes('dashboard')) {
        setInterval(() => {
            const stats = document.querySelectorAll('.stat-value');
            stats.forEach(stat => {
                // Add pulse animation
                stat.classList.add('badge-pulse');
                setTimeout(() => {
                    stat.classList.remove('badge-pulse');
                }, 1000);
            });
        }, 30000);
    }
}

// ============================================
// REAL-TIME CLOCK
// ============================================
function initRealTimeClock() {
    const clockElements = document.querySelectorAll('#current-time, .live-clock');
    
    if (clockElements.length > 0) {
        function updateClock() {
            const now = new Date();
            const timeString = now.toLocaleTimeString('vi-VN', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            
            clockElements.forEach(element => {
                element.textContent = timeString;
            });
        }
        
        updateClock();
        setInterval(updateClock, 1000);
    }
}

// ============================================
// SEARCH & FILTER
// ============================================
function initSearchFilters() {
    const searchInput = document.querySelector('input[type="search"], input[placeholder*="Tìm"]');
    
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const rows = document.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
}

// ============================================
// FORM VALIDATION
// ============================================
function initFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = this.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('border-red-500');
                    
                    // Add error message
                    if (!field.nextElementSibling || !field.nextElementSibling.classList.contains('error-message')) {
                        const error = document.createElement('p');
                        error.className = 'error-message text-red-500 text-sm mt-1';
                        error.textContent = 'Trường này không được để trống';
                        field.parentNode.insertBefore(error, field.nextSibling);
                    }
                } else {
                    field.classList.remove('border-red-500');
                    const errorMsg = field.nextElementSibling;
                    if (errorMsg && errorMsg.classList.contains('error-message')) {
                        errorMsg.remove();
                    }
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                showToast('Vui lòng điền đầy đủ thông tin', 'error');
            }
        });
    });
}

// ============================================
// TOAST NOTIFICATIONS
// ============================================
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    }[type] || 'ℹ';
    
    toast.innerHTML = `
        <div class="flex items-center">
            <span class="text-2xl mr-3">${icon}</span>
            <span class="flex-1">${message}</span>
            <button class="ml-4 text-gray-400 hover:text-gray-600" onclick="this.parentElement.parentElement.remove()">
                ✕
            </button>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

// Format number with thousand separator
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Đã copy vào clipboard', 'success');
    }).catch(() => {
        showToast('Không thể copy', 'error');
    });
}

// Download QR Code
function downloadQR(vehiclePlate) {
    const qrImage = document.querySelector('.qr-image');
    if (!qrImage) return;
    
    const link = document.createElement('a');
    link.download = `QR_${vehiclePlate}.png`;
    link.href = qrImage.src;
    link.click();
    
    showToast('Đang tải xuống...', 'success');
}

// Print QR Code
function printQR() {
    window.print();
}

// ============================================
// PARKING OPERATIONS
// ============================================

// Check-in confirmation
function confirmCheckin(vehiclePlate) {
    return confirm(`Xác nhận check-in xe ${vehiclePlate}?`);
}

// Check-out confirmation
function confirmCheckout(vehiclePlate) {
    return confirm(`Xác nhận check-out xe ${vehiclePlate}?`);
}

// ============================================
// STATISTICS UPDATE
// ============================================
function updateStatistics() {
    // This would typically call an API endpoint
    console.log('Updating statistics...');
    
    // Simulate update with animation
    const statCards = document.querySelectorAll('.stat-card');
    statCards.forEach(card => {
        card.style.transform = 'scale(1.05)';
        setTimeout(() => {
            card.style.transform = 'scale(1)';
        }, 200);
    });
}

// ============================================
// LICENSE PLATE INPUT FORMATTER
// ============================================
function formatLicensePlate(input) {
    // Auto-format license plate as user types
    let value = input.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
    
    // Format: 29K1-12345 or 30A-12345
    if (value.length > 4) {
        value = value.slice(0, 4) + '-' + value.slice(4);
    }
    
    input.value = value;
}

// Add event listeners to license plate inputs
document.addEventListener('DOMContentLoaded', function() {
    const licensePlateInputs = document.querySelectorAll('input[name="license_plate"]');
    licensePlateInputs.forEach(input => {
        input.addEventListener('input', function() {
            formatLicensePlate(this);
        });
    });
});

// ============================================
// EXPORT DATA
// ============================================
function exportToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const rowData = Array.from(cols).map(col => col.textContent.trim());
        csv.push(rowData.join(','));
    });
    
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename || 'export.csv';
    link.click();
    
    showToast('Đã xuất dữ liệu', 'success');
}

// ============================================
// KEYBOARD SHORTCUTS
// ============================================
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K: Focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('input[type="search"]');
        if (searchInput) searchInput.focus();
    }
    
    // ESC: Close modals
    if (e.key === 'Escape') {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => modal.style.display = 'none');
    }
});

// ============================================
// CONSOLE EASTER EGG
// ============================================
console.log('%c🚗 Parking Management System', 'font-size: 20px; color: #2563eb; font-weight: bold;');
console.log('%cĐược phát triển bởi UAH Team', 'color: #64748b;');
console.log('%cVersion: 1.0.0', 'color: #64748b;');