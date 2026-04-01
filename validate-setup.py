"""
GrowMate Voice Agent Setup Validator
Checks all prerequisites and validates configuration before running.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Tuple, List

logging.basicConfig(level=logging.INFO, format='  %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_header():
    """Print startup header."""
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"  GrowMate Voice Agent Setup Validator")
    print(f"{'='*60}{Colors.END}\n")

def print_section(title: str):
    """Print section separator."""
    print(f"\n{Colors.BLUE}{title}{Colors.END}")
    print(f"{'-'*60}")

def check_pass(message: str):
    """Print passing check."""
    print(f"  {Colors.GREEN}✓{Colors.END} {message}")

def check_fail(message: str):
    """Print failing check."""
    print(f"  {Colors.RED}✗{Colors.END} {message}")

def check_warn(message: str):
    """Print warning check."""
    print(f"  {Colors.YELLOW}!{Colors.END} {message}")

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def check_python() -> bool:
    """Verify Python 3.8+ is installed."""
    print_section("1. Python Verification")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        check_pass(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        check_fail(f"Python {version.major}.{version.minor} (need 3.8+)")
        return False

def check_dependencies() -> bool:
    """Check if required packages are installed."""
    print_section("2. Dependencies Check")
    
    required_packages = {
        'livekit': 'LiveKit Python SDK',
        'livekit.agents': 'LiveKit Agents Framework',
        'livekit.plugins.google': 'Google Realtime API',
        'livekit.plugins.noise_cancellation': 'Noise Cancellation',
        'flask': 'Flask Web Framework',
        'firebase_admin': 'Firebase Admin SDK',
        'tensorflow': 'TensorFlow (ML)',
        'PIL': 'Pillow (Image Processing)',
        'dotenv': 'Python Dotenv',
    }
    
    all_ok = True
    for module, name in required_packages.items():
        try:
            __import__(module)
            check_pass(f"{name}")
        except ImportError:
            check_fail(f"{name} (import {module})")
            all_ok = False
    
    if not all_ok:
        check_warn("Run: pip install -r requirements.txt")
    
    return all_ok

def check_environment_file() -> Tuple[bool, dict]:
    """Check .env file exists and has required keys."""
    print_section("3. Environment Configuration")
    
    if not os.path.exists('.env'):
        check_fail(".env file not found")
        return False, {}
    
    check_pass(".env file exists")
    
    # Load .env
    env_vars = {}
    try:
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    except Exception as e:
        check_fail(f"Could not parse .env: {e}")
        return False, {}
    
    # Check required keys
    required_keys = {
        'LIVEKIT_URL': 'LiveKit Server URL',
        'LIVEKIT_API_KEY': 'LiveKit API Key',
        'LIVEKIT_API_SECRET': 'LiveKit API Secret',
        'LIVEKIT_AGENT_NAME': 'Agent Name',
    }
    
    all_ok = True
    for key, description in required_keys.items():
        if key in env_vars and env_vars[key]:
            value = env_vars[key]
            # Mask sensitive values
            if 'SECRET' in key or 'KEY' in key:
                value = value[:8] + '*' * max(0, len(value) - 12) + value[-4:]
            check_pass(f"{description}: {value}")
        else:
            check_fail(f"{description}: NOT SET")
            all_ok = False
    
    return all_ok, env_vars

def check_model_files() -> bool:
    """Check if ML model files exist."""
    print_section("4. Model Files")
    
    required_files = {
        'plant_model_v5-beta.h5': 'TensorFlow Disease Detection Model',
        'class_indices.json': 'Disease Class Labels',
    }
    
    all_ok = True
    for filename, description in required_files.items():
        if os.path.exists(filename):
            size_mb = os.path.getsize(filename) / (1024*1024)
            check_pass(f"{description} ({size_mb:.1f} MB)")
        else:
            check_fail(f"{description} - NOT FOUND: {filename}")
            all_ok = False
    
    return all_ok

def check_python_modules() -> bool:
    """Check if key GrowMate modules exist."""
    print_section("5. GrowMate Modules")
    
    required_modules = {
        'app.py': 'Flask Backend',
        'voice_agent.py': 'Voice Agent Worker',
        'disease_detection.py': 'Disease Detection',
        'firebase_service.py': 'Firebase Service',
        'extensions.py': 'Flask Extensions',
    }
    
    all_ok = True
    for filename, description in required_modules.items():
        if os.path.exists(filename):
            check_pass(f"{description}")
        else:
            check_fail(f"{description} - NOT FOUND: {filename}")
            all_ok = False
    
    return all_ok

def check_directories() -> bool:
    """Check if required directories exist."""
    print_section("6. Directory Structure")
    
    required_dirs = {
        'templates': 'HTML Templates',
        'static': 'Static Assets',
        'static/uploads': 'Upload Directory',
    }
    
    all_ok = True
    for dirname, description in required_dirs.items():
        if os.path.isdir(dirname):
            check_pass(f"{description}")
        else:
            check_fail(f"{description} - NOT FOUND: {dirname}")
            all_ok = False
    
    return all_ok

def check_voice_bot_template() -> bool:
    """Check if voicebot.html exists and is configured."""
    print_section("7. Voice Bot UI Template")
    
    if not os.path.exists('templates/voicebot.html'):
        check_fail("voicebot.html not found in templates/")
        return False
    
    check_pass("voicebot.html template exists")
    
    # Check for key features
    with open('templates/voicebot.html', 'r') as f:
        content = f.read()
        
        features = {
            'livekit': 'LiveKit JavaScript import',
            'fetchRoomDebug': 'Backend diagnostics',
            'Enable Audio': 'Audio unlock button',
            'language': 'Language selector',
        }
        
        for feature, description in features.items():
            if feature in content:
                check_pass(f"Has {description}")
            else:
                check_warn(f"Missing {description}")
    
    return True

def check_firebase_credentials() -> bool:
    """Check Firebase credentials."""
    print_section("8. Firebase Credentials")
    
    credential_files = [
        'aqro-f0322-firebase-adminsdk-fbsvc-f82124232c.json',
        'growmateaqro-firebase-adminsdk-fbsvc-51d86af04f.json',
    ]
    
    found = False
    for cred_file in credential_files:
        if os.path.exists(cred_file):
            check_pass(f"Firebase credentials: {cred_file}")
            found = True
            break
    
    if not found:
        check_warn("No Firebase credential files found (may be via env vars)")
    
    return True

def check_database_module() -> bool:
    """Check database initialization."""
    print_section("9. Database Module")
    
    if os.path.exists('database_init.py'):
        check_pass("Database initialization module exists")
    else:
        check_warn("database_init.py not found (optional)")
    
    if os.path.exists('instance/'):
        check_pass("Instance directory for Flask app context exists")
    else:
        check_warn("instance/ directory not found (optional)")
    
    return True

def check_port_availability(port: int) -> bool:
    """Check if a port is available."""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result != 0

def check_ports() -> bool:
    """Check if required ports are available."""
    print_section("10. Port Availability")
    
    ports = {
        5000: 'Flask Backend',
        8081: 'Voice Agent Worker',
    }
    
    all_ok = True
    for port, service in ports.items():
        if check_port_availability(port):
            check_pass(f"Port {port} available ({service})")
        else:
            check_fail(f"Port {port} in use ({service})")
            all_ok = False
    
    return all_ok

def print_summary(results: dict) -> bool:
    """Print validation summary."""
    print_section("Validation Summary")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    print(f"  Total Checks: {total}")
    print(f"  {Colors.GREEN}Passed: {passed}{Colors.END}")
    if failed > 0:
        print(f"  {Colors.RED}Failed: {failed}{Colors.END}")
    
    if failed == 0:
        print(f"\n{Colors.GREEN}✓ All checks passed! Ready to run.{Colors.END}")
        print(f"\nNext steps:")
        print(f"  1. Run Flask: python app.py")
        print(f"  2. Run Agent: python voice_agent.py")
        print(f"  3. Open: http://localhost:5000/voicebot")
        print()
        return True
    else:
        print(f"\n{Colors.RED}✗ Some checks failed. See above for details.{Colors.END}")
        print()
        return False

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run all validation checks."""
    print_header()
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    results = {}
    
    # Run checks
    results['Python'] = check_python()
    results['Dependencies'] = check_dependencies()
    results['Environment'] = check_environment_file()[0]
    results['Model Files'] = check_model_files()
    results['Python Modules'] = check_python_modules()
    results['Directories'] = check_directories()
    results['Voice Bot UI'] = check_voice_bot_template()
    results['Firebase'] = check_firebase_credentials()
    results['Database'] = check_database_module()
    results['Ports'] = check_ports()
    
    # Print summary
    all_pass = print_summary(results)
    
    return 0 if all_pass else 1

if __name__ == '__main__':
    sys.exit(main())
