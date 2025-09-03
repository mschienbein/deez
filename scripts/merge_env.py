#!/usr/bin/env python3
"""
Merge .env.example into .env, preserving existing values
"""

import os
from pathlib import Path

def parse_env_file(filepath):
    """Parse an env file and return a dict of key-value pairs"""
    env_vars = {}
    lines = []
    
    if not os.path.exists(filepath):
        return env_vars, lines
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        # Skip comments and empty lines for parsing
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            # Handle key=value pairs
            if '=' in stripped:
                key, value = stripped.split('=', 1)
                env_vars[key.strip()] = value.strip().strip('"')
    
    return env_vars, lines


def merge_env_files(env_path, example_path):
    """Merge .env.example into .env, keeping existing values"""
    
    # Parse both files
    env_vars, env_lines = parse_env_file(env_path)
    example_vars, example_lines = parse_env_file(example_path)
    
    # Find missing variables
    missing_vars = {}
    for key, value in example_vars.items():
        if key not in env_vars:
            missing_vars[key] = value
    
    if not missing_vars:
        print("✅ All variables from .env.example are already in .env")
        return
    
    print(f"Found {len(missing_vars)} missing variables to add:")
    for key in missing_vars:
        print(f"  - {key}")
    
    # Append missing variables to .env
    with open(env_path, 'a') as f:
        f.write("\n# ====================================\n")
        f.write("# Added from .env.example\n")
        f.write("# ====================================\n\n")
        
        # Group related variables
        groups = {
            "Neo4j": ["NEO4J_"],
            "PostgreSQL": ["POSTGRES_"],
            "Redis": ["REDIS_"],
            "MinIO": ["MINIO_"],
            "Soulseek": ["SLSKD_", "SOULSEEK_"],
            "Rekordbox": ["REKORDBOX_"],
            "Beatport": ["BEATPORT_"],
            "Discogs": ["DISCOGS_"],
            "Other": []
        }
        
        grouped_vars = {group: [] for group in groups}
        
        for key, value in sorted(missing_vars.items()):
            assigned = False
            for group, prefixes in groups.items():
                if group != "Other":
                    for prefix in prefixes:
                        if key.startswith(prefix):
                            grouped_vars[group].append((key, value))
                            assigned = True
                            break
                    if assigned:
                        break
            if not assigned:
                grouped_vars["Other"].append((key, value))
        
        # Write grouped variables
        for group, vars in grouped_vars.items():
            if vars:
                f.write(f"# {group} Configuration\n")
                for key, value in vars:
                    # Use placeholder values for sensitive data
                    if "PASSWORD" in key or "SECRET" in key or "TOKEN" in key or "API_KEY" in key:
                        if key == "SLSKD_API_KEY":
                            value = "deez-slskd-api-key-2024"
                        elif key == "SLSKD_USERNAME":
                            value = "deezmusic"
                        elif key == "SLSKD_PASSWORD":
                            value = "deezmusic123"
                        elif key == "SOULSEEK_USERNAME":
                            value = "your_soulseek_username_here"
                        elif key == "SOULSEEK_PASSWORD":
                            value = "your_soulseek_password_here"
                        else:
                            value = value  # Keep example value
                    f.write(f'{key}="{value}"\n')
                f.write("\n")
    
    print(f"\n✅ Added {len(missing_vars)} variables to {env_path}")
    print("\n⚠️  Please update the following variables with your actual values:")
    print("  - SOULSEEK_USERNAME")
    print("  - SOULSEEK_PASSWORD")


def main():
    """Main function"""
    project_root = Path(__file__).parent.parent
    env_path = project_root / ".env"
    example_path = project_root / ".env.example"
    
    print("=" * 60)
    print("Merging .env.example into .env")
    print("=" * 60)
    
    if not example_path.exists():
        print(f"❌ {example_path} not found")
        return 1
    
    if not env_path.exists():
        print(f"❌ {env_path} not found")
        print(f"Creating new .env from .env.example...")
        with open(example_path, 'r') as src, open(env_path, 'w') as dst:
            dst.write(src.read())
        print(f"✅ Created {env_path}")
        return 0
    
    merge_env_files(env_path, example_path)
    return 0


if __name__ == "__main__":
    exit(main())