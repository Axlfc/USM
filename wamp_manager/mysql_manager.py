#!/usr/bin/env python3
"""
MySQL Manager - Fully Automated Version
Configures MySQL server and creates databases/users for different services
Handles MySQL 8.4 compatibility issues automatically
"""
import argparse
import os
import sys
import subprocess
import time
import json
import urllib.request
import zipfile
import shutil
from pathlib import Path
import getpass


class MySQLManager:
    def __init__(self, mysql_path="C:/mysql", root_password=None):
        self.mysql_path = Path(mysql_path)
        self.bin_path = self.mysql_path / "bin"
        self.data_path = self.mysql_path / "data"
        self.tmp_path = self.mysql_path / "tmp"
        self.root_password = root_password
        self.mysql_url = "https://dev.mysql.com/get/Downloads/MySQL-8.4/mysql-8.4.6-winx64.zip"
        # self.mysql_url = "https://dev.mysql.com/get/Downloads/MySQL-8.0/mysql-8.0.40-winx64.zip"  # mysql 8.0 test
        # self.mysql_url = "https://dev.mysql.com/get/Downloads/MySQL-5.7/mysql-5.7.44-winx64.zip"  # mysql 5.7 test

        # Predefined service configurations
        self.service_configs = {
            "drupal": {
                "database": "drupal_db",
                "username": "drupal_user",
                "password": "drupal_pass_123",
                "description": "Drupal CMS Database"
            },
            "phpmyadmin": {
                "database": "phpmyadmin_db",
                "username": "pma_user",
                "password": "pma_pass_123",
                "description": "phpMyAdmin Database"
            },
            "wordpress": {
                "database": "wordpress_db",
                "username": "wp_user",
                "password": "wp_pass_123",
                "description": "WordPress Database"
            },
            "testapp": {
                "database": "testdb",
                "username": "testuser",
                "password": "testpass",
                "description": "Test Application Database"
            }
        }

    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def is_mysql_running(self):
        """Check if MySQL server is already running"""
        try:
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq mysqld.exe"],
                capture_output=True,
                text=True
            )
            return "mysqld.exe" in result.stdout
        except:
            return False

    def stop_mysql_server(self):
        """Stop MySQL server if running"""
        if not self.is_mysql_running():
            self.log("ℹ️ MySQL server is not running")
            return True

        self.log("⏹️ Stopping MySQL server...")
        try:
            subprocess.run(["taskkill", "/F", "/IM", "mysqld.exe"],
                           capture_output=True, check=False)
            time.sleep(3)

            if not self.is_mysql_running():
                self.log("✅ MySQL server stopped")
                return True
            else:
                self.log("⚠️ MySQL server may still be running", "WARNING")
                return False
        except Exception as e:
            self.log(f"❌ Failed to stop MySQL: {e}", "ERROR")
            return False

    def create_directories(self):
        """Create necessary directories: C:/mysql, bin, data, tmp"""
        directories = [self.mysql_path, self.data_path, self.tmp_path]

        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                self.log(f"✅ Directory created/verified: {directory}")
            except Exception as e:
                self.log(f"❌ Failed to create directory {directory}: {e}", "ERROR")
                return False
        return True

    def download_mysql(self):
        """Download and extract MySQL if bin/mysqld.exe does not exist"""
        mysqld_exe = self.bin_path / "mysqld.exe"
        if mysqld_exe.exists():
            self.log(f"✅ mysqld.exe already exists: {mysqld_exe}")
            return True

        self.log("⬇️ Downloading MySQL...")

        temp_dir = Path("temp_mysql_download")
        temp_dir.mkdir(exist_ok=True)
        zip_path = temp_dir / "mysql.zip"

        try:
            self.log(f"📥 Downloading from: {self.mysql_url}")
            urllib.request.urlretrieve(self.mysql_url, zip_path)
            self.log("✅ Download completed")

            self.log("📦 Extracting MySQL archive...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            extracted_folders = [d for d in temp_dir.iterdir() if
                                 d.is_dir() and d.name.startswith("mysql-") and "winx64" in d.name]
            if not extracted_folders:
                self.log("❌ No valid MySQL folder found in ZIP", "ERROR")
                shutil.rmtree(temp_dir)
                return False

            source_dir = extracted_folders[0]
            self.log(f"📁 Found MySQL source: {source_dir}")

            for item in os.listdir(source_dir):
                src = source_dir / item
                dst = self.mysql_path / item
                if src.is_dir():
                    if not dst.exists():
                        shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)

            self.log("✅ MySQL files copied to C:/mysql")

            if not mysqld_exe.exists():
                self.log("❌ mysqld.exe not found after extraction!", "ERROR")
                return False

            shutil.rmtree(temp_dir)
            self.log("🧹 Temporary files cleaned up")
            return True

        except Exception as e:
            self.log(f"❌ Failed to download/extract MySQL: {e}", "ERROR")
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            return False

    def create_config_file(self):
        """Create my.ini configuration file with version-appropriate settings"""
        basedir = self.mysql_path.as_posix()
        datadir = self.data_path.as_posix()
        tmpdir = self.tmp_path.as_posix()

        mysql_version = self.detect_mysql_version()
        self.log(f"📝 Creating config for MySQL {mysql_version}")

        # Common base configuration
        config_content = f"""[mysqld]
    basedir={basedir}
    datadir={datadir}
    tmpdir={tmpdir}
    port=3306

    # Logging
    log-error={datadir}/mysqld.log

    # Connection settings
    max_connections=100
    max_allowed_packet=16M

    # InnoDB
    innodb_buffer_pool_size=128M
    innodb_strict_mode=0
    innodb_flush_log_at_trx_commit=2

    # Character set
    character-set-server=utf8mb4
    collation-server=utf8mb4_general_ci

    # SQL Mode - relaxed for application compatibility
    sql_mode=NO_ENGINE_SUBSTITUTION
    """

        # Version-specific authentication settings
        if mysql_version == 5.7:
            self.log("   Using MySQL 5.7 configuration")
            # MySQL 5.7 uses mysql_native_password by default
            pass

        elif mysql_version == 8.0:
            self.log("   Using MySQL 8.0 configuration")
            config_content += """
    # MySQL 8.0 authentication
    default_authentication_plugin=mysql_native_password
    """

        elif mysql_version >= 8.4:
            self.log("   Using MySQL 8.4+ configuration")
            # In MySQL 8.4+, default_authentication_plugin was removed
            # Instead, we enable mysql_native_password plugin
            config_content += """
    # MySQL 8.4+ authentication
    # Note: mysql_native_password must be enabled explicitly in 8.4+
    mysql_native_password=ON
    """

        config_file = self.mysql_path / 'my.ini'
        try:
            config_file.write_text(config_content, encoding='utf-8')
            self.log(f"✅ Configuration file created: {config_file}")
            self.log(f"   Location: {config_file}")
            return True
        except Exception as e:
            self.log(f"❌ Failed to create config file: {e}", "ERROR")
            return False

    def detect_mysql_version(self):
        """Detect MySQL version from URL or installed binary"""
        # Check from download URL first
        if "5.7" in self.mysql_url:
            return 5.7
        elif "8.0" in self.mysql_url:
            return 8.0
        elif "8.4" in self.mysql_url:
            return 8.4

        # Try to detect from installed mysqld.exe
        mysqld_exe = self.bin_path / "mysqld.exe"
        if mysqld_exe.exists():
            try:
                result = subprocess.run(
                    [str(mysqld_exe), "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                version_output = result.stdout + result.stderr
                if "5.7" in version_output:
                    return 5.7
                elif "8.0" in version_output:
                    return 8.0
                elif "8.4" in version_output:
                    return 8.4
            except:
                pass

        # Default to 8.0 if can't detect
        return 8.0

    def check_mysql_dependencies(self):
        """Check for required Visual C++ redistributables"""
        self.log("🔍 Checking MySQL dependencies...")

        try:
            import ctypes
            try:
                ctypes.CDLL("vcruntime140.dll")
                self.log("✅ Visual C++ 2015-2019 runtime found")
            except OSError:
                self.log("⚠️  Visual C++ 2015-2019 runtime may be missing", "WARNING")
                self.log("💡 If initialization fails, install Microsoft Visual C++ 2015-2019 Redistributable")
        except:
            pass

        return True

    def initialize_mysql(self):
        """Initialize MySQL server using --initialize-insecure for reliability"""
        # Check if MySQL is running first
        if self.is_mysql_running():
            self.log("⚠️ MySQL is currently running. Stopping it first...", "WARNING")
            if not self.stop_mysql_server():
                self.log("❌ Cannot proceed with initialization while MySQL is running", "ERROR")
                return None
        if self.data_path.exists():
            self.log("🗑️ Removing existing data directory...")
            try:
                shutil.rmtree(self.data_path)
                time.sleep(2)
                self.log("✅ Existing data directory removed")
            except Exception as e:
                self.log(f"❌ Cannot remove old data: {e}", "ERROR")
                self.log("💡 Try running: taskkill /F /IM mysqld.exe", "INFO")
                return None
        self.data_path.mkdir(exist_ok=True)
        self.check_mysql_dependencies()
        self.log("🔧 Initializing MySQL data directory...")
        self.log("💡 Using --initialize-insecure (no temp password, safer for automation)")
        cmd = [
            str(self.bin_path / "mysqld.exe"),
            "--initialize-insecure",
            "--console",
            f"--basedir={self.mysql_path}",
            f"--datadir={self.data_path}"
        ]
        self.log(f"🔧 Running command: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.bin_path),
                timeout=120,
                encoding='utf-8',
                errors='replace'
            )
            self.log(f"📊 Exit code: {result.returncode}")
            if result.stderr:
                for line in result.stderr.split('\n'):
                    if line.strip():
                        self.log(f"   {line.strip()}", "ERROR" if "ERROR" in line else "INFO")
            if result.returncode == 0:
                self.log("✅ MySQL data directory initialized successfully")
                return ""  # Empty password initially
            else:
                self.log("❌ MySQL initialization failed", "ERROR")
                return None
        except Exception as e:
            self.log(f"❌ Failed to initialize MySQL: {e}", "ERROR")
            return None

    def start_mysql_server(self):
        """Start MySQL server in background with better error handling"""
        if self.is_mysql_running():
            self.log("✅ MySQL server is already running")
            return True

        self.log("🚀 Starting MySQL server...")

        config_file = self.mysql_path / 'my.ini'
        cmd = [
            str(self.bin_path / "mysqld.exe"),
            f"--defaults-file={config_file}",
            "--console"
        ]

        try:
            self.log(f"🔧 Starting server with command: {' '.join(cmd)}")
            process = subprocess.Popen(
                cmd,
                cwd=str(self.bin_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'
            )

            self.log("⏳ Waiting for MySQL server to start...")
            time.sleep(3)

            if process.poll() is not None:
                stdout, stderr = process.communicate()
                self.log("❌ MySQL server failed to start", "ERROR")
                self.log(f"📊 Exit code: {process.returncode}")
                if stdout:
                    self.log("📋 Server output:")
                    for line in stdout.strip().split('\n')[:20]:
                        if line.strip():
                            self.log(f"   {line.strip()}")
                if stderr:
                    self.log("📋 Server errors:")
                    for line in stderr.strip().split('\n')[:20]:
                        if line.strip():
                            self.log(f"   {line.strip()}")
                return None

            time.sleep(5)

            if process.poll() is None:
                self.log("✅ MySQL server started successfully")
                return process
            else:
                self.log("❌ MySQL server exited unexpectedly", "ERROR")
                return None

        except Exception as e:
            self.log(f"❌ Failed to start MySQL server: {e}", "ERROR")
            return None

    def test_mysql_connection(self, max_retries=10):
        """Test MySQL connection with better host handling"""
        self.log("🔍 Testing MySQL connection...")

        for attempt in range(max_retries):
            approaches = [
                [str(self.bin_path / "mysql.exe"), "-u", "root", "-h", "localhost", "-e", "SELECT 1;"],
                [str(self.bin_path / "mysql.exe"), "-u", "root", "-e", "SELECT 1;"],
                [str(self.bin_path / "mysqladmin.exe"), "-u", "root", "-h", "localhost", "ping"]
            ]

            for i, cmd in enumerate(approaches):
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        self.log(f"✅ MySQL server is responding (method {i + 1})")
                        return True
                    else:
                        if "Access denied" not in result.stderr:
                            self.log(f"   Method {i + 1} failed: {result.stderr.strip()}")
                except Exception as e:
                    self.log(f"   Method {i + 1} error: {e}")

            if attempt < max_retries - 1:
                self.log(f"⏳ Connection attempt {attempt + 1}/{max_retries} failed, retrying...")
                time.sleep(3)

        return False

    def connect_to_mysql(self, username="root", password="", database=None):
        """Connect to MySQL server using mysql.connector if available"""
        try:
            import mysql.connector
            from mysql.connector import Error

            connection = mysql.connector.connect(
                host='localhost',
                user=username,
                password=password,
                database=database,
                port=3306
            )
            return connection
        except ImportError:
            self.log("❌ mysql-connector-python not installed. Use: pip install mysql-connector-python", "ERROR")
            return None
        except Exception as e:
            self.log(f"❌ Failed to connect to MySQL: {e}", "ERROR")
            return None

    def change_root_password(self, new_password):
        """Change root password using mysql_native_password for compatibility"""
        self.log("🔐 Setting root password with mysql_native_password...")

        connection = self.connect_to_mysql(username="root", password="")
        if not connection:
            self.log("❌ Cannot connect to MySQL to set password", "ERROR")
            return False

        try:
            cursor = connection.cursor()

            mysql_version = self.detect_mysql_version()

            if mysql_version >= 8.4:
                # MySQL 8.4+ syntax
                self.log("   Using MySQL 8.4+ authentication syntax")
                cursor.execute(
                    f"ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '{new_password}';"
                )
            else:
                # MySQL 8.0 and earlier
                cursor.execute(
                    f"ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '{new_password}';"
                )

            cursor.execute("FLUSH PRIVILEGES;")
            connection.commit()
            self.log("✅ Root password set with mysql_native_password")

            self.root_password = new_password
            cursor.close()
            connection.close()
            return True

        except Exception as e:
            self.log(f"❌ Error setting password: {e}", "ERROR")
            if connection and connection.is_connected():
                connection.close()
            return False

    def fix_existing_root_password(self):
        """Fix existing root user to use mysql_native_password"""
        self.log("🔧 Converting root user to mysql_native_password...")
        if not self.root_password:
            self.log("❌ Root password not set", "ERROR")
            return False
        connection = self.connect_to_mysql(username="root", password=self.root_password)
        if not connection:
            self.log("❌ Cannot connect to MySQL", "ERROR")
            return False
        try:
            cursor = connection.cursor()
            # Check current authentication plugin
            cursor.execute("SELECT plugin FROM mysql.user WHERE user='root' AND host='localhost';")
            result = cursor.fetchone()
            if result:
                current_plugin = result[0]
                self.log(f"📋 Current authentication plugin: {current_plugin}")
                if current_plugin != "mysql_native_password":
                    self.log("🔄 Converting to mysql_native_password...")
                    cursor.execute(
                        f"ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '{self.root_password}';")
                    cursor.execute("FLUSH PRIVILEGES;")
                    connection.commit()
                    self.log("✅ Root user converted to mysql_native_password")
                else:
                    self.log("✅ Root user already uses mysql_native_password")
            cursor.close()
            connection.close()
            return True
        except Exception as e:
            self.log(f"❌ Error fixing root user: {e}", "ERROR")
            if connection and connection.is_connected():
                connection.close()
            return False

    def create_database_and_user(self, service_name=None, database=None, username=None, password=None):
        """Create database and user for a service"""
        if service_name and service_name in self.service_configs:
            config = self.service_configs[service_name]
            database = config["database"]
            username = config["username"]
            password = config["password"]
            description = config["description"]
        elif not all([database, username, password]):
            self.log("❌ Missing required parameters", "ERROR")
            return False
        else:
            description = f"Custom database: {database}"

        connection = self.connect_to_mysql(password=self.root_password)
        if not connection:
            self.log("❌ Cannot connect to MySQL. Is the server running?", "ERROR")
            return False

        try:
            cursor = connection.cursor()

            mysql_version = self.detect_mysql_version()

            # Create database
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;"
            )
            self.log(f"✅ Database '{database}' created/verified")

            # Drop user if exists
            cursor.execute(f"DROP USER IF EXISTS '{username}'@'localhost';")

            # Create user with mysql_native_password
            if mysql_version >= 8.4:
                # MySQL 8.4+ requires mysql_native_password to be explicitly enabled
                self.log(f"   Creating user for MySQL 8.4+ with mysql_native_password")
                cursor.execute(
                    f"CREATE USER '{username}'@'localhost' IDENTIFIED WITH mysql_native_password BY '{password}';"
                )
            else:
                cursor.execute(
                    f"CREATE USER '{username}'@'localhost' IDENTIFIED WITH mysql_native_password BY '{password}';"
                )

            self.log(f"✅ User '{username}' created with mysql_native_password")

            # Grant privileges
            cursor.execute(f"GRANT ALL PRIVILEGES ON `{database}`.* TO '{username}'@'localhost';")
            cursor.execute("FLUSH PRIVILEGES;")
            self.log(f"✅ Privileges granted to '{username}' on '{database}'")

            # Create test table for testdb
            if database == "testdb":
                cursor.execute(f"USE `{database}`;")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS test_table (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(50),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cursor.execute("INSERT IGNORE INTO test_table (name) VALUES ('Test Data');")
                self.log("✅ Test table created with sample data")

            connection.commit()
            self.log(f"🎉 {description} setup completed!")

            self.save_service_info(service_name or 'custom', database, username, password)
            return True

        except Exception as e:
            self.log(f"❌ Failed to create DB/user: {e}", "ERROR")
            return False
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

    def check_drupal_installation(self):
        """Check if Drupal is properly installed in the database"""
        connection = self.connect_to_mysql(
            username="drupal_user",
            password="drupal_pass_123",
            database="drupal_db"
        )

        if not connection:
            self.log("❌ Cannot connect to Drupal database", "ERROR")
            return False

        try:
            cursor = connection.cursor()
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()

            if len(tables) == 0:
                self.log("❌ Drupal database is empty - Drupal not installed!", "ERROR")
                self.log("💡 Go to http://localhost/drupal/install.php to install Drupal")
                return False

            self.log(f"✅ Found {len(tables)} tables in drupal_db")

            # Check for essential Drupal tables
            essential_tables = ['users', 'node', 'system', 'variable']
            table_names = [t[0] for t in tables]

            for table in essential_tables:
                if table in table_names:
                    self.log(f"   ✓ {table}")
                else:
                    self.log(f"   ✗ {table} missing", "WARNING")

            cursor.close()
            connection.close()
            return True

        except Exception as e:
            self.log(f"❌ Error checking Drupal: {e}", "ERROR")
            return False

    def save_service_info(self, service_name, database, username, password):
        """Save service info to JSON"""
        info_file = self.mysql_path / "services_info.json"
        service_info = {
            "service": service_name,
            "database": database,
            "username": username,
            "password": password,
            "host": "localhost",
            "port": 3306,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        services = []
        if info_file.exists():
            try:
                services = json.loads(info_file.read_text())
            except:
                pass

        services = [s for s in services if s.get('service') != service_name]
        services.append(service_info)

        info_file.write_text(json.dumps(services, indent=2), encoding='utf-8')
        self.log(f"💾 Service info saved: {info_file}")

    def list_services(self):
        """List all configured services"""
        info_file = self.mysql_path / "services_info.json"
        if not info_file.exists():
            self.log("ℹ️ No services configured yet")
            return

        try:
            services = json.loads(info_file.read_text())
            self.log("\n📋 CONFIGURED SERVICES")
            self.log("=" * 60)
            for s in services:
                self.log(f"🔹 {s['service'].upper()}")
                self.log(f"   DB: {s['database']} | User: {s['username']}")
                self.log(f"   Password: {s['password']}")
                self.log(f"   Created: {s['created_at']}")
                self.log("")
        except Exception as e:
            self.log(f"❌ Failed to read services: {e}", "ERROR")

    def create_drupal_settings_file(self):
        """Create Drupal settings.php snippet"""
        if "drupal" not in self.service_configs:
            self.log("❌ Drupal configuration not found", "ERROR")
            return False

        config = self.service_configs["drupal"]

        settings_content = f'''<?php
/**
 * Database configuration for Drupal 7
 * Generated by MySQL Manager
 */

$databases['default']['default'] = array(
  'driver' => 'mysql',
  'database' => '{config["database"]}',
  'username' => '{config["username"]}',
  'password' => '{config["password"]}',
  'host' => 'localhost',
  'port' => 3306,
  'prefix' => '',
  'collation' => 'utf8mb4_general_ci',
);

/**
 * Connection information:
 * - Database: {config["database"]}
 * - Username: {config["username"]}
 * - Password: {config["password"]}
 * - Host: localhost
 * - Port: 3306
 * 
 * This configuration uses mysql_native_password for compatibility.
 */
'''

        output_dir = self.mysql_path / "drupal_config"
        output_dir.mkdir(exist_ok=True)

        settings_file = output_dir / "drupal_settings_snippet.php"
        settings_file.write_text(settings_content, encoding='utf-8')

        self.log(f"📄 Drupal settings snippet created: {settings_file}")
        self.log("💡 Copy this configuration to your sites/default/settings.php")

        return True

    def recreate_database(self, service_name):
        """Recreate a database (drops and creates fresh)"""
        if service_name not in self.service_configs:
            self.log(f"❌ Unknown service: {service_name}", "ERROR")
            return False

        config = self.service_configs[service_name]
        database = config["database"]

        connection = self.connect_to_mysql(password=self.root_password)
        if not connection:
            self.log("❌ Cannot connect to MySQL", "ERROR")
            return False

        try:
            cursor = connection.cursor()

            # Drop database
            self.log(f"🗑️ Dropping database '{database}'...")
            cursor.execute(f"DROP DATABASE IF EXISTS `{database}`;")

            # Recreate with utf8mb4
            cursor.execute(
                f"CREATE DATABASE `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            self.log(f"✅ Database '{database}' recreated with utf8mb4")

            connection.commit()
            cursor.close()
            connection.close()

            self.log(f"✅ Database ready for fresh installation")
            return True

        except Exception as e:
            self.log(f"❌ Failed to recreate database: {e}", "ERROR")
            return False
        finally:
            if connection and connection.is_connected():
                connection.close()

    def create_php_test_file(self, service_name="testapp"):
        """Create PHP test file"""
        if service_name not in self.service_configs:
            service_name = "testapp"
        config = self.service_configs[service_name]

        php_content = f'''<?php
echo "<h1>✅ PHP + MySQL Test - {config["description"]}</h1>";
echo "<p>PHP Version: " . phpversion() . "</p>";

$dbname = '{config["database"]}';
$dbuser = '{config["username"]}';
$dbpass = '{config["password"]}';
$dbhost = 'localhost';

echo "<h2>📡 Connecting to MySQL...</h2>";
$link = mysqli_connect($dbhost, $dbuser, $dbpass);
if (!$link) {{
    die("<p style='color:red'>❌ Connection failed: " . mysqli_connect_error() . "</p>");
}}
echo "<p style='color:green'>✔ Connected to MySQL server</p>";

if (!mysqli_select_db($link, $dbname)) {{
    die("<p style='color:red'>❌ Cannot select database: " . mysqli_error($link) . "</p>");
}}
echo "<p style='color:green'>✔ Database '{config['database']}' selected</p>";

$result = mysqli_query($link, "SHOW TABLES");
if ($result) {{
    echo "<h3>📋 Tables:</h3><ul>";
    while ($row = mysqli_fetch_row($result)) {{
        echo "<li>{{$row[0]}}</li>";
    }}
    echo "</ul>";
}}

// Test authentication plugin
$result = mysqli_query($link, "SELECT plugin FROM mysql.user WHERE user='{config['username']}' LIMIT 1");
if ($result && $row = mysqli_fetch_assoc($result)) {{
    echo "<p>🔐 Authentication plugin: <strong>{{$row['plugin']}}</strong></p>";
}}

mysqli_close($link);
echo "<p style='color:green'>✅ Connection closed successfully.</p>";
?>
'''

        htdocs_dir = Path("C:/APACHE24/htdocs")
        if not htdocs_dir.exists():
            htdocs_dir.mkdir(parents=True, exist_ok=True)
            self.log(f"📁 Created htdocs directory: {htdocs_dir}")

        test_file = htdocs_dir / f"test_mysql_{service_name}.php"
        test_file.write_text(php_content, encoding='utf-8')
        self.log(f"📄 PHP test file created: {test_file}")
        self.log(f"🌐 Access at: http://localhost/test_mysql_{service_name}.php")

    def full_setup(self, services=None, root_password="root"):
        """Complete automated setup with specified services"""
        self.log("🚀 STARTING FULLY AUTOMATED MySQL SETUP")
        self.log(f"🔑 Root password will be set to: {root_password}")

        if services is None:
            services = ["testapp", "drupal"]

        self.log(f"📦 Services to create: {', '.join(services)}")

        # Check if MySQL is already running
        if self.is_mysql_running():
            self.log("⚠️ MySQL is already running!", "WARNING")
            self.log("🔄 Stopping and reinitializing...")
            if not self.stop_mysql_server():
                self.log("❌ Cannot proceed with setup", "ERROR")
                return False

        if not self.create_directories():
            return False
        if not self.download_mysql():
            return False
        if not self.create_config_file():
            return False

        if self.initialize_mysql() is None:
            return False

        proc = self.start_mysql_server()
        if not proc:
            return False

        time.sleep(5)

        if not self.test_mysql_connection():
            self.log("❌ MySQL server is not responding", "ERROR")
            return False

        if not self.change_root_password(root_password):
            return False

        # Create all requested services
        for service in services:
            if service in self.service_configs:
                self.log(f"\n{'=' * 60}")
                self.log(f"Creating service: {service}")
                self.log(f"{'=' * 60}")
                if not self.create_database_and_user(service):
                    self.log(f"⚠️ Failed to create service: {service}", "WARNING")
                else:
                    self.create_php_test_file(service)
            else:
                self.log(f"⚠️ Unknown service: {service}", "WARNING")

        # Create Drupal settings if drupal was requested
        if "drupal" in services:
            self.create_drupal_settings_file()

        if "drupal" in services:
            self.log("\n" + "=" * 60)
            self.log("Checking Drupal installation...")
            self.log("=" * 60)
            self.check_drupal_installation()

        self.log("\n" + "=" * 60)
        self.log("🎉 SUCCESS! MySQL is fully configured and ready!")
        self.log("=" * 60)
        self.log(f"🔑 Root password: {root_password}")
        self.log(f"📋 Services created: {', '.join(services)}")
        self.log(f"📄 Configuration saved to: {self.mysql_path}/services_info.json")
        self.log("\n💡 MySQL server is running. Keep this terminal open or use 'start-server' to restart.")


        return True

    def fix_existing_installation(self):
        """Fix an existing MySQL installation to use mysql_native_password"""
        self.log("🔧 FIXING EXISTING MySQL INSTALLATION")

        # Check if MySQL is running
        if not self.is_mysql_running():
            self.log("⚠️ MySQL is not running. Starting it...", "WARNING")
            if not self.start_mysql_server():
                self.log("❌ Cannot start MySQL", "ERROR")
                return False
            time.sleep(5)

        # Update config file
        self.log("📝 Updating configuration file...")
        if not self.create_config_file():
            return False

        # Restart MySQL
        self.log("🔄 Restarting MySQL with new configuration...")
        if not self.stop_mysql_server():
            return False

        time.sleep(2)

        if not self.start_mysql_server():
            return False

        time.sleep(5)

        # Get root password
        if not self.root_password:
            self.root_password = getpass.getpass("Enter current root password: ")

        # Fix root user
        if not self.fix_existing_root_password():
            return False

        self.log("✅ Installation fixed successfully!")
        return True


def parse_args():
    parser = argparse.ArgumentParser(description="MySQL Manager - Fully Automated Version")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Comando 'setup'
    setup_parser = subparsers.add_parser("setup", help="Full installation")
    setup_parser.add_argument("--services", nargs="+", default=["testapp", "drupal"], help="Services to create")
    setup_parser.add_argument("--root-password", default="root", help="Root password")

    # Comando 'create-service'
    create_service_parser = subparsers.add_parser("create-service", help="Create predefined or custom service")
    create_service_parser.add_argument("name", help="Service name or 'custom'")
    create_service_parser.add_argument("--db", help="Database name (for custom)")
    create_service_parser.add_argument("--user", help="Username (for custom)")
    create_service_parser.add_argument("--pwd", help="Password (for custom)")


    # Comando 'fix-installation'
    subparsers.add_parser("fix-installation", help="Fix an existing MySQL installation")

    # Comando 'recreate-db'
    recreate_parser = subparsers.add_parser("recreate-db", help="Recreate a database (fresh install)")
    recreate_parser.add_argument("service", help="Service name (e.g., drupal, wordpress)")

    # Comando 'list-services'
    subparsers.add_parser("list-services", help="Show all databases")

    # Comando 'create-drupal-config'
    subparsers.add_parser("create-drupal-config", help="Create Drupal settings.php snippet")

    # Comando 'start-server'
    subparsers.add_parser("start-server", help="Start MySQL server")

    # Comando 'stop-server'
    subparsers.add_parser("stop-server", help="Stop MySQL server")

    # Comando 'test-connection'
    subparsers.add_parser("test-connection", help="Test if MySQL is responding")

    # Comando 'status'
    subparsers.add_parser("status", help="Check if MySQL is running")

    return parser.parse_args()


def main():
    args = parse_args()
    mgr = MySQLManager()

    if args.command == "setup":
        mgr.full_setup(services=args.services, root_password=args.root_password)
    elif args.command == "create-service":
        if args.name == "custom":
            if not all([args.db, args.user, args.pwd]):
                print("Error: For custom service, you must provide --db, --user, and --pwd")
                return
            mgr.root_password = getpass.getpass("Root password: ")
            mgr.create_database_and_user(database=args.db, username=args.user, password=args.pwd)
        else:
            mgr.root_password = getpass.getpass("Root password: ")
            mgr.create_database_and_user(args.name)
    elif args.command == "fix-installation":
        mgr.fix_existing_installation()
    elif args.command == "recreate-db":
        mgr.root_password = getpass.getpass("Root password: ")
        mgr.recreate_database(args.service)
    elif args.command == "list-services":
        mgr.list_services()
    elif args.command == "create-drupal-config":
        mgr.create_drupal_settings_file()
    elif args.command == "start-server":
        mgr.start_mysql_server()
    elif args.command == "stop-server":
        mgr.stop_mysql_server()
    elif args.command == "test-connection":
        mgr.test_mysql_connection()
    elif args.command == "status":
        if mgr.is_mysql_running():
            mgr.log("✅ MySQL is running")
        else:
            mgr.log("❌ MySQL is not running")


if __name__ == "__main__":
    main()