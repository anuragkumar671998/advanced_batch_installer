#!/usr/bin/env python3
"""
Advanced Background Batch App Installer
Automatically runs in background - installs/uninstalls random apps in batches
Total: 161-199 apps, Batch size: 5-14 apps, Delay: 7-16 minutes
"""

import subprocess
import random
import time
import sys
import os
import logging
import atexit
import signal
import threading
from datetime import datetime
from pathlib import Path

# Global flag for graceful shutdown
shutdown_flag = False
pid_file = "/tmp/background_batch_installer.pid"
log_file = "/tmp/background_batch_installer.log"

def daemonize():
    """Turn the script into a daemon that runs in background"""
    try:
        # First fork
        pid = os.fork()
        if pid > 0:
            # Parent exits
            sys.exit(0)
    except OSError as e:
        sys.stderr.write(f"First fork failed: {e}\n")
        sys.exit(1)
    
    # Decouple from parent environment
    os.chdir('/')
    os.setsid()
    os.umask(0)
    
    # Second fork
    try:
        pid = os.fork()
        if pid > 0:
            # Parent exits
            sys.exit(0)
    except OSError as e:
        sys.stderr.write(f"Second fork failed: {e}\n")
        sys.exit(1)
    
    # Redirect standard file descriptors to /dev/null
    sys.stdout.flush()
    sys.stderr.flush()
    
    # Write PID file
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))
    
    # Register cleanup
    atexit.register(cleanup_pid_file)
    
    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_flag
    logger = logging.getLogger(__name__)
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_flag = True

def cleanup_pid_file():
    """Remove PID file on exit"""
    if os.path.exists(pid_file):
        os.remove(pid_file)

def check_existing_process():
    """Check if another instance is already running"""
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process is still running
            try:
                os.kill(pid, 0)
                print(f"Another instance is already running (PID: {pid})")
                print(f"Check log file: {log_file}")
                print("If not running, remove: " + pid_file)
                return True
            except OSError:
                # Process not running, remove stale PID file
                os.remove(pid_file)
                return False
        except:
            # Corrupted PID file
            os.remove(pid_file)
            return False
    return False

def setup_logging():
    """Setup logging for background process"""
    # Create log directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
        ]
    )
    return logging.getLogger(__name__)

