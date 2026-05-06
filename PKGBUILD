pkgname=spotube-converter
pkgver=0.1.0
pkgrel=1
pkgdesc="A CLI tool to convert Spotify CSV playlists to YouTube Music playlists"
arch=('any')
url="https://github.com/yourusername/spotube-converter"
license=('MIT')
depends=('python' 'python-pandas')
makedepends=('python-build' 'python-installer' 'python-setuptools' 'python-wheel')
source=("spotube-converter-$pkgver.tar.gz")
sha256sums=('SKIP')

build() {
    cd "$srcdir/spotube-converter"
    python -m build --wheel --no-isolation
}

package() {
    cd "$srcdir/spotube-converter"
    python -m installer --destdir="$pkgdir" dist/*.whl
}
