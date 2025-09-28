#!/usr/bin/env python3
"""
Professional Build Automation Script for PyInstaller with Kivy/KivyMD support
Handles: cleaning, versioning, building, signing, and archiving
"""

import argparse
import os
import sys
import shutil
import subprocess
import json
from pathlib import Path
from datetime import datetime
import re


class BuildAutomator:
    def __init__(self, project_root=os.getcwd()):
        self.project_root = Path(project_root).resolve()
        self.src_dir = self.project_root / "src"
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        self.automation_dir = self.project_root / "app_builder"
        self.spec_file = self.project_root / "build.spec"

        # Version management
        self.version_file = self.automation_dir / "version.json"
        self.version_template = self.automation_dir / "templates" / "version.template"

        # Output naming
        self.project_name = "Relo-Downloader"
        self.version = None

        # Determine build type from environment
        self.build_type = self._get_build_type()

    def _get_build_type(self):
        """Determine build type from environment variables"""
        # Check multiple possible environment variables
        env_vars = ['BUILD_TYPE', 'CI', 'GITHUB_ACTIONS', 'GITLAB_CI', 'RELEASE']

        for env_var in env_vars:
            value = os.getenv(env_var, '').lower()
            if value:
                if env_var == 'CI' or env_var.endswith('_CI'):
                    # CI environment usually means release build
                    return 'release'
                elif value in ['release', 'production', 'prod', 'true', '1']:
                    return 'release'
                elif value in ['development', 'dev', 'debug', 'false', '0']:
                    return 'development'

        # Default to development if no environment variables set
        return 'development'

    def _is_release_build(self):
        """Check if this is a release build"""
        return self.build_type == 'release'

    def _is_ci_environment(self):
        """Check if running in CI environment"""
        ci_vars = ['CI', 'GITHUB_ACTIONS', 'GITLAB_CI', 'JENKINS_URL', 'TRAVIS']
        return any(os.getenv(var) for var in ci_vars)

    def clean(self, everything=False):
        """Clean build artifacts"""
        print("[+] Cleaning build artifacts...")
        print(f"[+] Build type: {self.build_type.upper()}")

        folders_to_remove = []
        if self.build_dir.exists():
            folders_to_remove.append(self.build_dir)
        if self.dist_dir.exists() and everything:
            folders_to_remove.append(self.dist_dir)

        for folder in folders_to_remove:
            print(f"[-] Removing {folder}")
            shutil.rmtree(folder, ignore_errors=True)

        # Clean __pycache__ directories
        for pycache in self.project_root.rglob("__pycache__"):
            shutil.rmtree(pycache, ignore_errors=True)

        # Remove spec file if clean_all
        if everything and self.spec_file.exists():
            self.spec_file.unlink()
            print(f"[-] Removing {self.spec_file}")

        print("[-] Clean complete")
    
    def create_installer(self):
        """Create a Windows Installer using Inno Setup Compiler."""
        print("[+] Creating Windows installer (Inno Setup)...")
        
        if os.name != 'nt':
            print("[-] Skipping installer creation: Inno Setup is only for Windows builds.")
            return False
            
        inno_setup_compiler = "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe"
        installer_script = self.automation_dir / "installer.iss"
        
        if not Path(inno_setup_compiler).exists():
            print(f"[-] Inno Setup Compiler not found at '{inno_setup_compiler}'. Skipping installer creation.")
            print("    Please install Inno Setup or update the ISCC.exe path.")
            return False
            
        if not installer_script.exists():
            print(f"[-] Inno Setup script not found at '{installer_script}'. Skipping.")
            return False

        # Define build-specific variables to pass to the Inno Setup script
        # This allows dynamic naming and conditional logic inside the .iss file.
        defines = [
            f"/Dapp_builder.BuildType={self.build_type}"
        ]

        try:
            cmd = [inno_setup_compiler, *defines, str(installer_script)]
            print(f"[+] Command: {' '.join(cmd)}")
            subprocess.run(cmd, cwd=self.project_root, check=True, capture_output=True, text=True)
            print("[+] Windows Installer created successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[-] Installer creation failed. Error: {e.stderr}")
            return False

    def get_current_version(self):
        """Read current version from version.json or return default"""
        if self.version_file.exists():
            try:
                with open(self.version_file, 'r') as f:
                    version_data = json.load(f)
                    return version_data.get('version', '1.0.0.0')
            except:
                pass

        return '1.0.0.0'

    def generate_version(self, bump_type=None):
        """Generate or bump version number with build type"""
        print("[+] Version management...")
        print(f"[+] Build type: {self.build_type.upper()}")

        current_version = self.get_current_version()
        print(f"[+] Current version: {current_version}")

        if bump_type:
            # Parse version
            match = re.match(r'(\d+)\.(\d+)\.(\d+)\.(\d+)', current_version)
            if match:
                major, minor, patch, build = map(int, match.groups())

                if bump_type == 'major':
                    major += 1
                    minor = 0
                    patch = 0
                elif bump_type == 'minor':
                    minor += 1
                    patch = 0
                elif bump_type == 'patch':
                    patch += 1
                elif bump_type == 'build':
                    build += 1

                new_version = f"{major}.{minor}.{patch}.{build}"
            else:
                new_version = current_version
        else:
            new_version = current_version

        self.version = new_version
        print(f"[+] New version: {self.version}")

        # Update version file with build type
        version_data = {
            "version": self.version,
            "build_date": datetime.now().isoformat(),
            "build_type": self.build_type,
            "build_environment": "ci" if self._is_ci_environment() else "local",
            "is_release": self._is_release_build()
        }

        # Ensure assets directory exists
        self.version_file.parent.mkdir(exist_ok=True)

        with open(self.version_file, 'w') as f:
            json.dump(version_data, f, indent=2)

        print("[+] Version updated with build type")
        return new_version

    def generate_version_resource(self):
        """Generate Windows version resource file from template with build type"""
        if not self.version_template.exists():
            print("[+] Version template not found, skipping version resource")
            return None

        with open(self.version_template, 'r') as f:
            template_content = f.read()

        # Replace version placeholders
        version_parts = self.version.split('.')
        version_data = {
            'VERSION_MAJOR': version_parts[0],
            'VERSION_MINOR': version_parts[1],
            'VERSION_PATCH': version_parts[2],
            'VERSION_BUILD': version_parts[3],
            'FULL_VERSION': self.version,
            'CURRENT_YEAR': str(datetime.now().year),
            'BUILD_TYPE': self.build_type.upper(),
            'IS_RELEASE': '1' if self._is_release_build() else '0'
        }

        version_content = template_content
        for key, value in version_data.items():
            version_content = version_content.replace(f'{{{key}}}', value)

        version_resource_file = self.project_root / "version.txt"
        with open(version_resource_file, 'w') as f:
            f.write(version_content)

        print(f"[+] Version resource generated for {self.build_type} build")
        return version_resource_file

    def generate_spec_file(self):
        """Generate the Kivy/KivyMD compatible spec file"""
        print("[+] Generating Kivy/KivyMD spec file...")
        print(f"[+] Build type: {self.build_type.upper()}")

        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

