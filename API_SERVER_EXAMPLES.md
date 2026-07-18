# StayX Capture API - Server-Side Implementation Guide

Your Capture.py app is now ready to send data to your website! Here's how to implement the server-side code.

---

## 📡 API Endpoint Requirements

Your website needs **ONE endpoint** that accepts POST requests:
- **URL Example:** `https://yourwebsite.com/api/upload`
- **Method:** `POST`
- **Content-Type:** `application/json`
- **Headers:** Optional `Authorization: Bearer YOUR_API_KEY`

---

## 📦 Request Format

The app sends JSON with two different types:

### **Type 1: Screenshot Upload**
```json
{
  "type": "screenshot",
  "filename": "screenshot_20260305_143025_123.png",
  "image": "iVBORw0KGgoAAAANSUhEUgAA...", // base64 encoded PNG
  "timestamp": "2026-03-05T14:30:25.123456",
  "api_key": "your-api-key" // if configured
}
```

### **Type 2: Clipboard Text**
```json
{
  "type": "clipboard",
  "text": "The copied text content goes here",
  "timestamp": "2026-03-05T14:30:25.123456",
  "api_key": "your-api-key" // if configured
}
```

---

## 🔧 Implementation Examples

### **Option 1: PHP (Most Common)**

Create file: `api/upload.php`

```php
<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *'); // Remove in production
header('Access-Control-Allow-Methods: POST');

// Database connection
$db = new mysqli('localhost', 'username', 'password', 'database');

if ($db->connect_error) {
    http_response_code(500);
    echo json_encode(['success' => false, 'error' => 'Database connection failed']);
    exit;
}

// Get POST data
$json = file_get_contents('php://input');
$data = json_decode($json, true);

if (!$data) {
    http_response_code(400);
    echo json_encode(['success' => false, 'error' => 'Invalid JSON']);
    exit;
}

// Optional: Verify API key
$api_key = isset($data['api_key']) ? $data['api_key'] : '';
if ($api_key !== 'YOUR_SECRET_API_KEY') {
    // Uncomment to enforce API key:
    // http_response_code(401);
    // echo json_encode(['success' => false, 'error' => 'Invalid API key']);
    // exit;
}

$type = $data['type'] ?? '';
$timestamp = $data['timestamp'] ?? date('Y-m-d H:i:s');

if ($type === 'screenshot') {
    // Handle screenshot upload
    $filename = $data['filename'] ?? 'screenshot.png';
    $image_base64 = $data['image'] ?? '';
    
    // Decode base64 image
    $image_data = base64_decode($image_base64);
    
    // Save image to disk
    $upload_dir = 'uploads/screenshots/';
    if (!is_dir($upload_dir)) {
        mkdir($upload_dir, 0777, true);
    }
    
    $filepath = $upload_dir . $filename;
    file_put_contents($filepath, $image_data);
    
    // Save to database
    $stmt = $db->prepare("INSERT INTO screenshots (filename, filepath, timestamp) VALUES (?, ?, ?)");
    $stmt->bind_param("sss", $filename, $filepath, $timestamp);
    $stmt->execute();
    
    echo json_encode([
        'success' => true,
        'id' => $db->insert_id,
        'url' => 'https://yourwebsite.com/' . $filepath
    ]);
    
} elseif ($type === 'clipboard') {
    // Handle clipboard text
    $text = $data['text'] ?? '';
    
    // Save to database
    $stmt = $db->prepare("INSERT INTO clipboard_history (text, timestamp) VALUES (?, ?)");
    $stmt->bind_param("ss", $text, $timestamp);
    $stmt->execute();
    
    echo json_encode([
        'success' => true,
        'id' => $db->insert_id
    ]);
    
} else {
    http_response_code(400);
    echo json_encode(['success' => false, 'error' => 'Invalid type']);
}

$db->close();
?>
```

**Database Tables (MySQL):**
```sql
CREATE TABLE screenshots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    filepath VARCHAR(500) NOT NULL,
    timestamp DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE clipboard_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    text TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### **Option 2: Node.js + Express**

Create file: `server.js`

```javascript
const express = require('express');
const mysql = require('mysql2/promise');
const fs = require('fs').promises;
const path = require('path');

const app = express();
app.use(express.json({ limit: '50mb' })); // Handle large images

// Database connection
const pool = mysql.createPool({
    host: 'localhost',
    user: 'username',
    password: 'password',
    database: 'database'
});

