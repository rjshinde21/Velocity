#!/bin/bash

# Deployment Configuration
APP_NAME="python-api"
APP_DIR="/var/www/${APP_NAME}"
LOG_FILE="/var/log/flaskapp.log"
BIND_ADDRESS="127.0.0.1:2000"
WORKERS=2
TIMEOUT=120

# Logging Functions
log_error() {
    echo "[ERROR] $(date): $1" | tee -a "${LOG_FILE}"
}

log_info() {
    echo "[INFO] $(date): $1" | tee -a "${LOG_FILE}"
}

# Pre-deployment Package Check
check_dependencies() {
    local missing_packages=()
    
    # Check critical packages
    local required_packages=("flask" "gunicorn")
    
    for pkg in "${required_packages[@]}"; do
        if ! python3 -c "import ${pkg}" &>/dev/null; then
            missing_packages+=("${pkg}")
        fi
    done
    
    if [ ${#missing_packages[@]} -gt 0 ]; then
        log_error "Missing Python packages: ${missing_packages[*]}"
        return 1
    fi
    
    return 0
}

# Deployment Function
deploy_application() {
    # Clear previous log
    > "${LOG_FILE}"

    # Kill existing Gunicorn processes
    pkill gunicorn

    cd "${APP_DIR}" || exit 1

    # System-wide package list for debugging
    pip3 list | tee -a "${LOG_FILE}"

    # Enhanced Gunicorn startup
    gunicorn \
        --bind "${BIND_ADDRESS}" \
        --workers "${WORKERS}" \
        --timeout "${TIMEOUT}" \
        --access-logfile "${LOG_FILE}" \
        --error-logfile "${LOG_FILE}" \
        --capture-output \
        --log-level debug \
        --preload \
        app:app
}

# Main Deployment Workflow
main() {
    log_info "Starting system-wide deployment for ${APP_NAME}"

    if ! check_dependencies; then
        log_error "Dependency check failed. Please install missing packages."
        exit 1
    fi

    deploy_application
}

# Execute main function
main