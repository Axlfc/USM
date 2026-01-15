# Unified Stack Manager

Unified Stack Manager is a versatile command-line tool designed to streamline the setup and management of local development environments. It provides specialized managers for both Windows (WAMP) and Linux (LAMP) stacks, with a future-proof architecture aimed at unifying a shared core.

This tool is ideal for developers and system administrators who need to rapidly provision, configure, and manage web servers for applications like Drupal, WordPress, or other PHP-based projects.

## Project Structure

The project is organized into two main components:

-   `lamp_manager/`: A modern, robust manager for Debian-based Linux systems (Ubuntu, Debian).
-   `wamp_manager/`: The legacy manager for Windows environments.

The long-term vision is to merge the common logic into a shared `core/` directory, providing a single, cross-platform interface.

---

## LAMP Manager (Linux)

The **LAMP Manager** is a powerful and safe tool for automating the installation and configuration of a LAMP (Linux, Apache, MySQL, PHP) stack on Debian-based systems. It is designed with production-ready features like robust validation, atomic operations with rollbacks, and a mandatory dry-run mode.

### Features

-   **Full Stack Installation**: Installs Apache, MySQL/MariaDB, and multiple PHP versions.
-   **Multi-PHP Support**: Leverages the `ppa:ondrej/php` repository to install a wide range of PHP versions.
-   **Automated Site Creation**: Creates Apache virtual hosts, document root directories, and MySQL databases/users with a single command.
-   **Secure by Default**: Automatically generates strong, random passwords for database users.
-   **Safety First**:
    -   **Pre-execution Validation**: Checks for root permissions, disk space, and internet connectivity.
    -   **Dry-Run Mode**: Preview all changes before they are made.
    -   **User Confirmation**: Requires explicit user approval for all system-modifying operations.
    -   **Atomic Operations**: Uses a rollback manager to revert file changes if an operation fails, preventing inconsistent states.
-   **Configuration Driven**: Uses a central YAML file for configuration to avoid hardcoded values.
-   **Audit Logging**: Logs all actions for traceability and compliance.

### Requirements

-   **Operating System**: Debian-based Linux (e.g., Ubuntu 22.04 LTS).
-   **Permissions**: `sudo` / root access.
-   **Python**: Python 3.8+
-   **Dependencies**: `PyYAML`

### Usage Instructions

#### 1. Setup

First, install the required Python dependency.

```bash
# Navigate to the repository root
sudo pip install -r requirements.txt
```

#### 2. Test Stack Installation (`--install-stack`)

This command provisions the complete LAMP stack.

**A. Perform a Dry Run (Recommended First)**

A dry run will show you what the script *would* do without making any actual changes to your system.

```bash
# Execute a dry run to install the stack with PHP 8.2
sudo python3 lamp_manager/cli.py --install-stack 8.2 --dry-run
```

**B. Execute the Real Installation**

Run the command without the `--dry-run` flag to begin the installation.

```bash
# Install the full LAMP stack with PHP 8.2
sudo python3 lamp_manager/cli.py --install-stack 8.2
```

The script will ask for confirmation before proceeding. After you type `y`, it will begin installing packages.

#### 3. Test Site Creation (`--create-site`)

This command automates the creation of a new website.

**A. Perform a Dry Run**

```bash
# Dry run for creating a site named 'test.local' with PHP 8.2
sudo python3 lamp_manager/cli.py --create-site test.local 8.2 --dry-run
```

This will show you the plan, including the database name and document root that will be created.

**B. Execute the Real Site Creation**

```bash
# Create the 'test.local' site with PHP 8.2
sudo python3 lamp_manager/cli.py --create-site test.local 8.2
```

If the operation is successful, the script will print the **database credentials** (database name, username, and the randomly generated password) to the console. **Make sure to save this password!**

#### 4. Verification

You can verify the installation and site creation with the following commands:

```bash
# Check Apache and MySQL status
systemctl is-active apache2
systemctl is-active mysql

# Check for the Apache virtual host file
ls /etc/apache2/sites-available/test.local.conf

# Check that the site was enabled
ls /etc/apache2/sites-enabled/test.local.conf

# Check for the document root directory
ls -l /var/www/test.local
```

---

## WAMP Manager (Legacy)

The legacy WAMP Manager provides a set of scripts for managing a WAMP (Windows, Apache, MySQL, PHP) environment.

*Note: This section preserves the original documentation for the legacy WAMP tool.*

### Show Help

```powershell
.\PythonFiles\.venv\Scripts\python .\wamp_manager\php_manager.py --help
```

### List Versions

```powershell
.\PythonFiles\.venv\Scripts\python .\wamp_manager\php_manager.py -l
```

### Install PHP

```powershell
.\PythonFiles\.venv\Scripts\python .\wamp_manager\php_manager.py --install -v 8.3
```

### Change CLI Version

```powershell
.\PythonFiles\.venv\Scripts\python .\wamp_manager\php_manager.py -v 8.3
```
