
__version__ = [1,0,0,'b21']

version = '.'.join(str(i) for i in __version__)
version_api = '.'.join(str(v).title() for v in __version__[:2])

PYGRID_VERSION='.'.join(str(i) for i in __version__)
PYGRID_MAJOR_VERSION=__version__[0]
PYGRID_MINOR_VERSION=__version__[1]
PYGRID_PATCH_VERSION=__version__[2]
PYGRID_RELEASE_VERSION=__version__[-1]
