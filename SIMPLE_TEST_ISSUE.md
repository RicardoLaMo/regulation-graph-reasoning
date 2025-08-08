# Simple Test Issue for Claude

Use this to test if Claude is responding:

---

## Title: Test Claude Response

## Body:

@claude Please create a simple hello world Python script in src/hello.py that prints "Hello from Claude!"

---

This simple request should help determine if:
1. Claude is responding at all
2. The action has proper permissions
3. The connection is working

If this works, then the issue with #5 might be:
- The request is too complex
- Claude is hitting token limits
- The specs references might be causing issues