// API endpoint
app.post('/api/upload', async (req, res) => {
    try {
        const { type, api_key, timestamp } = req.body;
        
        // Optional: Verify API key
        if (api_key !== 'YOUR_SECRET_API_KEY') {
            // Uncomment to enforce:
            // return res.status(401).json({ success: false, error: 'Invalid API key' });
        }
        
        if (type === 'screenshot') {
            const { filename, image } = req.body;
            
            // Decode base64 image
            const imageBuffer = Buffer.from(image, 'base64');
            
            // Save to disk
            const uploadDir = 'uploads/screenshots';
            await fs.mkdir(uploadDir, { recursive: true });
            const filepath = path.join(uploadDir, filename);
            await fs.writeFile(filepath, imageBuffer);
            
            // Save to database
            const [result] = await pool.execute(
                'INSERT INTO screenshots (filename, filepath, timestamp) VALUES (?, ?, ?)',
                [filename, filepath, timestamp]
            );
            
            res.json({
                success: true,
                id: result.insertId,
                url: `https://yourwebsite.com/${filepath}`
            });
            
        } else if (type === 'clipboard') {
            const { text } = req.body;
            
            // Save to database
            const [result] = await pool.execute(
                'INSERT INTO clipboard_history (text, timestamp) VALUES (?, ?)',
                [text, timestamp]
            );
            
            res.json({
                success: true,
                id: result.insertId
            });
            
        } else {
            res.status(400).json({ success: false, error: 'Invalid type' });
        }
        
    } catch (error) {
        console.error('API Error:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

app.listen(3000, () => {
    console.log('API server running on port 3000');
});
```

**Install dependencies:**
```bash
npm install express mysql2
```

---

### **Option 3: Python Flask**

Create file: `app.py`

```python
from flask import Flask, request, jsonify
import base64
import mysql.connector
from datetime import datetime
import os

app = Flask(__name__)

# Database connection
db_config = {
    'host': 'localhost',
    'user': 'username',
    'password': 'password',
    'database': 'database'
}

@app.route('/api/upload', methods=['POST'])
def upload():
    try:
        data = request.get_json()
        
        # Optional: Verify API key
        api_key = data.get('api_key', '')
        if api_key != 'YOUR_SECRET_API_KEY':
            # Uncomment to enforce:
            # return jsonify({'success': False, 'error': 'Invalid API key'}), 401
            pass
        
        data_type = data.get('type')
        timestamp = data.get('timestamp', datetime.now().isoformat())
        
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        if data_type == 'screenshot':
            filename = data.get('filename', 'screenshot.png')
            image_base64 = data.get('image', '')
            
            # Decode base64 image
            image_data = base64.b64decode(image_base64)
            
            # Save to disk
            upload_dir = 'uploads/screenshots'
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            # Save to database
            cursor.execute(
                "INSERT INTO screenshots (filename, filepath, timestamp) VALUES (%s, %s, %s)",
                (filename, filepath, timestamp)
            )
            conn.commit()
            
            return jsonify({
                'success': True,
                'id': cursor.lastrowid,
                'url': f'https://yourwebsite.com/{filepath}'
            })
            
        elif data_type == 'clipboard':
            text = data.get('text', '')
            
            # Save to database
            cursor.execute(
                "INSERT INTO clipboard_history (text, timestamp) VALUES (%s, %s)",
                (text, timestamp)
            )
            conn.commit()
            
            return jsonify({
                'success': True,
                'id': cursor.lastrowid
            })
            
        else:
            return jsonify({'success': False, 'error': 'Invalid type'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    app.run(port=5000, debug=True)
```

**Install dependencies:**
```bash
pip install flask mysql-connector-python
```

---

## ⚙️ Configuration in Capture.py

Once your server is ready:

1. **Open your screenshot app**
2. **Click Settings tab**
3. **Scroll to "API INTEGRATION" section**
4. **Configure:**
   - Enable API Upload: ✅ ON
   - API Endpoint: `https://yourwebsite.com/api/upload`
   - API Key: (optional) `your-secret-key`
   - Upload Screenshots: ✅ ON
   - Upload Clipboard Text: ✅ ON

---

## 🧪 Testing

### Test with curl:
```bash
# Test screenshot upload
curl -X POST https://yourwebsite.com/api/upload \
  -H "Content-Type: application/json" \
  -d '{
    "type": "screenshot",
    "filename": "test.png",
    "image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
    "timestamp": "2026-03-05T14:30:25",
    "api_key": "your-key"
  }'

# Test clipboard upload
curl -X POST https://yourwebsite.com/api/upload \
  -H "Content-Type: application/json" \
  -d '{
    "type": "clipboard",
    "text": "Hello World",
    "timestamp": "2026-03-05T14:30:25",
    "api_key": "your-key"
  }'
```

---

## 🔒 Security Best Practices

1. **Use HTTPS** (not HTTP) in production
2. **Validate API keys** properly
3. **Sanitize filenames** to prevent path traversal
4. **Limit file sizes** (10MB max recommended)
5. **Rate limiting** to prevent abuse
6. **Use prepared statements** for SQL (already done in examples)
7. **Store API keys** in environment variables, not in code

---

## 📊 View Your Data

Add these pages to your website:

### Screenshots Gallery:
```php
// gallery.php
$db = new mysqli('localhost', 'user', 'pass', 'database');
$result = $db->query("SELECT * FROM screenshots ORDER BY created_at DESC LIMIT 50");

while ($row = $result->fetch_assoc()) {
    echo "<img src='{$row['filepath']}' alt='{$row['filename']}'>";
}
```

### Clipboard History:
```php
// clipboard.php
$db = new mysqli('localhost', 'user', 'pass', 'database');
$result = $db->query("SELECT * FROM clipboard_history ORDER BY created_at DESC LIMIT 100");

while ($row = $result->fetch_assoc()) {
    echo "<div>{$row['text']} - {$row['timestamp']}</div>";
}
```

---

## ✅ Done!

Your screenshot app will now automatically upload to your website! 🎉
