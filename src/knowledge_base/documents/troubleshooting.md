# CloudSync Troubleshooting Guide

## Login Issues

### Cannot Login to Account

#### Error: "Invalid credentials"
**Solution:**
1. Verify email address is correct
2. Check CAPS LOCK is off
3. Try password reset
4. Clear browser cache and cookies
5. Try different browser or device

#### Error: "Account locked"
**Solution:**
1. Too many failed login attempts
2. Wait 30 minutes and try again
3. Or use "Forgot Password" to reset
4. Contact support if repeatedly locked

#### Two-Factor Authentication Issues
**Solution:**
1. Ensure correct time on device
2. Use backup codes if available
3. Try authenticator app instead of SMS
4. Contact support to disable 2FA if needed

## Sync Problems

### Files Not Syncing

#### Check Basic Requirements
1. **Internet Connection**
   - Test connection with other websites
   - Check firewall settings
   - Verify proxy configuration

2. **CloudSync Status**
   - Look for system tray icon
   - Green = working
   - Yellow = syncing
   - Red = error

3. **Storage Space**
   - Check local disk space
   - Verify cloud storage quota
   - Free up space if needed

#### Advanced Troubleshooting
```
1. Restart CloudSync:
   - Windows: System tray > Quit > Restart
   - Mac: Menu bar > Quit > Restart
   - Linux: killall cloudsync && cloudsync

2. Check sync status:
   - Right-click CloudSync icon
   - Select "View Sync Status"
   - Look for specific error messages

3. Reset sync database:
   - Settings > Advanced > Reset Sync
   - Warning: This will resync all files
```

### Selective Sync Issues

#### Files Missing After Enabling Selective Sync
**Solution:**
1. Files are not deleted, just not synced locally
2. Access via web interface
3. Re-enable folders in Selective Sync settings
4. Files will download again

### Sync Conflicts

#### Understanding Conflicts
Conflicts occur when:
- Same file edited on multiple devices
- Offline edits that conflict
- Network issues during sync

#### Resolving Conflicts
1. CloudSync creates "conflicted copy"
2. Original: `document.doc`
3. Conflict: `document (John's conflicted copy 2024-01-15).doc`
4. Review both versions
5. Keep the desired version
6. Delete the other

## Performance Issues

### Slow Upload/Download Speeds

#### Check Bandwidth Settings
1. Settings > Bandwidth
2. Ensure not limited too low
3. Disable "Limit automatically"
4. Test with single large file

#### Optimize Performance
- Pause other cloud services
- Close bandwidth-heavy applications
- Sync during off-peak hours
- Use ethernet instead of WiFi
- Disable antivirus scanning of CloudSync folder

### High CPU Usage

#### Common Causes
1. Initial sync of large folders
2. Many small files syncing
3. Antivirus scanning
4. Corrupted database

#### Solutions
1. Let initial sync complete
2. Pause sync temporarily
3. Add CloudSync to antivirus exceptions
4. Reset sync database if corrupted

### High Memory Usage

#### Normal vs Excessive
- Normal: 200-500MB
- High: 500MB-1GB (large sync)
- Excessive: Over 1GB

#### Reduce Memory Usage
1. Reduce number of synced folders
2. Use Selective Sync
3. Restart CloudSync periodically
4. Update to latest version

## File & Folder Issues

### Cannot Upload Specific Files

#### Check File Restrictions
1. **File size limits by plan**
2. **Filename restrictions:**
   - No: `\ / : * ? " < > |`
   - Max 255 characters
   - No trailing spaces or periods

#### System Files
- Some system files blocked
- Temporary files ignored
- Database files may fail
- Use zip for problematic files

### Missing Files

#### Files Disappeared
1. Check Trash/Recycle Bin
2. View online at cloudsync.com
3. Check file history/versions
4. Verify Selective Sync settings
5. Search by filename

#### Recovery Options
- Restore from trash (30-90 days)
- Restore previous version
- Contact support for longer recovery

## Mobile App Issues

### App Won't Start

#### iOS Issues
1. Update to latest iOS
2. Update CloudSync app
3. Restart iPhone/iPad
4. Reinstall app
5. Check storage space

#### Android Issues
1. Clear app cache
2. Clear app data (will need to login again)
3. Check permissions
4. Disable battery optimization
5. Reinstall app

### Camera Upload Not Working

#### Enable Camera Upload
1. App Settings > Camera Upload
2. Enable "Upload Photos"
3. Choose WiFi only or always
4. Grant photo permissions

#### Troubleshooting
- Check available storage
- Verify permissions granted
- Ensure app not restricted by battery saver
- Try manual upload first
- Check upload queue in app

## Account & Billing Issues

### Payment Failed

#### Common Reasons
1. Expired credit card
2. Insufficient funds
3. Card declined by bank
4. Billing address mismatch

#### Resolution
1. Update payment method
2. Contact bank about declined payment
3. Try alternative payment method
4. Contact support for invoice option

### Cannot Upgrade/Downgrade Plan

#### Troubleshooting Steps
1. Ensure account owner (not team member)
2. Clear browser cache
3. Try different browser
4. Disable ad blockers
5. Contact support with error message

## Error Messages

### Common Error Codes

#### Error 400: Bad Request
- Corrupted request
- Clear cache and retry

#### Error 401: Unauthorized
- Session expired
- Log in again

#### Error 403: Forbidden
- No permission for action
- Check account status

#### Error 404: Not Found
- File deleted or moved
- Refresh file list

#### Error 429: Too Many Requests
- Rate limited
- Wait and retry

#### Error 500: Server Error
- CloudSync server issue
- Check status page
- Try again later

#### Error 507: Insufficient Storage
- Quota exceeded
- Delete files or upgrade plan

## Getting Further Help

### Before Contacting Support
1. Check this troubleshooting guide
2. Visit status.cloudsync.com
3. Search help.cloudsync.com
4. Try basic steps (restart, update)

### Contacting Support
**Provide:**
- Account email
- Error messages (screenshots)
- Steps to reproduce
- Operating system and version
- CloudSync version
- When issue started

### Support Channels
- Email: support@cloudsync.com
- Chat: Available for paid plans
- Phone: Enterprise plans only
- Response times vary by plan
