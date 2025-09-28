## Initial Setup and Environment
These commands are used to prepare your local development environment before running the build script.

    Command	                            Platform	            Description
    python -m venv venv	                All	                    Creates a Python Virtual Environment named venv.
    venv\Scripts\activate	            Windows	                Activates the virtual environment.
    source venv/bin/activate            Linux/macOS	            Activates the virtual environment.
    pip install -r requirements.txt	    All	                    Installs all required Python dependencies.

## Build Pipeline Commands
These commands execute the main build and maintenance tasks using the script.

    Command	                                                    Description
    python app_builder/build.py --full	                        Runs the full build pipeline (test, clean, versioning, spec, build). The build type is auto-detected (defaulting to development).

    python app_builder/build.py --bump minor --full --archive	Bumps the minor version in version.json, runs the full build, and then creates a final distribution archive (ZIP).

    python app_builder/build.py --clean-all --full	            Cleans all artifacts (build/ and dist/), then runs a new full build.

    python app_builder/build.py --generate-spec	                Only generates the PyInstaller spec file (build.spec) based on current configurations.

    python app_builder/build.py --version	                    Shows the current application version read from version.json.

    python app_builder/build.py --show-env	                    Displays relevant environment variables that        influence the build process (e.g., BUILD_TYPE, CI).

## Build Type Management
The script uses a build_type flag (either development or release) to apply optimizations, include debug code, or enable signing.

    Auto-Detection and Default
    Command	                                                    Description
    python app_builder/build.py --full	                        The script auto-detects the build type. If no environment variables are set, it defaults to development.

    (CI Environments)	The script automatically sets build_type to release if common CI environment variables are detected (e.g., GITHUB_ACTIONS, GITLAB_CI).
    
## Overriding the Build Type
You can explicitly set the build type either via environment variables or a command-line flag.

    Command	Platform	                                            Description
    python app_builder/build.py --full --set-build-type release	    All	Overrides the environment setting and forces a release build.

    export BUILD_TYPE=release python app_builder/build.py --full	Linux/macOS	Sets the environment variable before execution.

    BUILD_TYPE=release python app_builder/build.py --full	        Linux/macOS	Sets the environment variable for only this command.

    $env:BUILD_TYPE="release"; python app_builder/build.py --full	Windows (PowerShell)	Sets the environment variable for only this command.
    
    set BUILD_TYPE=release && python app_builder/build.py --full	Windows (CMD)	Sets the environment variable for only this command.
