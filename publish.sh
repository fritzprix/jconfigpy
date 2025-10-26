#!/bin/bash
# PyPI에 패키지 배포하는 스크립트
# 요구사항: twine, setuptools, wheel

set -e

echo "🚀 jconfigpy를 PyPI에 배포 중..."

# 1. 기존 dist 디렉토리 정리
if [ -d dist ]; then
    echo "🧹 기존 dist 디렉토리 정리..."
    rm -rf dist build *.egg-info
fi

# 2. 배포 패키지 빌드
echo "📦 배포 패키지 빌드 중..."
python3 setup.py sdist bdist_wheel

# 3. 패키지 검증
echo "✅ 패키지 검증 중..."
twine check dist/*

# 4. PyPI에 업로드
echo "📤 PyPI에 업로드 중..."
twine upload dist/*

echo "✅ 배포 완료!"
