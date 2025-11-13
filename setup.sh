#!/bin/bash
# Plutus Data Warehouse - Setup Script

echo "========================================="
echo "Plutus Data Warehouse - Setup"
echo "========================================="

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if Google Service Account JSON exists
if [ -f "credentials/google_service_account.json" ]; then
    echo "✅ Google Service Account JSON found"
else
    echo "⚠️  Google Service Account JSON not found"
    echo "   Please place your JSON file at: credentials/google_service_account.json"
fi

# Check if .env exists
if [ -f ".env" ]; then
    echo "✅ .env file found"
else
    echo "⚠️  .env file not found (this should have been created already)"
fi

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Ensure Google Service Account JSON is at:"
echo "   credentials/google_service_account.json"
echo ""
echo "3. Share your Google Sheets with the service account email"
echo ""
echo "4. Test with dry-run:"
echo "   python cli.py tofu-ingestion --dry-run --verbose"
echo ""
echo "5. Run for real:"
echo "   python cli.py tofu-ingestion"
echo ""
