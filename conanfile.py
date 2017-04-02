from conans import ConanFile, CMake, tools
import os
import re

class Options:
    def __init__(self, version, arch, exception, threads):
        self.version = version
        self.arch = arch
        self.exception = exception
        self.threads = threads

def create_releases(version, archs, exceptions, threads, sub_version, rt, revision):
    for arch in archs:
        for exception in exceptions:
            for thread in threads:
                if (arch == "x86" and exception == "seh"):
                    continue
                if (arch == "x86_64" and exception == "dwarf2"):
                    continue
                yield MinGWRelease(Options(version, arch, exception, thread), sub_version, rt, revision)

class MinGWCollection:
    def __init__(self):
        self.collection = {}
        self.threads = set()
        self.exception = set()
        self.arch = set()
        self.version = set()
        
    def generate_key(self, options):
        return (options.version, options.arch, options.exception, options.threads)

    def add_options(self, options):
        self.threads.add(options.threads)
        self.exception.add(options.exception)
        self.arch.add(options.arch)
        self.version.add(options.version)
    
    def add(self, release):
        key = self.generate_key(release.options)
        if key in self.collection:
            raise Exception()
        
        self.add_options(release.options)
        
        self.collection[key] = release
    
    def add_list(self, releases):
        for release in releases:
            self.add(release)

    def get_options(self):
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

    def __str__(self):
        return str(self.collection)
        

class MinGWRelease:

    def __init__(self, options, sub_version, rt, revision):
        self.options = options
        self.sub_version = sub_version
        self.rt = rt
        self.revision = revision
    
    @property
    def url(self):
        version = self.options.version + ('.%s' % self.sub_version if self.sub_version else '')
        arch = self.options.arch
        threads = self.options.threads
        exception = self.options.exception
        rt = self.rt
        revision = self.revision
        
        url = 'http://downloads.sourceforge.net/project/mingw-w64/Toolchains%20targetting%20Win64/Personal%20Builds/mingw-builds'
        path = '%s/threads-%s/%s' % (version, threads, exception)
        file = '%s-%s-release-%s-%s-rt_v%s-rev%s.7z' % (arch, version, threads, exception, rt, revision)
        
        return url + '/' + path + '/' + file



class MingwinstallerConan(ConanFile):
    name = "mingw_installer"
    version = "0.1"
    license = "MIT"
    url = "http://github.com/lasote/conan-mingw-installer"
    settings = {"os": ["Windows"]}
    
    mingw_collection = MinGWCollection()
    mingw_collection.add_list(create_releases("4.8", ["x86", "x86_64"], ["sjlj", "seh", "dwarf2"], ["posix", "win32"], "2", "3", "0"))
    mingw_collection.add_list(create_releases("4.9", ["x86", "x86_64"], ["sjlj", "seh", "dwarf2"], ["posix", "win32"], "2", "3", "1"))
    mingw_collection.add_list(create_releases("5.4", ["x86", "x86_64"], ["sjlj", "seh", "dwarf2"], ["posix", "win32"], "0", "5", "0"))
    mingw_collection.add_list(create_releases("6.2", ["x86", "x86_64"], ["sjlj", "seh", "dwarf2"], ["posix", "win32"], "0", "5", "1"))
    options = mingw_collection.get_options()
    
    default_options = "exception=sjlj", "threads=posix", "arch=x86_64", "version=4.9"
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

