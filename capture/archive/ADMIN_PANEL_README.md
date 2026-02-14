# Admin Panel Documentation

## Overview
The admin panel allows you to review and manage all vocabulary uploads from users via photo/camera.

## Access
Navigate to: `http://localhost:5000/admin` (or your server URL + `/admin`)

## Features

### 1. **Log List (Left Sidebar)**
- Shows all photo upload attempts
- Filter by status: All / Pending / Validated / Rejected
- Quick view of:
  - Filename
  - Status badge
  - Upload date/time
  - User IP address
  - Number of entries created/updated

### 2. **Detail Panel (Right Side)**
When you click on a log entry, you'll see:

#### Basic Information
- User IP address
- Section assigned
- Detected language (Chinese/French)
- Number of entries created/updated

#### Uploaded Image
- Thumbnail preview
- Click to view in full-screen modal
- Link to open in new tab

#### OCR Detected Text
- Raw text extracted from the image by Google Vision API

#### Vocabulary Entries
For each vocabulary word/phrase created:
- **Chinese (汉字)**: The Chinese characters
- **Pinyin**: Romanization with tone marks
- **English**: English translation
- **French**: French translation
- **Example Sentences**: In all four formats (Chinese, Pinyin, English, French)

### 3. **Action Buttons**

#### ✓ Validate
- Marks the entry as validated
- Indicates the upload was correct and approved
- Status changes to "validated" (green badge)

#### ✗ Reject
- Marks the entry as rejected
- Indicates the upload had issues or was spam
- Status changes to "rejected" (red badge)
- **Note**: Vocabulary entries remain in database

#### 🗑 Delete
- **WARNING**: Permanently deletes:
  - The log entry
  - ALL associated vocabulary entries from the database
- Use with caution!
- Requires confirmation

## Status Indicators

| Status | Color | Meaning |
|--------|-------|---------|
| **Pending** | Yellow | Awaiting admin review |
| **Validated** | Green | Approved by admin |
| **Rejected** | Red | Rejected by admin |

## Database Schema

### PhotoLog Table
```python
- id: Integer (primary key)
- timestamp: DateTime (UTC)
- user_ip: String (IP address)
- filename: String (original filename)
- image_path: String (server path to saved image)
- section: String (vocabulary section)
- ocr_text: Text (raw OCR output)
- detected_language: String (chinese/french)
- entries_json: Text (JSON array of processed entries)
- status: String (pending/validated/rejected)
- created_count: Integer
- updated_count: Integer
- vocab_ids: Text (comma-separated vocabulary IDs)
- error_message: Text (if processing failed)
```

## API Endpoints

### Admin Page
- `GET /admin` - Render admin dashboard

### Log Management
- `GET /admin/logs` - Get all logs (JSON)
- `GET /admin/log/<id>` - Get detailed log info (JSON)
- `POST /admin/log/<id>/validate` - Validate a log entry
- `POST /admin/log/<id>/reject` - Reject a log entry
- `DELETE /admin/log/<id>/delete` - Delete log and vocabularies
- `GET /admin/image/<id>` - Serve uploaded image

## Tips

1. **Review regularly**: Check pending entries daily to ensure quality
2. **Validate good entries**: Helps track which sources produce quality data
3. **Reject spam**: Mark low-quality uploads to identify problem users
4. **Delete carefully**: Only delete entries that are completely wrong
5. **Use filters**: Focus on pending entries first, then review others

## Troubleshooting

### Image not loading
- Check if the file exists in the `uploads/` folder
- Verify file permissions
- Check browser console for errors

### No logs appearing
- Ensure users have uploaded photos
- Check browser console for API errors
- Verify database connection

### Can't delete entries
- Confirm you have database write permissions
- Check server logs for errors
