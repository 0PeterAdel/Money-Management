#!/bin/bash

# Safe cleanup script - removes legacy duplicates
# Creates backup before deletion

set -e  # Exit on error

echo "================================================"
echo "Cleaning up legacy duplicate files"
echo "================================================"
echo ""

# Create timestamped backup directory
BACKUP_DIR="legacy_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📦 Creating backup: $BACKUP_DIR"
echo ""

# Files to backup and remove (duplicates migrated to microservices)
FILES_TO_REMOVE=(
    "config.py"
    "database.py"
    "security.py"
    "notifications.py"
    "bot"
)

echo "🗑️  Backing up and removing duplicate files:"
echo ""

for file in "${FILES_TO_REMOVE[@]}"; do
    if [ -e "$file" ]; then
        echo "  ✓ $file"
        cp -r "$file" "$BACKUP_DIR/"
        rm -rf "$file"
    else
        echo "  ⊘ $file (not found)"
    fi
done

echo ""
echo "================================================"
echo "✅ Cleanup complete!"
echo "================================================"
echo ""
echo "Removed files:"
echo "  • config.py          → services/*/app/core/config.py"
echo "  • database.py        → shared/database/"
echo "  • security.py        → services/auth_service/app/core/security.py"
echo "  • notifications.py   → services/notification_service/"
echo "  • bot/               → services/bot_service/app/"
echo ""
echo "Kept files (contain unmigrated features):"
echo "  • main.py            (expenses, wallet, voting endpoints)"
echo "  • models.py          (Expense, Debt, Payment models)"
echo "  • requirements.txt   (reference)"
echo ""
echo "Backup location: $BACKUP_DIR/"
echo ""
echo "Next steps:"
echo "  1. Test services: ./test_services.sh"
echo "  2. Check structure: tree -L 2"
echo ""
