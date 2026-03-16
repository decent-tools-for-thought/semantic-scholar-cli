pkgname=semantic-scholar-tool
_modname=semantic_scholar_tool
pkgver=0.1.0
pkgrel=1
pkgdesc="Semantic Scholar CLI for Graph, Recommendations, and Datasets APIs"
arch=('any')
url="https://api.semanticscholar.org/"
license=('custom')
depends=('python')
makedepends=('python-build' 'python-installer' 'python-setuptools' 'python-wheel')
checkdepends=('python')
source=()
sha256sums=()

prepare() {
  local buildroot="$startdir/.makepkg-build"
  rm -rf "$buildroot"
  mkdir -p "$buildroot"
  cp -a "$startdir/PKGBUILD" "$startdir/README.md" "$startdir/PROJECT_OUTLINE.md" "$startdir/pyproject.toml" "$buildroot/"
  cp -a "$startdir/src" "$startdir/tests" "$buildroot/"
  rm -rf "$buildroot/src/semantic_scholar_tool/__pycache__" \
         "$buildroot/tests/__pycache__"
}

build() {
  cd "$startdir/.makepkg-build"
  python -m build --wheel --no-isolation
}

check() {
  cd "$startdir/.makepkg-build"
  PYTHONPATH=src python -m unittest discover -s tests -p 'test*.py'
}

package() {
  cd "$startdir/.makepkg-build"
  python -m installer --destdir="$pkgdir" dist/*.whl

  install -Dm644 README.md "$pkgdir/usr/share/doc/$pkgname/README.md"
  install -Dm644 PROJECT_OUTLINE.md "$pkgdir/usr/share/doc/$pkgname/PROJECT_OUTLINE.md"
}
