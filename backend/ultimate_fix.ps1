Write-Host "Running ultimate fix for huggingface_hub..." -ForegroundColor Yellow

# 1. Check current version
python -c "
import huggingface_hub
print(f'huggingface_hub version: {huggingface_hub.__version__}')
print('Available imports:')
import inspect
members = inspect.getmembers(huggingface_hub)
for name, _ in members:
    if 'download' in name.lower():
        print(f'  - {name}')
"

# 2. Patch the library file
$library_path = "..\venv\Lib\site-packages\sentence_transformers\SentenceTransformer.py"
if (Test-Path $library_path) {
    Write-Host "`nPatching $library_path..." -ForegroundColor Cyan
    $content = Get-Content $library_path -Raw
    
    # Check what import line looks like
    if ($content -match "from huggingface_hub import.*cached_download") {
        Write-Host "Found problematic import line" -ForegroundColor Yellow
        
        # Replace with correct import
        $new_content = $content -replace "from huggingface_hub import HfApi, HfFolder, Repository, hf_hub_url, cached_download", "from huggingface_hub import HfApi, HfFolder, Repository, hf_hub_url, hf_hub_download as cached_download"
        
        $new_content | Set-Content $library_path -NoNewline
        Write-Host "✅ File patched!" -ForegroundColor Green
    } else {
        Write-Host "Could not find the import pattern" -ForegroundColor Red
        Write-Host "File content snippet:" -ForegroundColor Yellow
        Get-Content $library_path -First 20
    }
} else {
    Write-Host "❌ Library file not found at: $library_path" -ForegroundColor Red
}

# 3. Test
Write-Host "`nTesting patch..." -ForegroundColor Cyan
python -c "
try:
    from sentence_transformers import SentenceTransformer
    print('✅ sentence-transformers imports work!')
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print('✅ Model loads successfully!')
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
"