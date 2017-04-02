from conans import ConanFile, CMake, tools
import os
import re
import urllib

class SimpleOptions:
    def __init__(self, version, arch, exception, threads):
        self.version = version
        self.arch = arch
        self.exception = exception
        self.threads = threads

class MinGWCollection:
    def __init__(self, release_matrixes):
        self.collection = {}
        self.threads = set()
        self.exception = set()
        self.arch = set()
        self.version = set()
        for release_matrix in release_matrixes:
            self.add_release_matrix(*release_matrix)
        
    def generate_key(self, options):
        return (str(options.version), str(options.arch), str(options.exception), str(options.threads))

    def add_options(self, options):
        self.threads.add(options.threads)
        self.exception.add(options.exception)
        self.arch.add(options.arch)
        self.version.add(options.version)
    
    def add(self, release):
        key = self.generate_key(release.options)
        if key in self.collection:
            raise Exception("Duplicate package added %s" % release)
        
        self.add_options(release.options)
        
        self.collection[key] = release
    
    def add_release_matrix(self, version, archs, exceptions, threads, sub_version, rt, revision):
        for arch in archs:
            for exception in exceptions:
                for thread in threads:
                    if (arch == "x86" and exception == "seh"):
                        continue
                    if (arch == "x86_64" and exception == "dwarf2"):
                        continue
                    self.add(MinGWRelease(SimpleOptions(version, arch, exception, thread), sub_version, rt, revision))

    def generate_options(self):
        return {
            "threads": list(self.threads),
            "exception": list(self.exception),
            "arch": list(self.arch),
            "version": list(self.version),
        }

    def get_url(self, options):
        key = self.generate_key(options)
        return self.collection[key].url
    
    def validate_options(self, options):
        key = self.generate_key(options)
        if key not in self.collection:
            raise Exception("Not valid %s and %s combination!" % (options.arch, options.exception))
        
class MinGWRelease:

    def __init__(self, options, sub_version, rt, revision):
        self.options = options
        self.sub_version = sub_version
        self.rt = rt
        self.revision = revision
    
    @property
    def url(self):
        version = self.options.version + ('.%s' % self.sub_version if self.sub_version else '')
        arch = self.options.arch if self.options.arch is not "x86" else "i686"
        path_arch = 'Win64' if arch == "x86_64" else 'Win32'
        threads = self.options.threads
        exception = self.options.exception if self.options.exception is not "dwarf2" else "dwarf"
        rt = self.rt
        revision = self.revision
        url = 'downloads.sourceforge.net/project/mingw-w64'
        path = 'Toolchains targetting %s/Personal Builds/mingw-builds/%s/threads-%s/%s' % (path_arch, version, threads, exception)
        file = '%s-%s-release-%s-%s-rt_v%s-rev%s.7z' % (arch, version, threads, exception, rt, revision)
        
        return 'http://' + urllib.parse.quote(url + '/' + path + '/' + file)

mingw_matrix = MinGWCollection((
    ("4.8", ["x86", "x86_64"], ["sjlj", "seh", "dwarf2"], ["posix", "win32"], "2", "3", "0"),
    ("4.9", ["x86", "x86_64"], ["sjlj", "seh", "dwarf2"], ["posix", "win32"], "2", "3", "1"),
    ("5.4", ["x86", "x86_64"], ["sjlj", "seh", "dwarf2"], ["posix", "win32"], "0", "5", "0"),
    ("6.2", ["x86", "x86_64"], ["sjlj", "seh", "dwarf2"], ["posix", "win32"], "0", "5", "1"),
    ("6.3", ["x86", "x86_64"], ["sjlj", "seh", "dwarf2"], ["posix", "win32"], "0", "5", "1"),
))

class MingwinstallerConan(ConanFile):
    name = "mingw_installer"
    version = "0.1"
    license = "MIT"
    url = "http://github.com/KalleDK/conan-mingw-installer"
    settings = {"os": ["Windows"]}
    
    mingw_collection = mingw_matrix
    options = mingw_collection.generate_options()
    
    default_options = "exception=sjlj", "threads=posix", "arch=x86_64", "version=6.3"
    build_policy = "missing"

    def configure(self):
        self.requires.add("7z_installer/0.1@lasote/testing", private=True)
        self.mingw_collection.validate_options(self.options)

    def build(self):
        tools.download(self.mingw_collection.get_url(self.options), "file.7z")
        self.run("7z x file.7z")
    
    def package(self):
        self.copy("*", dst="", src="mingw32")
        self.copy("*", dst="", src="mingw64")

    def package_info(self):
        self.env_info.path.append(os.path.join(self.package_folder, "bin"))
        self.env_info.CXX = os.path.join(self.package_folder, "bin", "g++.exe")
        self.env_info.CC = os.path.join(self.package_folder, "bin", "gcc.exe")

