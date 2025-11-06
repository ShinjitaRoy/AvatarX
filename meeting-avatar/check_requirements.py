import pkg_resources
import requirements

def check_requirements():
    # Get installed packages
    installed = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
    
    # Read requirements file
    required = {}
    with open('requirements.txt') as f:
        for req in requirements.parse(f):
            if req.name and req.specs:
                required[req.name.lower()] = req.specs[0][1]
            elif req.name:
                required[req.name.lower()] = None

    print("\nPackage Status:")
    print("-" * 50)
    
    for package, version in required.items():
        if package in installed:
            status = f"✓ {package:<20} Installed: {installed[package]:<10}"
            if version and installed[package] != version:
                status += f" (Required: {version})"
            print(status)
        else:
            print(f"✗ {package:<20} Not installed (Required: {version})")

if __name__ == "__main__":
    check_requirements()