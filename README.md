


# Mostrar ayuda
.\PythonFiles\.venv\Scripts\python .\PythonFiles\php_manager.py --help

# Listar versiones
.\PythonFiles\.venv\Scripts\python .\PythonFiles\php_manager.py -l

# Instalar PHP 8.3
.\PythonFiles\.venv\Scripts\python .\PythonFiles\php_manager.py --install -v 8.3

.\PythonFiles\.venv\Scripts\python .\PythonFiles\php_manager.py --install -v 8.1


# Cambiar versión CLI (y autoinstalar si no existe)
.\PythonFiles\.venv\Scripts\python .\PythonFiles\php_manager.py -v 8.3

# Mostrar info de PHP 8.3
.\PythonFiles\.venv\Scripts\python .\PythonFiles\php_manager.py -i -v 8.3

# Escanear versiones online
.\PythonFiles\.venv\Scripts\python .\PythonFiles\php_manager.py --scan


# Mapear directorio
.\PythonFiles\.venv\Scripts\python .\PythonFiles\php_manager.py -d "C:\APACHE24\htdocs\project1" -v 8.3 -a project1
.\PythonFiles\.venv\Scripts\python .\PythonFiles\php_manager.py -d "C:\APACHE24\htdocs\legacy" -v 8.1 -a legacy






# Mostrar mappings
.\PythonFiles\.venv\Scripts\python .\PythonFiles\php_manager.py --show-mappings

# Eliminar mapping
.\PythonFiles\.venv\Scripts\python .\PythonFiles\php_manager.py --remove-mapping -a project1

# Configurar Apache multi-versión
.\PythonFiles\.venv\Scripts\python .\PythonFiles\php_manager.py --setup-multiversion

# Ejecutar comando
python php_manager.py --command "php -r 'echo PHP_VERSION;'"

---




