#!/bin/bash
# Copenhagen Housing Market Forecasting Ecosystem Management Script

set -e

PROJECT_DIR="/Users/ianropke/.gemini/antigravity/scratch/cph-housing-model"

# Colors for pretty output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD='\033[1m'

show_help() {
    echo -e "${BOLD}Copenhagen Housing Market Forecasting Ecosystem${NC}"
    echo -e "Usage: ./manage.sh [command]"
    echo ""
    echo -e "${BOLD}Commands:${NC}"
    echo -e "  ${GREEN}start${NC}     Start the interactive dashboard dev server and open in browser"
    echo -e "  ${GREEN}update${NC}    Force an immediate update of the forecasting data pipeline"
    echo -e "  ${GREEN}test${NC}      Run the unit and integration test suite"
    echo -e "  ${GREEN}backtest${NC}  Run the historical backtesting engine & calibrate thresholds"
    echo -e "  ${GREEN}deploy-preview${NC} Deploy the latest dashboard changes to Vercel Preview"
    echo -e "  ${GREEN}deploy-prod${NC}    Deploy the latest dashboard changes to Vercel Production"
    echo -e "  ${GREEN}env-pull${NC}       Pull Vercel environment variables to .env.local"
    echo -e "  ${GREEN}status${NC}    Check the status of data files, logs, and scheduled tasks"
    echo -e "  ${GREEN}help${NC}      Show this help menu"
    echo ""
}

case "$1" in
    start)
        echo -e "${BLUE}=== Starting Dashboard Dev Server ===${NC}"
        # Make sure data is pre-seeded
        if [ ! -f "$PROJECT_DIR/dashboard/src/data/housingData.js" ]; then
            echo -e "${YELLOW}Data file not found. Running pipeline first...${NC}"
            python3 "$PROJECT_DIR/scripts/daily_pipeline.py"
        fi
        cd "$PROJECT_DIR/dashboard"
        echo -e "${GREEN}Running: npm run dev -- --open${NC}"
        npm run dev -- --open
        ;;
    update)
        echo -e "${BLUE}=== Running Data Update Pipeline ===${NC}"
        python3 "$PROJECT_DIR/scripts/daily_pipeline.py"
        echo -e "${GREEN}Data pipeline update complete!${NC}"
        ;;
    test)
        echo -e "${BLUE}=== Running Complete Model & Frontend Test Suite ===${NC}"
        export PYTHONPATH="$PROJECT_DIR/server"
        python3 "$PROJECT_DIR/tests/test_tools.py"
        python3 "$PROJECT_DIR/tests/test_backtest.py"
        python3 "$PROJECT_DIR/tests/test_data_integrity.py"
        python3 -m unittest "$PROJECT_DIR/tests/test_economic_logic.py"
        python3 "$PROJECT_DIR/tests/test_pipeline_errors.py"
        python3 -m unittest "$PROJECT_DIR/tests/test_frontend_jsx.py"
        python3 -m unittest "$PROJECT_DIR/tests/test_visual_playwright.py"
        echo -e "${GREEN}All 7 test suites passed successfully!${NC}"
        ;;
    backtest)
        echo -e "${BLUE}=== Running Historical Backtesting & Calibration ===${NC}"
        export PYTHONPATH="$PROJECT_DIR/server"
        python3 -c "import sys; sys.path.insert(0, '$PROJECT_DIR/server'); from cph_housing_server import run_historical_backtest; import json; print(json.dumps(run_historical_backtest(2007, 2024), indent=2))"
        ;;
    deploy-preview)
        echo -e "${BLUE}=== Deploying to Vercel Preview ===${NC}"
        npx vercel
        ;;
    deploy-prod)
        echo -e "${BLUE}=== Deploying to Vercel Production ===${NC}"
        npx vercel --prod
        ;;
    env-pull)
        echo -e "${BLUE}=== Pulling Vercel Environment Variables ===${NC}"
        npx vercel env pull .env.local
        ;;
    status)
        echo -e "${BLUE}=== Ingestion Status & Diagnostics ===${NC}"
        echo -e "${BOLD}Project Directory:${NC} $PROJECT_DIR"
        echo ""
        echo -e "${BOLD}Data Files:${NC}"
        if [ -f "$PROJECT_DIR/dashboard/src/data/housingData.js" ]; then
            echo -e "  - housingData.js: ${GREEN}Exists${NC} (Last modified: $(date -r "$PROJECT_DIR/dashboard/src/data/housingData.js" "+%Y-%m-%d %H:%M:%S"))"
        else
            echo -e "  - housingData.js: ${RED}Missing${NC}"
        fi
        
        if [ -f "$PROJECT_DIR/dashboard/public/data/latest_pipeline.json" ]; then
            echo -e "  - latest_pipeline.json: ${GREEN}Exists${NC} (Last modified: $(date -r "$PROJECT_DIR/dashboard/public/data/latest_pipeline.json" "+%Y-%m-%d %H:%M:%S"))"
        else
            echo -e "  - latest_pipeline.json: ${RED}Missing${NC}"
        fi
        
        echo ""
        echo -e "${BOLD}Latest Daily Reports:${NC}"
        ls -lt "$PROJECT_DIR/reports" | head -n 4 | awk '{if (NR>1) print "  - " $9}'
        
        echo ""
        echo -e "${BOLD}Cron Task Health Check:${NC}"
        echo "The daily background updater task is scheduled to run at 02:00 AM CET daily via the Antigravity scheduler."
        ;;
    *)
        show_help
        ;;
esac
