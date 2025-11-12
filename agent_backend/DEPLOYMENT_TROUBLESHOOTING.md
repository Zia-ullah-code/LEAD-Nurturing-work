# Deployment Troubleshooting Guide

## Current Issue: onnxruntime Compatibility

### Error Message
```
ERROR: Could not find a version that satisfies the requirement onnxruntime==1.19.2
```

### Root Cause
- `onnxruntime==1.19.2` is not available for Python 3.11.0
- Available versions for Python 3.11: 1.20.0, 1.20.1, 1.21.0, 1.21.1, 1.22.0, 1.22.1, 1.23.0, 1.23.1, 1.23.2

### Solution Applied
1. ✅ Removed `onnxruntime` from `requirements.txt` (it's not directly used)
2. ✅ Updated Python version to `3.11.7` for better compatibility
3. ✅ Updated build script with better error handling
4. ✅ Let `sentence-transformers` manage its own dependencies

## If Build Still Fails

### Option 1: Force Install Compatible onnxruntime (if needed)

If `sentence-transformers` requires `onnxruntime`, add this to `build.sh`:

```bash
# After installing sentence-transformers
pip install "onnxruntime>=1.20.0,<1.25.0" || echo "Warning: onnxruntime optional, continuing..."
```

### Option 2: Use Python 3.10 Instead

Python 3.10 has better package compatibility:

1. Update `runtime.txt`:
   ```
   python-3.10.12
   ```

2. Update `render.yaml`:
   ```yaml
   - key: PYTHON_VERSION
     value: 3.10.12
   ```

3. Update `requirements.txt` to be compatible with Python 3.10

### Option 3: Pin Compatible Versions

If dependency conflicts persist, pin compatible versions:

```txt
sentence-transformers==5.1.2
torch>=2.0.0,<2.5.0
transformers>=4.30.0,<4.40.0
```

### Option 4: Use CPU-Only PyTorch (Smaller, Faster)

Add to `requirements.txt`:
```txt
--extra-index-url https://download.pytorch.org/whl/cpu
torch>=2.0.0,<3.0.0
```

### Option 5: Install Dependencies in Stages

Update `build.sh` to install in stages:

```bash
# Stage 1: Core dependencies
pip install Django==4.2.26 django-ninja==1.4.5 gunicorn whitenoise psycopg2-binary dj-database-url

# Stage 2: ML dependencies (let pip resolve)
pip install sentence-transformers==5.1.2

# Stage 3: Remaining dependencies
pip install -r requirements.txt
```

## Common Build Issues

### Issue 1: Connection Timeout
**Solution**: The build script now has retry logic and longer timeouts.

### Issue 2: Memory Issues
**Solution**: 
- Upgrade to a larger Render plan
- Install dependencies in stages
- Remove unused packages

### Issue 3: Build Timeout
**Solution**:
- Increase build timeout in Render settings
- Optimize requirements.txt
- Use cached builds

### Issue 4: Package Conflicts
**Solution**:
- Let pip resolve dependencies automatically
- Remove explicit version pins where possible
- Use version ranges instead of exact versions

## Verification Steps

After deployment, verify:

1. **Application starts**:
   ```bash
   curl https://your-app.onrender.com/api/hello
   ```

2. **Dependencies are installed**:
   ```bash
   python -c "import django; print('Django OK')"
   python -c "import chromadb; print('ChromaDB OK')"
   python -c "from sentence_transformers import SentenceTransformer; print('sentence-transformers OK')"
   ```

3. **Static files are served**:
   - Check browser console for 404 errors
   - Verify CSS/JS files load

4. **Database connection**:
   - Check application logs
   - Verify migrations ran
   - Test database queries

## Next Steps

1. Commit and push the updated files
2. Monitor build logs on Render
3. Verify deployment succeeds
4. Test all features
5. Monitor application performance

---

**If issues persist, check the build logs for specific error messages and adjust accordingly.**

