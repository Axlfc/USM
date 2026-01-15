#!/usr/bin/env python3
# lamp_manager/cli.py

import argparse
import sys
from lamp_manager.platform.detector import detect_platform
from lamp_manager.linux.linux_stack_manager import LinuxStackManager

def main():
    """Entry point que detecta el OS y delega"""

    # Detectar plataforma
    current_platform = detect_platform()

    print(f"🖥️  Plataforma detectada: {current_platform}")

    # Comprobar si la plataforma es compatible
    if current_platform != 'linux':
        print(f"❌ Plataforma no soportada: {current_platform}")
        sys.exit(1)

    # Configurar el parser de argumentos
    parser = argparse.ArgumentParser(description="LAMP Manager para Debian/Ubuntu")
    parser.add_argument(
        '--install-stack',
        metavar='PHP_VERSION',
        type=str,
        help='Instala el stack LAMP completo con una versión de PHP específica (ej: 8.2)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simula la ejecución sin realizar cambios reales.'
    )
    parser.add_argument(
        '--create-site',
        nargs=2,
        metavar=('SITE_NAME', 'PHP_VERSION'),
        help='Crea un nuevo sitio con el nombre de dominio y la versión de PHP especificados.'
    )

    args = parser.parse_args()

    # Instanciar el manager
    manager = LinuxStackManager(dry_run=args.dry_run)

    # Ejecutar comandos
    if args.install_stack:
        manager.install_stack(php_version=args.install_stack)
    elif args.create_site:
        site_name, php_version = args.create_site
        manager.create_site(site_name=site_name, php_version=php_version)
    else:
        # Si no se pasan argumentos, mostrar la ayuda
        parser.print_help()

if __name__ == '__main__':
    main()
