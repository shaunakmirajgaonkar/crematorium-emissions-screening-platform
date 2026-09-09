```bash
cd ~/Downloads/CrematoriumEmissionsScreeningPlatform_EmberGuard_Local
rm -rf .git
git init
git branch -M main
git add -A
git status
git commit -m "feat: add EmberGuard crematorium emissions screening platform"
git remote remove origin 2>/dev/null || true
git remote add origin https://github.com/shaunakmirajgaonkar/crematorium-emissions-screening-platform.git
git push -u origin main --force
```
