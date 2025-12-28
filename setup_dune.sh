#!/bin/bash
# Quick setup script for Dune API key

echo "Dune Analytics API Key Setup"
echo "=============================="
echo ""
echo "Please enter your Dune API key:"
read -s DUNE_KEY

if [ -z "$DUNE_KEY" ]; then
    echo "Error: No key provided"
    exit 1
fi

# Create or update .env file
if [ -f .env ]; then
    # Update existing .env
    if grep -q "DUNE_API_KEY" .env; then
        sed -i.bak "s/DUNE_API_KEY=.*/DUNE_API_KEY=$DUNE_KEY/" .env
        echo "✓ Updated existing .env file"
    else
        echo "DUNE_API_KEY=$DUNE_KEY" >> .env
        echo "✓ Added DUNE_API_KEY to .env file"
    fi
else
    # Create new .env
    echo "DUNE_API_KEY=$DUNE_KEY" > .env
    echo "✓ Created .env file with DUNE_API_KEY"
fi

echo ""
echo "Setup complete! You can now test with:"
echo "  python test_dune.py"

