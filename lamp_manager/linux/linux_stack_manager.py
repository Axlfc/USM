# lamp_manager/linux/linux_stack_manager.py
import os
import secrets
import string
from pathlib import Path

from .apache_manager import ApacheManager
from .mysql_manager import MySQLManager
from .php_manager import PHPManager
from lamp_manager.core.config import LAMPConfig
from lamp_manager.core.logger import AuditLogger
from lamp_manager.core.rollback import RollbackManager
from lamp_manager.core.validators import SystemValidator

class LinuxStackManager:
    def __init__(self, dry_run: bool = False):
        self.config = LAMPConfig()
        self.dry_run = dry_run or self.config.get('security.dry_run_by_default', False)
        self.logger = AuditLogger()
        self.rollback = RollbackManager()
        self.apache = ApacheManager(self.config, self.logger, self.rollback)
        self.mysql = MySQLManager(self.config, self.logger, self.rollback)
        self.php = PHPManager(self.config, self.logger)

    def install_stack(self, php_version: str):
        """Instala el stack LAMP completo."""

        # 1. Validar prerrequisitos del sistema
        is_valid, errors = SystemValidator.validate_prerequisites()
        if not is_valid:
            print("❌ Errores de prerrequisitos del sistema:")
            for error in errors:
                print(f"   - {error}")
            return False

        print("Iniciando la instalación del stack LAMP...")

        if self.dry_run:
            print("\n🔍 DRY RUN - No se realizarán cambios reales")
            print("📋 Plan de instalación:")
            print("  - Añadir PPA de PHP (si es necesario)")
            print("  - Instalar Apache2 y utilidades")
            print("  - Instalar MySQL/MariaDB server")
            print(f"  - Instalar PHP {php_version} y módulos comunes")
            return True

        # 2. Pedir confirmación
        response = input("\n¿Proceder con la instalación? [y/N]: ")
        if response.lower() != 'y':
            print("Operación cancelada.")
            return False

        # 3. Ejecutar con protección de rollback (aunque la instalación de paquetes no es transaccional)
        try:
            with self.rollback.protected_operation('install_stack', []):
                print("\nPaso 1: Instalando Apache...")
                if not self.apache.install():
                    raise RuntimeError("La instalación de Apache falló.")

                print("\nPaso 2: Instalando MySQL/MariaDB...")
                if not self.mysql.install():
                    raise RuntimeError("La instalación de MySQL falló.")

                print(f"\nPaso 3: Instalando PHP {php_version}...")
                if not self.php.install(php_version):
                    raise RuntimeError(f"La instalación de PHP {php_version} falló.")

            user = os.getenv('SUDO_USER', 'unknown')
            self.logger.audit('install_stack', 'lamp', user, {'php_version': php_version})
            print("\n✅ Stack LAMP instalado correctamente.")
            return True

        except Exception as e:
            print(f"\n❌ Falló la instalación del stack: {e}")
            return False

    def create_site(self, site_name: str, php_version: str):
        """Crea un nuevo sitio web (vhost, directorio, BD)."""

        site_config = {
            'site_name': site_name,
            'php_version': php_version
        }

        # 1. Validar configuración del sitio y prerrequisitos
        supported_versions = self.config.get('php.supported_versions')
        is_valid, errors = SystemValidator.validate_site_config(site_config, supported_versions)
        if not is_valid:
            print("❌ Errores de validación de la configuración del sitio:")
            for error in errors:
                print(f"   - {error}")
            return False

        # 2. Mostrar plan de ejecución
        db_name = f"{site_name.replace('.', '_')}_db"
        doc_root = f"{self.config.get('apache.sites_dir')}/{site_name}"
        doc_root_subdir = self.config.get('apache.doc_root_subdir', 'web')
        print(f"\n📋 Plan para crear el sitio '{site_name}':")
        print(f"   - Versión de PHP: {php_version}")
        print(f"   - Base de datos: {db_name}")
        print(f"   - DocumentRoot: {doc_root}/{doc_root_subdir}")

        if self.dry_run:
            print("\n🔍 DRY RUN - No se realizarán cambios reales.")
            return True

        # 3. Pedir confirmación
        response = input("\n¿Continuar con la creación del sitio? [y/N]: ")
        if response.lower() != 'y':
            print("Operación cancelada.")
            return False

        # 4. Ejecutar con protección de rollback
        try:
            doc_root_path = Path(doc_root)
            vhost_file = Path(self.config.get('apache.vhosts_dir')) / f"{site_name}.conf"

            # Ahora la operación protegida conoce los ficheros y directorios a revertir
            with self.rollback.protected_operation('create_site', [doc_root_path, vhost_file]):
                self._do_create_site(site_name, php_version, db_name, doc_root)

            user = os.getenv('SUDO_USER', 'unknown')
            self.logger.audit('create_site', site_name, user, {'php_version': php_version})
            print(f"\n✅ Sitio '{site_name}' creado correctamente.")
            print("\n--- Credenciales de la Base de Datos ---")
            print(f"  Database: {db_name}")
            print(f"  Username: {db_name}_user")
            print(f"  Password: {self.last_generated_password}")
            print("----------------------------------------")
            return True

        except Exception as e:
            print(f"\n❌ Falló la creación del sitio: {e}")
            return False

    def _do_create_site(self, site_name, php_version, db_name, doc_root):
        """Lógica interna para crear el sitio."""

        # Generar un password seguro
        alphabet = string.ascii_letters + string.digits
        db_password = ''.join(secrets.choice(alphabet) for i in range(16))
        db_user = f"{db_name}_user"

        print(f"\nCreando DocumentRoot en {doc_root}...")
        doc_root_path = Path(doc_root)
        doc_root_subdir = self.config.get('apache.doc_root_subdir', '')
        full_doc_root_path = doc_root_path / doc_root_subdir
        os.makedirs(full_doc_root_path, exist_ok=True)
        # Aquí iría la lógica para chown/chmod

        print(f"Creando VirtualHost para Apache...")
        if not self.apache.create_virtualhost(site_name, str(doc_root_path), php_version):
            raise RuntimeError("La creación del VirtualHost falló.")

        print(f"Creando base de datos '{db_name}'...")
        if not self.mysql.create_database(db_name):
            raise RuntimeError("La creación de la base de datos falló.")

        print(f"Creando usuario de base de datos '{db_user}'...")
        if not self.mysql.create_user(db_user, db_password):
            raise RuntimeError("La creación del usuario de base de datos falló.")

        print(f"Otorgando privilegios...")
        if not self.mysql.grant_privileges(db_name, db_user):
            raise RuntimeError("El otorgamiento de privilegios falló.")

        print("Recargando configuración de Apache...")
        if not self.apache.reload_service():
            raise RuntimeError("La recarga de Apache falló.")

        # Almacenar el password para mostrarlo al final
        self.last_generated_password = db_password
