# core/orchestrator.py
from services.php.php_manager import PHPManager
from services.apache.apache_manager import ApacheManager
from services.mysql.mysql_manager import MySQLManager

print("hola")

class Orchestrator:
    def __init__(self):
        self.php = PHPManager()
        self.apache = ApacheManager()
        self.mysql = MySQLManager()

    def setup_php_and_apache(self, version: str, restart_apache: bool = True):
        if not self.php.install_version(version):
            return False

        php_path = self.php.available_versions[version]
        if not self.apache.update_php_module(php_path):
            return False

        if restart_apache:
            return self.apache.restart()

        return True

    def info(self):
        self.php.print_colored("🔧 Servicios disponibles:", "cyan")
        self.php.print_colored(f"  PHP: {list(self.php.available_versions.keys())}", "gray")
        self.php.print_colored(f"  Apache: {self.apache.conf_path}", "gray")