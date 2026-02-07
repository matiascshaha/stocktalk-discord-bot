#!/usr/bin/env python3
"""
Setup Script for Discord Stock Monitor

Automatically creates virtual environment, installs dependencies, and sets up the project.
"""

import sys
import os
import subprocess
import platform

def print_step(step_num, message):
    """Print a formatted step message"""
    print(f"\n{'='*60}")
    print(f"Step {step_num}: {message}")
    print('='*60)

def run_command(command, shell=False, check=True):
    """Run a shell command and handle errors"""
    try:
        if isinstance(command, str):
            result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        else:
            result = subprocess.run(command, shell=shell, check=check, capture_output=True, text=True)
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return None

def check_python_version():
    """Check if Python version is 3.8+"""
    print_step(1, "Checking Python Version")
    
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required!")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print("✅ Python version is compatible")
    return True

def create_venv():
    """Create virtual environment"""
    print_step(2, "Creating Virtual Environment")
    
    venv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'venv')
    
    if os.path.exists(venv_path):
        print(f"⚠️  Virtual environment already exists at: {venv_path}")
        response = input("   Do you want to recreate it? (y/N): ").strip().lower()
        if response == 'y':
            print("   Removing existing virtual environment...")
            if platform.system() == 'Windows':
                run_command(f'rmdir /s /q "{venv_path}"', shell=True, check=False)
            else:
                run_command(f'rm -rf "{venv_path}"', shell=True, check=False)
        else:
            print("   Using existing virtual environment")
            return venv_path
    
    print(f"Creating virtual environment at: {venv_path}")
    result = run_command([sys.executable, '-m', 'venv', venv_path], check=True)
    
    if result:
        print("✅ Virtual environment created successfully")
        return venv_path
    else:
        print("❌ Failed to create virtual environment")
        return None

def get_pip_command(venv_path):
    """Get the pip command for the virtual environment"""
    if platform.system() == 'Windows':
        return os.path.join(venv_path, 'Scripts', 'pip.exe')
    else:
        return os.path.join(venv_path, 'bin', 'pip')

def get_python_command(venv_path):
    """Get the python command for the virtual environment"""
    if platform.system() == 'Windows':
        return os.path.join(venv_path, 'Scripts', 'python.exe')
    else:
        return os.path.join(venv_path, 'bin', 'python')

def install_requirements(venv_path):
    """Install requirements.txt"""
    print_step(3, "Installing Dependencies")
    
    project_root = os.path.dirname(os.path.dirname(__file__))
    requirements_file = os.path.join(project_root, 'requirements.txt')
    
    if not os.path.exists(requirements_file):
        print(f"❌ requirements.txt not found at: {requirements_file}")
        return False
    
    pip_cmd = get_pip_command(venv_path)
    
    # Upgrade pip first
    print("Upgrading pip...")
    run_command([pip_cmd, 'install', '--upgrade', 'pip'], check=False)
    
    # Install requirements
    print(f"Installing packages from {requirements_file}...")
    result = run_command([pip_cmd, 'install', '-r', requirements_file], check=True)
    
    if not result:
        print("❌ Failed to install dependencies")
        return False

    # Install project in editable mode for stable imports and IDE indexing
    print("Installing project in editable mode...")
    editable_result = run_command([pip_cmd, 'install', '-e', project_root], check=True)
    if not editable_result:
        print("❌ Failed to install project in editable mode")
        return False

    print("✅ All dependencies installed successfully")
    return True

def create_env_file():
    """Create .env file from .env.example if it doesn't exist"""
    print_step(4, "Setting Up Environment File")
    
    project_root = os.path.dirname(os.path.dirname(__file__))
    env_example = os.path.join(project_root, '.env.example')
    env_file = os.path.join(project_root, '.env')
    
    if os.path.exists(env_file):
        print("⚠️  .env file already exists")
        response = input("   Do you want to overwrite it? (y/N): ").strip().lower()
        if response != 'y':
            print("   Keeping existing .env file")
            return True
    
    if not os.path.exists(env_example):
        print(f"⚠️  .env.example not found at: {env_example}")
        print("   You'll need to create .env manually")
        return False
    
    # Copy .env.example to .env
    try:
        with open(env_example, 'r', encoding='utf-8') as src:
            with open(env_file, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        print("✅ Created .env file from .env.example")
        print("   ⚠️  IMPORTANT: Edit .env file and add your credentials!")
        print("   See docs/CREDENTIALS_SETUP.md for instructions")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def create_data_directory():
    """Create data directory if it doesn't exist"""
    print_step(5, "Creating Data Directory")
    
    project_root = os.path.dirname(os.path.dirname(__file__))
    data_dir = os.path.join(project_root, 'data')
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        # Create .gitkeep
        gitkeep = os.path.join(data_dir, '.gitkeep')
        with open(gitkeep, 'w') as f:
            f.write('')
        print(f"✅ Created data directory at: {data_dir}")
    else:
        print(f"✅ Data directory already exists at: {data_dir}")
    
    return True

def print_activation_instructions(venv_path):
    """Print instructions for activating the virtual environment"""
    print_step(6, "Setup Complete!")
    
    print("\n" + "="*60)
    print("Next Steps:")
    print("="*60)
    
    if platform.system() == 'Windows':
        activate_cmd = f"{venv_path}\\Scripts\\activate"
        print(f"\n1. Activate virtual environment:")
        print(f"   {activate_cmd}")
        print(f"   OR")
        print(f"   .\\venv\\Scripts\\activate")
    else:
        activate_cmd = f"source {venv_path}/bin/activate"
        print(f"\n1. Activate virtual environment:")
        print(f"   {activate_cmd}")
        print(f"   OR")
        print(f"   source venv/bin/activate")
    
    print(f"\n2. Edit .env file with your credentials:")
    print(f"   See docs/CREDENTIALS_SETUP.md for detailed instructions")
    
    print(f"\n3. Test your credentials:")
    print(f"   python -m scripts.test_credentials")
    
    print(f"\n4. Run the monitor:")
    print(f"   python -m src.main")
    
    print("\n" + "="*60)

def main():
    """Main setup function"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║     Discord Stock Monitor - Automated Setup Script        ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create virtual environment
    venv_path = create_venv()
    if not venv_path:
        sys.exit(1)
    
    # Install requirements
    if not install_requirements(venv_path):
        sys.exit(1)
    
    # Create .env file
    create_env_file()
    
    # Create data directory
    create_data_directory()
    
    # Print instructions
    print_activation_instructions(venv_path)
    
    print("\n✅ Setup completed successfully!\n")
    return 0

if __name__ == '__main__':
    sys.exit(main())
