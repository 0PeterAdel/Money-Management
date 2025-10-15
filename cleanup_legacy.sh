#!/bin/bash

# Cleanup Legacy Files Script
# This script moves old monolithic files to a backup directory

echo "======================================"
echo "Cleaning up legacy monolithic files"
echo "======================================"
echo ""

# Create backup directory
BACKUP_DIR="legacy_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Creating backup directory: $BACKUP_DIR"
echo ""

# Files to archive
FILES_TO_ARCHIVE=(
    "config.py"
    "database.py"
    "security.py"
    "notifications.py"
    "bot"
)

# Files to keep (still contain unmigrated features)
FILES_TO_KEEP=(
    "main.py"
    "models.py"
    "requirements.txt"
)

echo "Moving legacy files to backup..."
for file in "${FILES_TO_ARCHIVE[@]}"; do
    if [ -e "$file" ]; then
        echo "  ✓ Moving $file"
        mv "$file" "$BACKUP_DIR/"
    else
        echo "  ⊘ $file not found (already removed?)"
    fi
done

echo ""
echo "Keeping these files (contain unmigrated features):"
for file in "${FILES_TO_KEEP[@]}"; do
    if [ -e "$file" ]; then
        echo "  → $file (KEEP - contains unmigrated endpoints)"
    fi
done

echo ""
echo "======================================"
echo "Cleanup complete!"
echo "======================================"
echo ""
echo "Legacy files backed up to: $BACKUP_DIR/"
echo ""
echo "Next steps:"
echo "1. Verify microservices are working: ./test_services.sh"
echo "2. Migrate remaining endpoints from main.py"
echo "3. Once everything is migrated, you can delete: $BACKUP_DIR/"
echo ""
