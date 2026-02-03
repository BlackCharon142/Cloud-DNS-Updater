#!/usr/bin/env python3
import os
import sys
import subprocess

def parse_env_list(env_var_name: str, default: str = '') -> str:
    """Parse environment variable list, converting empty string to default"""
    value = os.getenv(env_var_name, '').strip()
    if not value and default:
        return default
    return value

def main():
    # Required parameters
    required_params = {
        'PROVIDER': os.getenv('PROVIDER'),
        'API_KEY': os.getenv('API_KEY'),
        'DOMAIN': os.getenv('DOMAIN'),
        'RECORDS': os.getenv('RECORDS')
    }
    
    # Check for missing required parameters
    missing = [param for param, value in required_params.items() if not value]
    if missing:
        print(f"Error: Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)
    
    # Build command
    cmd = [
        "python", "main.py",
        "--provider", required_params['PROVIDER'],
        "--key", required_params['API_KEY'],
        "--domain", required_params['DOMAIN'],
        "--records", required_params['RECORDS']
    ]
    
    # IP version configuration
    ip_version = os.getenv('IP_VERSION', '4').strip()
    if ip_version == '6':
        cmd.append('--ipv6')
    elif ip_version == 'dual':
        cmd.append('--dual-stack')
    else:
        cmd.append('--ipv4')
    
    # IP source configuration
    if sources := parse_env_list('SOURCES', 'all'):
        cmd.extend(['--sources', sources])
    
    if exclude_sources := parse_env_list('EXCLUDE_SOURCES'):
        cmd.extend(['--exclude-sources', exclude_sources])
    
    if source_timeout := os.getenv('SOURCE_TIMEOUT'):
        cmd.extend(['--source-timeout', source_timeout])
    
    # Timing configuration
    if interval := os.getenv('INTERVAL'):
        cmd.extend(['--interval', interval])
    
    if timeout := os.getenv('TIMEOUT'):
        cmd.extend(['--timeout', timeout])
    
    # Mode flags
    if os.getenv('VALIDATE_ONLY', 'false').lower() in ('true', '1', 'yes'):
        cmd.append('--validate-only')
    
    if os.getenv('LIST_SOURCES', 'false').lower() in ('true', '1', 'yes'):
        cmd.append('--list-sources')
    
    # Execute command
    try:
        result = subprocess.run(cmd, check=True)
        sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        print(f"Command: {' '.join(cmd)}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()