from six.moves.urllib.parse import urlsplit
import os
import urllib
from urllib.request import urlretrieve

def path_to_string(path):
    """Convert `PathLike` objects to their string representation.

    If given a non-string typed path object, converts it to its string
    representation.

    If the object passed to `path` is not among the above, then it is
    returned unchanged. This allows e.g. passthrough of file objects
    through this function.

    Args:
      path: `PathLike` object that represents a path

    Returns:
      A string representation of the path argument, if Python support exists.
    """
    if isinstance(path, os.PathLike):
        return os.fspath(path)
    return path

def get_file(
    fname=None,
    origin=None,
    untar=False,
    md5_hash=None,
    file_hash=None,
    cache_subdir="luketils",
    hash_algorithm="auto",
    extract=False,
    archive_format="auto",
    cache_dir=None,
):
    """Downloads a file from a URL if it not already in the cache.

    By default the file at the url `origin` is downloaded to the
    cache_dir `~/.luketils`, placed in the cache_subdir `datasets`,
    and given the filename `fname`. The final location of a file
    `example.txt` would therefore be `~/.luketils/datasets/example.txt`.

    Files in tar, tar.gz, tar.bz, and zip formats can also be extracted.
    Passing a hash will verify the file after download. The command line
    programs `shasum` and `sha256sum` can compute the hash.

    Args:
        fname: Name of the file. If an absolute path `/path/to/file.txt` is
            specified the file will be saved at that location. If `None`, the
            name of the file at `origin` will be used.
        origin: Original URL of the file.
        untar: Deprecated in favor of `extract` argument.
            boolean, whether the file should be decompressed
        md5_hash: Deprecated in favor of `file_hash` argument.
            md5 hash of the file for verification
        file_hash: The expected hash string of the file after download.
            The sha256 and md5 hash algorithms are both supported.
        cache_subdir: Subdirectory under the Keras cache dir where the file is
            saved. If an absolute path `/path/to/folder` is
            specified the file will be saved at that location.
        hash_algorithm: Select the hash algorithm to verify the file.
            options are `'md5'`, `'sha256'`, and `'auto'`.
            The default 'auto' detects the hash algorithm in use.
        extract: True tries extracting the file as an Archive, like tar or zip.
        archive_format: Archive format to try for extracting the file.
            Options are `'auto'`, `'tar'`, `'zip'`, and `None`.
            `'tar'` includes tar, tar.gz, and tar.bz files.
            The default `'auto'` corresponds to `['tar', 'zip']`.
            None or an empty list will return no matches found.
        cache_dir: Location to store cached files, when None it
            defaults to the default directory `~/.luketils/`.

    Returns:
        Path to the downloaded file.
    """
    if origin is None:
        raise ValueError(
            'Please specify the "origin" argument (URL of the file '
            "to download)."
        )

    if cache_dir is None:
        cache_dir = os.path.join(os.path.expanduser("~"), ".luketils")
    if md5_hash is not None and file_hash is None:
        file_hash = md5_hash
        hash_algorithm = "md5"
    datadir_base = os.path.expanduser(cache_dir)
    if not os.access(datadir_base, os.W_OK):
        datadir_base = os.path.join("/tmp", ".luketils")
    datadir = os.path.join(datadir_base, cache_subdir)
    _makedirs_exist_ok(datadir)

    fname = path_to_string(fname)
    if not fname:
        fname = os.path.basename(urlsplit(origin).path)
        if not fname:
            raise ValueError(
                "Can't parse the file name from the origin provided: "
                f"'{origin}'."
                "Please specify the `fname` as the input param."
            )

    if untar:
        if fname.endswith(".tar.gz"):
            fname = pathlib.Path(fname)
            # The 2 `.with_suffix()` are because of `.tar.gz` as pathlib
            # considers it as 2 suffixes.
            fname = fname.with_suffix("").with_suffix("")
            fname = str(fname)
        untar_fpath = os.path.join(datadir, fname)
        fpath = untar_fpath + ".tar.gz"
    else:
        fpath = os.path.join(datadir, fname)

    download = False
    if os.path.exists(fpath):
        # File found; verify integrity if a hash was provided.
        if file_hash is not None:
            if not validate_file(fpath, file_hash, algorithm=hash_algorithm):
                print(
                    "A local file was found, but it seems to be "
                    f"incomplete or outdated because the {hash_algorithm} "
                    "file hash does not match the original value of "
                    f"{file_hash} "
                    "so we will re-download the data."
                )
                download = True
    else:
        download = True

    if download:
        print(f"Downloading data from {origin}")
        error_msg = "URL fetch failure on {}: {} -- {}"
        try:
            try:
                urlretrieve(origin, fpath)
            except urllib.error.HTTPError as e:
                raise Exception(error_msg.format(origin, e.code, e.msg))
            except urllib.error.URLError as e:
                raise Exception(error_msg.format(origin, e.errno, e.reason))
        except (Exception, KeyboardInterrupt):
            if os.path.exists(fpath):
                os.remove(fpath)
            raise

        # Validate download if succeeded and user provided an expected hash
        # Security conscious users would get the hash of the file from a
        # separate channel and pass it to this API to prevent MITM / corruption:
        if os.path.exists(fpath) and file_hash is not None:
            if not validate_file(fpath, file_hash, algorithm=hash_algorithm):
                raise ValueError(
                    "Incomplete or corrupted file detected. "
                    f"The {hash_algorithm} "
                    "file hash does not match the provided value "
                    f"of {file_hash}."
                )

    if untar:
        if not os.path.exists(untar_fpath):
            _extract_archive(fpath, datadir, archive_format="tar")
        return untar_fpath

    if extract:
        _extract_archive(fpath, datadir, archive_format)

    return fpath


def _makedirs_exist_ok(datadir):
    os.makedirs(datadir, exist_ok=True)
