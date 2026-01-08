# main.py
import argparse
from core.orchestrator import Orchestrator


def main():
    parser = argparse.ArgumentParser(description="DevStack Orchestrator")
    parser.add_argument("--install-php", type=str, help="Instalar versión PHP (ej: 8.3)")
    parser.add_argument("--setup-apache", action="store_true", help="Configurar Apache para PHP actual")
    parser.add_argument("--restart", action="store_true", help="Reiniciar Apache")
    parser.add_argument("--info", action="store_true", help="Mostrar estado")

    args = parser.parse_args()
    orch = Orchestrator()

    if args.install_php:
        orch.setup_php_and_apache(args.install_php)

    elif args.setup_apache:
        # Use active PHP logic or default
        orch.apache.update_php_module(orch.php.available_versions["8.3"])
        if args.restart:
            orch.apache.restart()

    elif args.restart:
        orch.apache.restart()

    elif args.info:
        orch.info()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()