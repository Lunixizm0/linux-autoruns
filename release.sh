#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:?Kullanım: ./release.sh 2.9.0}"
TAG="v${VERSION}"

echo "pyproject.toml güncelleniyor..."
sed -i "s/^version = .*/version = \"${VERSION}\"/" pyproject.toml

echo "Testler çalıştırılıyor..."
uv run pytest tests/ -v

echo "Commit ediliyor..."
git add pyproject.toml
git diff --cached --quiet || git commit -m "release: ${TAG}"

echo "Tag oluşturuluyor..."
git tag -f "${TAG}"

echo "Push ediliyor..."
git push origin master "${TAG}" --force

echo "GitHub Release oluşturuluyor..."
gh release delete "${TAG}" --yes --cleanup-tag 2>/dev/null || true
gh release create "${TAG}" \
  --title "${TAG}" \
  --generate-notes

echo ""
echo "${TAG} yayınlandı! GitHub Actions PyPI'ya yüklüyor."
echo "https://github.com/Lunixizm0/linux-autoruns/actions"
echo "https://pypi.org/project/linux-autoruns/${VERSION}/"