# Extended list of useful applications (200+ apps)
ALL_USEFUL_APPS = [
    # System Tools & Monitoring
    'htop', 'neofetch', 'btop', 'glances', 'nmon', 'bashtop',
    'ncdu', 'ranger', 'mc', 'tree', 'fdupes', 'dust', 'duf',
    'inxi', 'hardinfo', 'lshw', 'screenfetch',
    
    # Package Management
    'aptitude', 'synaptic', 'gdebi', 'snapd', 'flatpak',
    
    # Terminal & Shell
    'zsh', 'fish', 'powerline', 'fonts-powerline',
    'terminator', 'guake', 'tilix', 'alacritty', 'kitty',
    'tmux', 'byobu', 'screen', 'expect',
    
    # Text Editors & IDEs
    'vim', 'neovim', 'emacs', 'nano', 'micro', 'gedit',
    'code', 'geany', 'bluefish',
    
    # File Management
    'rsync', 'unzip', 'p7zip-full', 'rar', 'unar',
    'filezilla', 'lftp', 'sshfs', 'curlftpfs',
    'ntfs-3g', 'exfat-utils', 'hfsprogs',
    
    # Network Tools
    'nmap', 'wireshark', 'tcpdump', 'net-tools', 'netcat',
    'socat', 'nethogs', 'iftop', 'bmon', 'vnstat',
    'iperf3', 'speedtest-cli', 'openssh-server', 'mosh',
    'wireguard-tools', 'openvpn',
    
    # Development Tools
    'build-essential', 'cmake', 'autoconf', 'automake',
    'libtool', 'pkg-config', 'checkinstall',
    'gcc', 'g++', 'clang', 'gdb', 'valgrind',
    'python3', 'python3-pip', 'python3-venv', 'python3-dev',
    'python-is-python3', 'nodejs', 'npm',
    'default-jdk', 'openjdk-17-jdk', 'ruby', 'perl',
    'php', 'golang', 'rustc', 'cargo',
    'git', 'gitk', 'tig', 'subversion',
    
    # Web Servers & Databases
    'apache2', 'nginx', 'mysql-server', 'postgresql',
    'sqlite3', 'sqlitebrowser', 'redis-server',
    'mariadb-server', 'phpmyadmin',
    
    # Cloud & DevOps
    'docker.io', 'docker-compose', 'ansible', 'terraform',
    'awscli', 'azure-cli', 'kubernetes-client',
    
    # Graphics & Design
    'gimp', 'inkscape', 'krita', 'blender', 'darktable',
    'rawtherapee', 'digikam', 'shotwell',
    
    # Multimedia
    'vlc', 'ffmpeg', 'handbrake', 'audacity',
    'obs-studio', 'kdenlive', 'openshot', 'shotcut',
    'mpv', 'clementine', 'rhythmbox', 'strawberry',
    
    # Office & Productivity
    'libreoffice', 'thunderbird', 'evolution',
    'evince', 'okular', 'calibre', 'fcitx', 'ibus',
    
    # Security
    'fail2ban', 'clamav', 'clamtk', 'rkhunter',
    'chkrootkit', 'lynis', 'ufw', 'gufw',
    'keepassxc', 'gnupg', 'seahorse',
    
    # Science & Education
    'octave', 'scilab', 'maxima', 'geogebra',
    'stellarium', 'atomix',
    
    # Games & Entertainment
    'steam', 'lutris', 'wine', 'dosbox', 'mame',
    'retroarch', 'minetest', 'supertuxkart',
    
    # Virtualization
    'virtualbox', 'qemu-kvm', 'libvirt-daemon-system',
    'virt-manager', 'gnome-boxes',
    
    # System Administration
    'cron', 'logwatch', 'rsyslog', 'smartmontools',
    'testdisk', 'gparted', 'baobab',
    
    # Hardware
    'hwinfo', 'dmidecode', 'mesa-utils', 'vulkan-tools',
    'stress', 'stress-ng',
    
    # Fun & Miscellaneous
    'cmatrix', 'figlet', 'lolcat', 'cowsay',
    'fortune', 'sl', 'bb', 'hollywood',
    'pipes.sh', 'tty-clock',
    
    # Browsers
    'firefox', 'chromium-browser', 'opera',
    'epiphany-browser', 'falkon',
    
    # Communication
    'discord', 'slack', 'telegram-desktop',
    'signal-desktop', 'pidgin', 'hexchat',
    
    # File Sharing & Sync
    'transmission', 'qbittorrent', 'deluge',
    'dropbox', 'nextcloud-client', 'syncthing',
    
    # System Cleanup
    'bleachbit', 'stacer', 'ubuntu-cleaner',
    
    # Additional useful packages
    'man-db', 'manpages', 'manpages-dev',
    'info', 'texinfo', 'bash-completion',
    'command-not-found', 'software-properties-common',
    'ubuntu-drivers-common', 'pptp-linux',
    'network-manager-pptp', 'mtr', 'hdparm',
    'lm-sensors', 'psensor', 'conky', 'variety',
    'shutter', 'kazam', 'cheese', 'gtk-recordmydesktop',
    'x11vnc', 'vinagre', 'remmina', 'freerdp2-x11',
    'guvcview', 'arc-theme', 'papirus-icon-theme',
    'fonts-firacode', 'fonts-hack', 'fonts-noto',
    'fonts-liberation', 'fonts-dejavu', 'fonts-ubuntu',
    'fonts-roboto', 'ttf-mscorefonts-installer'
]

