"""
Advanced Filter CSS with Dropdown Menu
"""

def get_advanced_filter_css() -> str:
    """Return the CSS for the actual dropdown filter menu"""
    return """
    <style>
    .filter-dropdown-container {
        position: fixed;
        top: 80px;
        right: 20px;
        z-index: 9999;
        font-family: 'Source Sans Pro', sans-serif;
    }
    
    .filter-dropdown-trigger {
        background: linear-gradient(90deg, #ff6b6b, #ee5a24);
        color: white;
        padding: 12px 20px;
        border-radius: 25px;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(238, 90, 36, 0.3);
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 600;
        font-size: 14px;
        transition: all 0.3s ease;
        border: none;
        text-decoration: none;
        user-select: none;
    }
    
    .filter-dropdown-trigger:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(238, 90, 36, 0.4);
        background: linear-gradient(90deg, #ee5a24, #ff6b6b);
    }
    
    .filter-dropdown-menu {
        position: absolute;
        top: 50px;
        right: 0;
        background: white;
        border-radius: 12px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
        min-width: 350px;
        max-width: 450px;
        max-height: 70vh;
        overflow-y: auto;
        padding: 0;
        opacity: 0;
        visibility: hidden;
        transform: translateY(-10px);
        transition: all 0.3s ease;
        border: 1px solid #e1e5e9;
        z-index: 10000;
    }
    
    .filter-dropdown-container.active .filter-dropdown-menu {
        opacity: 1;
        visibility: visible;
        transform: translateY(0);
    }
    
    .filter-dropdown-header {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        padding: 16px 20px;
        border-bottom: 1px solid #dee2e6;
        border-radius: 12px 12px 0 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .filter-dropdown-title {
        font-size: 16px;
        font-weight: 700;
        color: #2c3e50;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .filter-dropdown-close {
        background: none;
        border: none;
        font-size: 20px;
        color: #6c757d;
        cursor: pointer;
        padding: 4px;
        border-radius: 4px;
        transition: all 0.2s ease;
    }
    
    .filter-dropdown-close:hover {
        background: #dee2e6;
        color: #495057;
    }
    
    .filter-dropdown-content {
        padding: 20px;
        max-height: 50vh;
        overflow-y: auto;
    }
    
    .filter-section {
        margin-bottom: 20px;
        padding-bottom: 15px;
        border-bottom: 1px solid #f1f3f4;
    }
    
    .filter-section:last-child {
        border-bottom: none;
        margin-bottom: 0;
    }
    
    .filter-section-title {
        font-size: 13px;
        font-weight: 600;
        color: #495057;
        margin-bottom: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .filter-control {
        margin-bottom: 12px;
    }
    
    .filter-control label {
        font-size: 14px;
        color: #495057;
        margin-bottom: 6px;
        display: block;
        font-weight: 500;
    }
    
    .filter-control select,
    .filter-control input[type="date"],
    .filter-control input[type="text"] {
        width: 100%;
        padding: 8px 12px;
        border: 1px solid #ced4da;
        border-radius: 6px;
        font-size: 14px;
        transition: border-color 0.2s ease;
        box-sizing: border-box;
    }
    
    .filter-control select:focus,
    .filter-control input:focus {
        outline: none;
        border-color: #80bdff;
        box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
    }
    
    .filter-control input[type="checkbox"] {
        margin-right: 8px;
    }
    
    .filter-status {
        background: #e3f2fd;
        padding: 12px;
        border-radius: 8px;
        margin-top: 15px;
        font-size: 13px;
        color: #1565c0;
        border-left: 4px solid #2196f3;
    }
    
    .clear-filters-btn {
        background: #dc3545;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 6px;
        font-size: 12px;
        cursor: pointer;
        margin-top: 10px;
        transition: background-color 0.2s ease;
        width: 100%;
    }
    
    .clear-filters-btn:hover {
        background: #c82333;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .filter-dropdown-container {
            position: relative;
            top: auto;
            right: auto;
            margin-bottom: 20px;
            width: 100%;
        }
        
        .filter-dropdown-trigger {
            justify-content: center;
            width: 100%;
        }
        
        .filter-dropdown-menu {
            position: relative;
            top: 10px;
            right: auto;
            left: 0;
            width: 100%;
            max-width: none;
            margin: 0;
        }
        
        .filter-dropdown-container.active .filter-dropdown-menu {
            opacity: 1;
            visibility: visible;
            transform: translateY(0);
        }
    }
    
    /* Overlay for mobile */
    .filter-dropdown-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.3);
        z-index: 9999;
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s ease;
    }
    
    .filter-dropdown-overlay.active {
        opacity: 1;
        visibility: visible;
    }
    
    @media (min-width: 769px) {
        .filter-dropdown-overlay {
            display: none;
        }
    }
    </style>
    """

def get_filter_js() -> str:
    """Return JavaScript for dropdown functionality"""
    return """
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        const container = document.querySelector('.filter-dropdown-container');
        const trigger = document.querySelector('.filter-dropdown-trigger');
        const closeBtn = document.querySelector('.filter-dropdown-close');
        const overlay = document.querySelector('.filter-dropdown-overlay');
        
        if (trigger) {
            trigger.addEventListener('click', function(e) {
                e.stopPropagation();
                container.classList.toggle('active');
                if (overlay) overlay.classList.toggle('active');
            });
        }
        
        if (closeBtn) {
            closeBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                container.classList.remove('active');
                if (overlay) overlay.classList.remove('active');
            });
        }
        
        if (overlay) {
            overlay.addEventListener('click', function() {
                container.classList.remove('active');
                overlay.classList.remove('active');
            });
        }
        
        // Close on escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && container.classList.contains('active')) {
                container.classList.remove('active');
                if (overlay) overlay.classList.remove('active');
            }
        });
        
        // Prevent menu from closing when clicking inside
        const menu = document.querySelector('.filter-dropdown-menu');
        if (menu) {
            menu.addEventListener('click', function(e) {
                e.stopPropagation();
            });
        }
    });
    </script>
    """
