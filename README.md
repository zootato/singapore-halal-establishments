# Singapore Halal Establishments

Automated daily-updated database of halal-certified establishments in Singapore from MUIS (Majlis Ugama Islam Singapura).

## 📊 Data Access

- **CSV**: [halal_establishments.csv](halal_establishments.csv) - Direct download
- **JSON**: [halal_establishments.json](halal_establishments.json) - For developers
- **Web Interface**: [View interactive table](https://zootato.github.io/singapore-halal-establishments/)

## 📈 Statistics

- **Total Establishments**: 3796
- **Last Updated**: 2026-01-13
- **Data Source**: [MUIS Halal Directory](https://halal.muis.gov.sg/halal/establishments)

## 🔄 Automated Updates

This repository updates daily at 6 AM Singapore Time using GitHub Actions:

1. **Comprehensive Search**: Uses 70+ search terms to capture all establishments
2. **Deduplication**: Ensures unique establishments only
3. **Multi-format Export**: CSV, JSON, and web interface
4. **Statistics Tracking**: Metadata about types and schemes

## 📋 Data Schema

```json
{
  "name": "Restaurant Name",
  "address": "Full address with postal code",
  "type": "Restaurant/Hawker/Bakery/etc",
  "number": "MUIS certification number",
  "scheme": "Certification scheme type",
  "postal": "Postal code"
}
```

## 🛠 API Usage

### Direct CSV Access
```
https://raw.githubusercontent.com/zootato/singapore-halal-establishments/main/halal_establishments.csv
```

### JSON Endpoint
```
https://raw.githubusercontent.com/zootato/singapore-halal-establishments/main/halal_establishments.json
```

### Python Example
```python
import pandas as pd

# Load data directly from GitHub
url = "https://raw.githubusercontent.com/zootato/singapore-halal-establishments/main/halal_establishments.csv"
df = pd.read_csv(url)

# Filter by establishment type
restaurants = df[df['type'] == 'Restaurant']
hawkers = df[df['type'] == 'Hawker']

# Search by location
jurong_food = df[df['address'].str.contains('Jurong', case=False)]
```

### JavaScript Example
```javascript
// Fetch all establishments
const response = await fetch('https://raw.githubusercontent.com/zootato/singapore-halal-establishments/main/halal_establishments.json');
const establishments = await response.json();

// Filter by type
const bakeries = establishments.filter(est => est.type === 'Bakery');

// Search by name
const searchTerm = 'chicken';
const results = establishments.filter(est =>
  est.name.toLowerCase().includes(searchTerm)
);
```

## 📊 Web Interface Features

The included web interface provides:

- **Live Search**: Filter by name or address
- **Category Filters**: Filter by establishment type and certification scheme
- **Responsive Design**: Works on desktop and mobile
- **Pagination**: Easy browsing of large dataset
- **Download Options**: Direct CSV/JSON downloads
- **Statistics Dashboard**: Live counts and updates

## 🚀 Setup Instructions

1. **Fork this repository**
2. **Enable GitHub Pages** in repository settings
3. **Update README** with your GitHub username in URLs
4. **Run initial scrape** (optional - will run automatically)

The GitHub Action will handle daily updates automatically.

## 🤝 Contributing

- **Issues**: Report problems or suggestions via [GitHub Issues](../../issues)
- **Manual Updates**: Trigger workflow manually if needed
- **Improvements**: Submit pull requests for enhancements

## ⚡ Performance

- **Daily Updates**: 6 AM SGT via GitHub Actions
- **Comprehensive Coverage**: 70+ search terms ensure complete data
- **Fast Loading**: Optimized JSON/CSV formats
- **CDN Delivery**: Fast global access via GitHub Pages

## ⚖️ Legal

- **Data Source**: MUIS public halal directory
- **Purpose**: Educational and research use
- **Updates**: Automated, respectful of source servers
- **Contact MUIS**: For certification questions, contact [MUIS directly](https://www.muis.gov.sg/)

---

*🤖 Automated by GitHub Actions • Updated daily at 6 AM SGT*