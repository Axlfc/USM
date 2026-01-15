# unified_stack_manager/windows/legacy/services/mysql/mysql_manager.py
import subprocess
from ..base_service import BaseService

class MySQLManager(BaseService):
    def __init__(self, config=None):
        # El config podría usarse en el futuro para obtener la ruta al binario de mysql, etc.
        self.config = config

    def _execute_query(self, query: str) -> bool:
        """Ejecuta una consulta SQL usando el cliente de línea de comandos de mysql."""
        self.print_colored(f"Ejecutando query: {query}", "gray")
        try:
            # En Windows, puede que necesitemos especificar el usuario y contraseña si mysql_secure_installation se ha ejecutado
            # Por ahora, asumimos que el acceso root sin contraseña está disponible para scripts.
            subprocess.run(
                ['mysql', '-u', 'root', '-e', query],
                check=True,
                capture_output=True,
                text=True
            )
            return True
        except subprocess.CalledProcessError as e:
            self.print_colored(f"Error al ejecutar la consulta SQL: {e.stderr}", "red")
            return False
        except FileNotFoundError:
            self.print_colored("Error: El comando 'mysql' no fue encontrado. Asegúrate de que está en el PATH del sistema.", "red")
            return False

    def create_database(self, db_name: str) -> bool:
        """Crea una nueva base de datos."""
        query = f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        return self._execute_query(query)

    def create_user(self, username: str, password: str, host: str = 'localhost') -> bool:
        """Crea un nuevo usuario de base de datos."""
        query = f"CREATE USER IF NOT EXISTS '{username}'@'{host}' IDENTIFIED BY '{password}';"
        return self._execute_query(query)

    def grant_privileges(self, db_name: str, username: str, host: str = 'localhost') -> bool:
        """Otorga todos los privilegios a un usuario sobre una base de datos."""
        query = f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{username}'@'{host}';"
        if not self._execute_query(query):
            return False
        return self._execute_query("FLUSH PRIVILEGES;")

    def create_database_and_user(self, db_name: str, username: str, password: str) -> bool:
        """Método de conveniencia para crear BD, usuario y otorgar privilegios."""
        self.print_colored(f"Iniciando creación de base de datos '{db_name}' y usuario '{username}'.", "cyan")
        if not self.create_database(db_name):
            self.print_colored(f"Falló la creación de la base de datos '{db_name}'.", "red")
            return False
        if not self.create_user(username, password):
            self.print_colored(f"Falló la creación del usuario '{username}'.", "red")
            return False
        if not self.grant_privileges(db_name, username):
            self.print_colored(f"Falló el otorgamiento de privilegios a '{username}' sobre '{db_name}'.", "red")
            return False

        self.print_colored(f"Base de datos y usuario creados con éxito.", "green")
        return True
