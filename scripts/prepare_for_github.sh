#!/bin/bash

# Prepare project for GitHub deployment
# This script cleans up and validates everything before pushing to GitHub

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     GitHub Deployment Preparation Script                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
        exit 1
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Step 1: Clean up data directories
echo "Step 1: Cleaning up generated data..."
if [ -d "data" ]; then
    rm -rf data/*
    mkdir -p data/{kafka,zookeeper,spark-checkpoints,spark-warehouse,prometheus,grafana,zookeeper-logs}
    print_status $? "Data directories cleaned"
else
    print_warning "Data directory doesn't exist, creating it..."
    mkdir -p data
fi
echo ""

# Step 2: Check for sensitive files
echo "Step 2: Checking for sensitive files..."
sensitive_files=(
    ".env"
    "*.key"
    "*.pem"
    "*.p12"
    "*secret*"
    "*password*"
)

found_sensitive=false
for pattern in "${sensitive_files[@]}"; do
    if ls $pattern 2>/dev/null; then
        print_warning "Found potentially sensitive file: $pattern"
        found_sensitive=true
    fi
done

if [ "$found_sensitive" = false ]; then
    print_status 0 "No sensitive files found"
fi
echo ""

# Step 3: Verify .gitignore exists
echo "Step 3: Verifying .gitignore..."
if [ -f ".gitignore" ]; then
    print_status 0 ".gitignore exists"
else
    print_status 1 ".gitignore missing!"
fi
echo ""

# Step 4: Check for placeholder text
echo "Step 4: Checking for placeholders to update..."
placeholders=$(grep -r "YOUR_USERNAME" . --exclude-dir=.git --exclude-dir=data --exclude="*.sh" 2>/dev/null || true)
if [ -n "$placeholders" ]; then
    print_warning "Found YOUR_USERNAME placeholders - please update with your GitHub username:"
    echo "$placeholders"
else
    print_status 0 "No placeholders found"
fi
echo ""

# Step 5: Verify required files exist
echo "Step 5: Checking required files..."
required_files=(
    "README.md"
    "LICENSE"
    "requirements.txt"
    "docker-compose.yml"
    ".gitignore"
    "CONTRIBUTING.md"
    "LEARNING_GUIDE.md"
    "VERIFICATION_REPORT.md"
)

all_files_exist=true
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✓${NC} $file"
    else
        echo -e "  ${RED}✗${NC} $file (missing)"
        all_files_exist=false
    fi
done

if [ "$all_files_exist" = true ]; then
    print_status 0 "All required files present"
else
    print_status 1 "Some required files missing"
fi
echo ""

# Step 6: Run tests
echo "Step 6: Running tests..."
if command -v pytest &> /dev/null; then
    if pytest tests/ -v --tb=short; then
        print_status 0 "All tests passed"
    else
        print_warning "Some tests failed - consider fixing before deployment"
    fi
else
    print_warning "pytest not installed - skipping tests"
fi
echo ""

# Step 7: Check Docker setup
echo "Step 7: Validating Docker setup..."
if docker-compose config > /dev/null 2>&1; then
    print_status 0 "docker-compose.yml is valid"
else
    print_status 1 "docker-compose.yml has errors"
fi
echo ""

# Step 8: Check for large files
echo "Step 8: Checking for large files..."
large_files=$(find . -type f -size +10M ! -path "./.git/*" ! -path "./data/*" 2>/dev/null || true)
if [ -n "$large_files" ]; then
    print_warning "Found large files (>10MB) - consider adding to .gitignore:"
    echo "$large_files"
else
    print_status 0 "No large files found"
fi
echo ""

# Step 9: Git status
echo "Step 9: Git repository status..."
if [ -d ".git" ]; then
    echo "Current branch: $(git branch --show-current)"
    echo "Uncommitted changes:"
    git status --short
else
    print_warning "Not a git repository - run 'git init' first"
fi
echo ""

# Summary
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    PREPARATION SUMMARY                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Your project is ready for GitHub deployment! 🎉"
echo ""
echo "Next steps:"
echo "  1. Update YOUR_USERNAME placeholders with your GitHub username"
echo "  2. Update contact information in README.md"
echo "  3. Review GITHUB_DEPLOYMENT_GUIDE.md for complete checklist"
echo "  4. Run: git add . && git commit -m 'Initial commit'"
echo "  5. Create GitHub repository"
echo "  6. Run: git remote add origin <your-repo-url>"
echo "  7. Run: git push -u origin main"
echo ""
echo "For detailed instructions, see: GITHUB_DEPLOYMENT_GUIDE.md"
echo ""


