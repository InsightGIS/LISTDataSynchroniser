####=================####
#Authors: Alex Leith, Duri Bradshaw
#Date: 2026-03-02
#Purpose: Download files from theLIST to a local directory over FTP, will skip any file that has not changed since last update.
#Version: 1.0 - Initial release
#Version: 2.0 - Added retry logic for FTP connection and downloads, with logging of attempts and errors.
####=================####

import os.path, time
import ftplib
import socket #used to catch ftp error
import ExtendedMethods
import globals



# configuration defaults
DEFAULT_MAX_RETRIES = 3      # used for both connection and download
DEFAULT_RETRY_DELAY = 5      # seconds between attempts


def retry_operation(func, max_retries=DEFAULT_MAX_RETRIES, delay=DEFAULT_RETRY_DELAY, on_error=None, *args, **kwargs):
    """Execute *func* with the given args/kwargs, retrying on exception.

    ``on_error`` if supplied is called as ``on_error(exception, attempt)``.
    The last exception is re-raised if all attempts fail.
    """
    attempt = 0
    while True:
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            attempt += 1
            if on_error:
                on_error(exc, attempt)
            if attempt >= max_retries:
                raise
            time.sleep(delay)


def connect_ftp(server, directory):
    """Return an authenticated ``ftplib.FTP`` instance pointed at *directory*.

    Retries using ``retry_operation``.
    """
    def _open():
        ftp = ftplib.FTP(server.url)
        ftp.login(server.username, server.password)
        ftp.cwd(directory)
        return ftp

    def _log_error(exc, attempt):
        globals.logging.error(
            "FTP connection failed on attempt %i: %s" % (attempt, exc)
        )
        print("Error: FTP connection attempt %i failed." % attempt)

    return retry_operation(_open, on_error=_log_error)


def list_remote_files(ftp, file_types):
    """Return list of ``(name, size, timestamp)`` for files matching types."""
    files = []
    for name in ftp.nlst():
        if os.path.splitext(name)[1].lower() in file_types:
            ts = int(ftp.sendcmd("MDTM %s" % name)[4:])
            files.append((name, ftp.size(name), ts))
    return files


def syncDirectory(server, files):
    """Walk each directory on *server* and grab changed/new files."""
    for directory in server.directories:
        try:
            ftp = connect_ftp(server, directory)
        except Exception:
            globals.logging.error(
                "Unable to connect to %s after %i attempts, skipping." %
                (directory, DEFAULT_MAX_RETRIES)
            )
            continue

        globals.logging.info("Connected to %s@%s" % (server.username, server.url))
        print('REMOTE: %s@%s' % (server.username, server.url))

        remote_files = list_remote_files(ftp, files.fileTypes)
        local_files = {
            name: (size, ts)
            for name, size, ts in ExtendedMethods.getLocalFiles(files)
        }

        print('LOCAL: %s' % files.localPath)

        unchanged = 0
        for name, size, ts in remote_files:
            print('Remote file: %s' % name)
            if name in local_files:
                lsize, lts = local_files[name]
                if size == lsize and ts < lts:
                    globals.logging.debug(
                        'Skip %s, unchanged (size %i, ts %i)' %
                        (name, size, ts)
                    )
                    unchanged += 1
                    continue
                globals.logging.info('File has changed: %s' % name)
                target = os.path.join(files.localPath, name)
            else:
                globals.logging.info('New file found: %s' % name)
                target = os.path.join(files.localPath, name)

            ftpDownloadFile(ftp, name, target, files)

        globals.logging.info("%i unchanged files found, not downloading." % unchanged)

# Download over FTP using shared retry helper
def ftpDownloadFile(connection, remoteFile, localFile, files):
    def _do_download():
        with open(localFile, "wb") as f:
            connection.retrbinary("RETR " + remoteFile, f.write)

    def _log_error(exc, attempt):
        globals.logging.error("Failed to retrieve %s (attempt %i): %s" % (remoteFile, attempt, exc))
        print("Downloading: %s (attempt %i)" % (remoteFile, attempt))

    try:
        retry_operation(_do_download, on_error=_log_error)
        globals.downloadedFiles.append(remoteFile)
        globals.logging.info("Retrieved: %s to: %s" % (remoteFile, localFile))
        if files.unzip == "True":
            globals.logging.info("Unzipping %s..." % localFile)
            ExtendedMethods.unzip(localFile, files.localPath)
        return True
    except Exception:
        globals.logging.error("Download failed for %s after %i attempts" %
                              (remoteFile, DEFAULT_MAX_RETRIES))
        print("Error: Download failed for %s after %i attempts." %
              (remoteFile, DEFAULT_MAX_RETRIES))
        return False