def update_system(logger):
    """Update system packages"""
    logger.info("Updating system packages...")
    try:
        result = subprocess.run(
            ['apt', 'update'],
            timeout=300,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            logger.info("System updated successfully")
            return True
        else:
            logger.warning(f"Update had issues: {result.stderr[:200]}")
            return True  # Continue anyway
    except subprocess.TimeoutExpired:
        logger.error("Update timed out")
        return False
    except Exception as e:
        logger.error(f"Update error: {e}")
        return False

def install_batch(apps_list, batch_num, total_batches, logger):
    """Install a batch of apps"""
    logger.info(f"Installing batch {batch_num}/{total_batches}: {len(apps_list)} apps")
    
    try:
        # Install all apps in batch
        result = subprocess.run(
            ['apt', 'install', '-y'] + apps_list,
            timeout=900,  # 15 minute timeout
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info(f"✓ Batch {batch_num} installed successfully")
            return True
        else:
            logger.warning(f"⚠ Batch {batch_num} installation had issues")
            
            # Try installing individually
            success_count = 0
            for app in apps_list:
                try:
                    app_result = subprocess.run(
                        ['apt', 'install', '-y', app],
                        timeout=300,
                        capture_output=True,
                        text=True
                    )
                    if app_result.returncode == 0:
                        success_count += 1
                    else:
                        logger.warning(f"  ✗ Failed to install {app}")
                except:
                    logger.warning(f"  ✗ Timeout installing {app}")
            
            logger.info(f"  Individual installs: {success_count}/{len(apps_list)} successful")
            return success_count > 0
            
    except subprocess.TimeoutExpired:
        logger.error(f"✗ Batch {batch_num} installation timed out")
        return False
    except Exception as e:
        logger.error(f"✗ Batch {batch_num} error: {e}")
        return False

def uninstall_batch(apps_list, batch_num, total_batches, logger):
    """Uninstall a batch of apps"""
    logger.info(f"Uninstalling batch {batch_num}/{total_batches}: {len(apps_list)} apps")
    
    try:
        # Uninstall all apps in batch
        result = subprocess.run(
            ['apt', 'remove', '-y'] + apps_list,
            timeout=600,  # 10 minute timeout
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info(f"✓ Batch {batch_num} uninstalled successfully")
            return True
        else:
            logger.warning(f"⚠ Batch {batch_num} uninstallation had issues")
            
            # Try uninstalling individually
            for app in apps_list:
                subprocess.run(
                    ['apt', 'remove', '-y', app],
                    timeout=180,
                    capture_output=True
                )
            return True
            
    except subprocess.TimeoutExpired:
        logger.error(f"✗ Batch {batch_num} uninstallation timed out")
        return False
    except Exception as e:
        logger.error(f"✗ Batch {batch_num} uninstall error: {e}")
        return False

def cleanup_system(logger):
    """Clean up system after operations"""
    logger.info("Performing system cleanup...")
    
    try:
        subprocess.run(
            ['apt', 'autoremove', '-y'],
            timeout=300,
            capture_output=True
        )
        subprocess.run(
            ['apt', 'autoclean'],
            timeout=180,
            capture_output=True
        )
        logger.info("System cleanup completed")
    except:
        logger.warning("Cleanup had issues")

def show_status():
    """Show current status if running"""
    if os.path.exists(log_file):
        print(f"Log file: {log_file}")
        print("\nLast 10 lines of log:")
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()[-10:]
                for line in lines:
                    print(line.strip())
        except:
            print("Could not read log file")
        
        print(f"\nPID file: {pid_file}")
        if os.path.exists(pid_file):
            try:
                with open(pid_file, 'r') as f:
                    pid = f.read().strip()
                    print(f"Process ID: {pid}")
            except:
                print("Could not read PID file")

def stop_process():
    """Stop the running background process"""
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Send SIGTERM signal
            os.kill(pid, signal.SIGTERM)
            print(f"Sent stop signal to process {pid}")
            time.sleep(2)
            
            # Check if process is still running
            try:
                os.kill(pid, 0)
                print("Process still running, sending SIGKILL...")
                os.kill(pid, signal.SIGKILL)
            except OSError:
                print("Process stopped successfully")
            
            # Clean up PID file
            if os.path.exists(pid_file):
                os.remove(pid_file)
            
        except ValueError:
            print("Invalid PID file")
            if os.path.exists(pid_file):
                os.remove(pid_file)
        except OSError as e:
            print(f"Error stopping process: {e}")
            if os.path.exists(pid_file):
                os.remove(pid_file)
    else:
        print("No process is running")

def main_installation():
    """Main installation process - runs in background"""
    global shutdown_flag
    
    # Setup logging
    logger = setup_logging()
    
    logger.info("="*60)
    logger.info("BACKGROUND BATCH APP INSTALLER STARTED")
    logger.info(f"Start time: {datetime.now()}")
    logger.info("="*60)
    
    # Update system first
    if not update_system(logger):
        logger.warning("System update failed, continuing anyway...")
    
    # Total number of apps to install/uninstall (161-199)
    total_apps = random.randint(161, 199)
    logger.info(f"Total apps to process: {total_apps}")
    
    # Process apps in batches
    processed_apps = 0
    batch_number = 0
    
    while processed_apps < total_apps and not shutdown_flag:
        batch_number += 1
        
        # Check for shutdown flag
        if shutdown_flag:
            logger.info("Shutdown requested, stopping after current batch...")
            break
        
        # Determine batch size (5-14 apps)
        batch_size = random.randint(5, 14)
        
        # Adjust last batch size if needed
        if processed_apps + batch_size > total_apps:
            batch_size = total_apps - processed_apps
        
        # Select random apps for this batch
        batch_apps = random.sample(ALL_USEFUL_APPS, min(batch_size, len(ALL_USEFUL_APPS)))
        
        logger.info(f"\n{'='*50}")
        logger.info(f"Starting batch {batch_number}")
        logger.info(f"Batch size: {batch_size} apps")
        logger.info(f"Progress: {processed_apps}/{total_apps} apps")
        logger.info(f"Selected apps: {', '.join(batch_apps)}")
        
        # Install the batch
        if install_batch(batch_apps, batch_number, "unknown", logger):
            logger.info(f"✓ Installation of batch {batch_number} completed")
        else:
            logger.warning(f"⚠ Installation of batch {batch_number} had issues")
        
        # Check for shutdown before delay
        if shutdown_flag:
            logger.info("Shutdown requested, stopping...")
            break
        
        # Random delay between 7-16 minutes
        delay_minutes = random.randint(7, 16)
        delay_seconds = delay_minutes * 60 + random.randint(0, 59)
        logger.info(f"Waiting {delay_minutes} minutes before uninstalling...")
        
        # Break delay into smaller chunks to check shutdown flag
        for _ in range(delay_seconds // 10):
            if shutdown_flag:
                break
            time.sleep(10)
        
        if shutdown_flag:
            logger.info("Shutdown requested, stopping...")
            break
        
        # Uninstall the batch
        if uninstall_batch(batch_apps, batch_number, "unknown", logger):
            logger.info(f"✓ Uninstallation of batch {batch_number} completed")
        else:
            logger.warning(f"⚠ Uninstallation of batch {batch_number} had issues")
        
        # Update processed count
        processed_apps += batch_size
        
        # Random delay before next batch (1-3 minutes)
        if processed_apps < total_apps and not shutdown_flag:
            next_delay = random.randint(60, 180)
            logger.info(f"Waiting {next_delay//60} minutes before next batch...")
            
            for _ in range(next_delay // 10):
                if shutdown_flag:
                    break
                time.sleep(10)
        
        # Occasional cleanup
        if batch_number % 5 == 0 and not shutdown_flag:
            cleanup_system(logger)
    
    # Final cleanup
    logger.info("\n" + "="*50)
    if shutdown_flag:
        logger.info("PROCESS STOPPED BY USER")
    else:
        logger.info("ALL BATCHES COMPLETED!")
    
    logger.info(f"Total batches processed: {batch_number}")
    logger.info(f"Total apps installed/uninstalled: {processed_apps}")
    
    cleanup_system(logger)
    
    if shutdown_flag:
        logger.info("Process stopped gracefully")
    else:
        logger.info("Process completed successfully!")
    
    logger.info(f"End time: {datetime.now()}")
    logger.info("="*60)

def show_summary():
    """Show summary of what will happen"""
    print("\n" + "="*60)
    print("BACKGROUND BATCH APP INSTALLER")
    print("="*60)
    print("This script will run in the background and:")
    print(f"1. Install 161-199 random useful apps")
    print("2. Process apps in batches of 5-14 apps")
    print("3. For each batch:")
    print("   - Install the batch")
    print("   - Wait 7-16 minutes")
    print("   - Uninstall the batch")
    print("4. Continue until all apps are processed")
    print("\nEstimated time: 1.5 to 10.5 hours")
    print(f"Log file: {log_file}")
    print(f"PID file: {pid_file}")
    print("="*60)
    print("\nCommands:")
    print(f"  Status:  {sys.argv[0]} status")
    print(f"  Stop:    {sys.argv[0]} stop")
    print(f"  Start:   {sys.argv[0]} start")
    print("="*60 + "\n")

def show_banner():
    """Show application banner"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║     BACKGROUND BATCH APP INSTALLER - UBUNTU 24.04 LTS        ║
║          Auto-run in background • Safe • Efficient           ║
╚══════════════════════════════════════════════════════════════╝
""")

if __name__ == "__main__":
    # Show banner
    show_banner()
    
    # Check arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "start":
            # Check if already running
            if check_existing_process():
                sys.exit(1)
            
            # Show summary
            show_summary()
            
            # Confirm
            response = input("Start in background? (yes/NO): ").strip().lower()
            if response != 'yes':
                print("Cancelled.")
                sys.exit(0)
            
            print("\nStarting in background...")
            print(f"Check status: {sys.argv[0]} status")
            print(f"Stop: {sys.argv[0]} stop")
            
            # Daemonize and start installation
            daemonize()
            main_installation()
            
        elif command == "stop":
            print("Stopping background process...")
            stop_process()
            
        elif command == "status":
            if os.path.exists(pid_file):
                print("Background process is RUNNING")
            else:
                print("Background process is NOT running")
            show_status()
            
        elif command == "help" or command == "--help" or command == "-h":
            show_summary()
            
        else:
            print(f"Unknown command: {command}")
            print(f"Usage: {sys.argv[0]} [start|stop|status|help]")
            sys.exit(1)
            
    else:
        # No arguments - show help
        show_summary()
        print("To start: sudo python3 " + sys.argv[0] + " start")