import os
import sys
from kivy_deps import sdl2, glew
from kivymd import hooks_path as kivymd_hooks_path
import kivymd.icon_definitions
from glob import glob

kv_files = [(f, f.replace("src/", "")) for f in glob("src/kivy_files/**/*.kv", recursive=True)]
asset_files = [(f, f.replace("src/", "")) for f in glob("src/assets/*", recursive=True)]
datas = kv_files + asset_files + [("src/*.kv", ".")]

path = os.path.abspath(".")

a = Analysis(
    ['src/main.py'],
    pathex=[path],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[kivymd_hooks_path],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

splash = Splash(
    os.path.abspath('src/assets/relodownloader-splash.png'),
    binaries=a.binaries,
    datas=a.datas,
    text_pos=None,
    text_size=12,
    minify_script=True,
    always_on_top=False,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
    name="{self.project_name}.exe",
    debug={'all' if not self._is_release_build() else False},
    bootloader_ignore_signals=False,
    strip={self._is_release_build()},
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="src/assets/launcher-icon.ico",
    version="version.txt"
)
'''

        with open(self.spec_file, 'w', encoding='utf-8') as f:
            f.write(spec_content)

        print("[+] Spec file generated")
        return True

    def generate_certificate(self, file_path, cert_name):
        """Generate a self-signed certificate using an external PowerShell script."""
        print("[+] Generating self-signed certificate...")
        print(f"[+] Output Path: {file_path}")
        print(f"[+] Cert Name: {cert_name}")

        if os.name != 'nt':
            print("[-] Certificate generation via PowerShell is only supported on Windows.")
            return False

        cert_script = self.automation_dir / "generate_cert.ps1"
        if not cert_script.exists():
            print(f"[-] Certificate generation script not found: {cert_script}")
            return False

        try:
            subprocess.run([
                'powershell', '-ExecutionPolicy', 'Bypass',
                '-File', str(cert_script), 
                '-FilePath', file_path,
                '-CertName', cert_name
            ], check=True)
            print("[+] Certificate generated successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[-] Certificate generation failed. PowerShell error: {e}")
            return False

    def build_with_spec(self, clean_build=True):
        """Build using the generated spec file with build type optimization"""
        print("[+] Building with spec file...")
        print(f"[+] Build type: {self.build_type.upper()}")

        if clean_build:
            self.clean()

        # Generate version resource
        version_file = self.generate_version_resource()

        # Build using the spec file with appropriate flags
        try:
            cmd = [
                'pyinstaller',
                '--clean',
                '--noconfirm',
            ]

            # Add optimization flags for release builds
            if self._is_release_build():
                #cmd.extend(['--strip']) # '--no-upx'
                print("[+] Release build: Using strip and no UPX for better performance")
            else:
                cmd.extend(['--debug', 'noarchive'])
                print("[+] Development build: Including debug information")

            cmd.append(str(self.spec_file))

            print(f"[+] Command: {' '.join(cmd)}")
            result = subprocess.run(cmd, cwd=self.project_root, check=True,
                                    capture_output=True, text=True)
            print("[+] Build successful")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[-] Build failed: {e}")
            print(f"Stderr: {e.stderr}")
            return False

    def sign_binary(self, binary_path, cert_source, cert_password=""):
        """Sign the executable (platform-specific)"""
        print(f"[+] Signing binary: {binary_path}")
        print(f"[+] Build type: {self.build_type.upper()}")

        if not os.path.exists(binary_path):
            print("[-] Binary not found for signing")
            return False

        if os.name == 'nt':  # Windows
            sign_script = self.automation_dir / "sign.ps1"
            if sign_script.exists():
                try:
                    subprocess.run([
                    'powershell', '-ExecutionPolicy', 'Bypass',
                    '-File', str(sign_script), 
                    '-FilePath', str(binary_path),
                    '-CertSource', cert_source,
                    '-CertPassword', cert_password if cert_password else "" # Pass empty string if none
                    ], check=True)
                    print("[+] Binary signed successfully")
                    return True
                except subprocess.CalledProcessError as e:
                    print(f"[-] Signing failed or not configured. Powershell error: {e}")
                    return False
        else:  # Linux/macOS
            sign_script = self.automation_dir / "sign.sh"
            if sign_script.exists() and os.access(sign_script, os.X_OK):
                try:
                    subprocess.run([str(sign_script), str(binary_path)], check=True)
                    print("[+] Binary signed")
                    return True
                except subprocess.CalledProcessError:
                    print("[-]  Signing failed or not configured")
                    return False

        print("[-] Signing scripts not found or not executable")
        return False

    def create_archive(self):
        """Create distribution archive for onedir build with build type in filename"""
        print("[-] Creating distribution archive...")
        print(f"[+] Build type: {self.build_type.upper()}")

        build_name = self.project_name
        folder_path = self.dist_dir
        archive_name = f"{build_name}-v{self.version}-{self.build_type}-windows-x64.zip"

        if not folder_path.exists():
            print("[-] Build directory not found for archiving")
            return None

        # Create archive
        archive_path = self.dist_dir / archive_name
        try:
            import zipfile
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_to_zip = os.path.join(root, file)
                        arcname = os.path.relpath(file_to_zip, self.dist_dir)
                        zipf.write(file_to_zip, arcname)

            print(f"[+] {self.build_type.upper()} archive created: {archive_path}")
            return archive_path
        except Exception as e:
            print(f"[-] Archive creation failed: {e}")
            return None

    def run_tests(self):
        """Run tests before building with build type context"""
        print("[-] Running tests...")
        print(f"[+] Build context: {self.build_type.upper()}")

        # Set build type environment for tests
        env = os.environ.copy()
        env['BUILD_TYPE'] = self.build_type
        env['APP_VERSION'] = self.version if self.version else self.get_current_version()

        try:
            # Check if tests directory exists
            tests_dir = self.project_root / "src" / "tests"
            if not tests_dir.exists():
                print("[-] Tests directory not found, skipping tests")
                return True

            # Run unittest discovery with environment context
            result = subprocess.run([
                'python', '-m', 'unittest', 'discover', '-s', f'{tests_dir}', '-v'
            ], cwd=self.project_root, env=env, capture_output=True, text=True)

            if result.returncode == 0:
                print("[+] Tests passed")
                return True
            else:
                print(f"[+] Tests failed: {result.stderr}")
                return False
        except FileNotFoundError:
            print("[-]  unittest not found, skipping tests")
            return True
        except Exception as e:
            print(f"[-] Tests failed {e}")
            return False

    def full_build_pipeline(self, args):
        """
        Run the complete build pipeline for Kivy app
        """
        print("[+] Starting full Kivy build pipeline")
        print("=" * 50)
        print(f"[+] Build type: {self.build_type.upper()}")

        # Run tests first
        if not args.skip_tests and not self.run_tests():
            print("[-] Build aborted due to test failures")
            return False

        # Clean
        self.clean(args.clean_all)

        # Version management
        self.generate_version(args.bump)

        # Generate spec file
        self.generate_spec_file()

        # Build with spec file
        if not self.build_with_spec(clean_build=False):
            return False

        # Find the built binary (for onedir mode)
        build_name = self.project_name
        binary_path = self.dist_dir / f"{build_name}.exe"

        # Sign binary (typically only for release builds)
        if args.sign and binary_path.exists() and self._is_release_build():
            self.sign_binary(binary_path, args.cert_source, args.cert_password)
        elif args.sign and not self._is_release_build():
            print("[-] Skipping signing for development build")
        
        if args.installer:
            self.create_installer()

        # Create archive
        if args.archive:
            self.create_archive()

        print("=" * 50)
        print("[+] Kivy build pipeline completed successfully!")

        # Show final output paths
        if binary_path.exists():
            print(f"[+] Application: {binary_path}")
        archive_pattern = f"{self.project_name}-v{self.version}-{self.build_type}-windows-x64.zip"
        archive_path = self.dist_dir / archive_pattern
        if archive_path.exists():
            print(f"[+] Archive: {archive_path}")

        return True


def main():
    parser = argparse.ArgumentParser(description="Professional Build Automation for Kivy")
    parser.add_argument('--clean', action='store_true', help='Clean build artifacts')
    parser.add_argument('--clean-all', action='store_true', help='Clean everything including dist')
    parser.add_argument('--bump', choices=['major', 'minor', 'patch', 'build'],
                        help='Bump version number')
    parser.add_argument('--sign', action='store_true', help='Sign the binary')
    parser.add_argument('--archive', action='store_true', help='Create distribution archive')
    parser.add_argument('--skip-tests', action='store_true', help='Skip running tests')
    parser.add_argument('--full', action='store_true', help='Run full build pipeline')
    parser.add_argument('--generate-spec', action='store_true', help='Generate spec file only')
    parser.add_argument('--version', action='store_true', help='Show current version')
    parser.add_argument('--set-build-type', choices=['release', 'development'],
                        help='Override environment build type')
    parser.add_argument('--show-env', action='store_true',
                        help='Show current environment variables')
    parser.add_argument('--generate-cert', action='store_true', 
                        help='Generate a self-signed certificate using generate_cert.ps1')
    parser.add_argument('--cert-source', type=str, 
                        help='The path to the PFX/CER file OR the certificate thumbprint for signing.')
    parser.add_argument('--cert-password', type=str, default="", 
                        help='The password for the PFX certificate file.')
    parser.add_argument('--installer', action='store_true', help='Create a Windows installer using Inno Setup.')
    
    args = parser.parse_args()

    automator = BuildAutomator()

    if args.show_env:
        print("[+] Environment Variables:")
        for key, value in os.environ.items():
            if any(term in key.lower() for term in ['build', 'ci', 'release', 'dev']):
                print(f"   {key}={value}")
        return

    if args.set_build_type:
        # Override environment variable
        os.environ['BUILD_TYPE'] = args.set_build_type
        print(f"[+] Overriding build type to: {args.set_build_type}")
        # Reinitialize to pick up the new value
        automator = BuildAutomator()
    
    if args.generate_cert:
        cert_path = str(automator.project_root)
        cert_name = automator.project_name + "-SigningCert"
        automator.generate_certificate(cert_path, cert_name)

    if args.version:
        version = automator.get_current_version()
        print(f"Current version: {version}")
    elif args.generate_spec:
        automator.generate_spec_file()
    elif args.clean or args.clean_all:
        automator.clean(args.clean_all)
    elif args.full:
        if args.sign and not args.cert_source:
            print("[-] Error: --sign requires --cert-source to be specified.")
            sys.exit(1)

        automator.full_build_pipeline(args)
    else:
        # Show help if no arguments
        parser.print_help()


if __name__ == "__main__":
    main()