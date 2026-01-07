# Testing Guide - Error Handling

## Quick Start

The app is now running at: **http://localhost:8501**

## Test Scenarios

### Scenario 1: No API Key (Default State)
1. Open the app
2. Navigate to "Advanced Options" in sidebar
3. You should see: "Status: No key provided — using default settings."
4. Upload a resume or enter information manually
5. **Expected:** App works with stub LLM responses

### Scenario 2: Invalid API Key
1. In Advanced Options, paste: `invalid_key_12345`
2. Click "Verify Key"
3. **Expected:** Error message "Verification failed: Authentication failed"
4. App continues to work with defaults

### Scenario 3: Valid API Key
1. Get a key from https://console.groq.com/keys
2. Paste valid key in Advanced Options (starts with `gsk_`)
3. Click "Verify Key"
4. **Expected:** Success message and green validation badge
5. Resume parsing uses real LLM

### Scenario 4: Resume Upload with API Key
1. Have valid API key set (Scenario 3)
2. Upload any resume (PDF or DOCX)
3. **Expected:** Fields auto-filled with:
   - Full Name
   - Email
   - Phone
   - Years of Experience
   - Desired Position
   - Location
   - Tech Stack

### Scenario 5: Resume Upload without API Key
1. No API key set (Scenario 1)
2. Upload a resume
3. **Expected:** Info message asking for API key
4. User can still manually enter information

### Scenario 6: Corrupted/Empty File
1. Upload empty PDF or DOCX
2. **Expected:** Error "Resume file is empty or contains no extractable text"
3. Option to manually enter information

### Scenario 7: Answer Evaluation
1. Complete information entry
2. Start assessment
3. Answer a question
4. **Expected:** 
   - Technical Score displayed
   - Sentiment Analysis shown
   - Feedback provided even if API fails
   - Graceful fallback if LLM unavailable

### Scenario 8: Error Recovery
1. Intentionally break something (e.g., close network)
2. Try to continue
3. **Expected:** 
   - Error message with recovery steps
   - Option to reset from sidebar
   - Helpful suggestions provided

## Error Messages Reference

| Scenario | Expected Message | Action |
|----------|-----------------|--------|
| No API key | "Status: No key provided" | Manual entry works |
| Invalid key | "API key looks malformed" | Verify or clear it |
| Valid key | "✅ Valid" + success message | Auto-fill enabled |
| Empty resume | "Resume file is empty" | Upload valid file |
| API timeout | Shows in detailed feedback | Click "View Detailed Feedback" |
| LLM failure | "Using fallback evaluation" | Continue assessment |
| Parsing error | "Resume parsing unavailable" | Manual entry option |

## Features to Verify

- ✅ Resume auto-fill works with valid API key
- ✅ App works without API key (with defaults)
- ✅ Invalid keys are caught early
- ✅ Assessment continues even if components fail
- ✅ Error messages are user-friendly
- ✅ Recovery options are provided
- ✅ No crashes or unhandled exceptions
- ✅ Session state preserved on errors

## Debugging Tips

1. **Check server logs:**
   ```bash
   # Terminal where server is running shows error messages
   ```

2. **Browser console errors:**
   - F12 → Console tab
   - Look for JavaScript errors

3. **Streamlit debug mode:**
   - Errors appear in app with traceback
   - Helpful for development

4. **API key validation:**
   - Use "Verify Key" button
   - Check Advanced Options for status
   - Look for warnings if malformed

## Success Criteria

The error handling is working correctly if:

1. ✅ App never crashes with unhandled exceptions
2. ✅ Users see helpful error messages (not technical jargon)
3. ✅ Recovery options are always provided
4. ✅ App continues working even with API failures
5. ✅ Graceful fallbacks maintain functionality
6. ✅ No data loss on errors
7. ✅ Session state is preserved
8. ✅ Resume parsing works with valid API key
9. ✅ Assessment completes without API key (with defaults)
10. ✅ All error messages are in English and user-friendly

## Common Test Cases

### For Developers
- Test with no environment variables set
- Test with invalid/expired API keys
- Test with network disconnection
- Test with corrupted input files
- Test with malformed JSON responses

### For Users
- Follow Scenarios 1-8 above
- Provide feedback on error message clarity
- Report any unexpected crashes
- Suggest improvements to recovery process

## Getting Help

If you encounter issues:
1. Check [ERROR_HANDLING.md](ERROR_HANDLING.md) for technical details
2. Review the error message in the app
3. Try the suggested recovery steps
4. Check Advanced Options → API key validation
5. Use the Reset Assessment button in sidebar
6. Clear browser cache if issues persist

---

**Last Updated:** January 7, 2026
**Status:** All error handling implemented and tested
