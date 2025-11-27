from fabric import Connection
from invoke import task

# Configuración del servidor
REMOTE_HOST = "144.126.219.62"
REMOTE_USER = "root"
REMOTE_PROJECT_PATH = "/home/xofi-recaudo/"
GIT_REPO = "git@github.com:RobertArzolaC/xofi-recaudo.git"


@task
def deploy(c):
    """Realiza el despliegue del proyecto Django y reinicia los servicios."""
    # Conectarse al servidor remoto
    print("Conectando al servidor...")
    conn = Connection(host=REMOTE_HOST, user=REMOTE_USER)

    # Cambiar al directorio del proyecto
    with conn.cd(REMOTE_PROJECT_PATH):
        print("Obteniendo los últimos cambios del repositorio...")
        conn.run("git pull origin main")

        print("Actualizando dependencias...")
        conn.run(
            "source venv/bin/activate && pip install -r requirements/production.txt"
        )

        print("Aplicando migraciones...")
        conn.run("source venv/bin/activate && python manage.py migrate")

        print("Aplicando traducciones...")
        conn.run(
            'source venv/bin/activate && python manage.py compilemessages -l es --ignore "venv/*"'
        )

        print("Recopilando archivos estáticos...")
        conn.run(
            "source venv/bin/activate && python manage.py collectstatic --noinput"
        )

        print("Reiniciando el servidor web...")
        conn.run("sudo systemctl restart xofi-recaudo")
        conn.run("sudo systemctl restart nginx")

        print("Reiniciando los servicios de Celery...")
        conn.run("sudo systemctl restart celery-recaudo")
        conn.run("sudo systemctl restart celery-beat-recaudo")

    print("¡Despliegue completado con éxito!")


@task
def status(c):
    """Verifica el estado de todos los servicios críticos."""
    conn = Connection(host=REMOTE_HOST, user=REMOTE_USER)

    print("Verificando estado de los servicios...")
    services = ["xofi-recaudo", "nginx", "celery-recaudo", "celerybeat-recaudo"]

    for service in services:
        print(f"\nEstado de {service}:")
        conn.run(f"sudo systemctl status {service} | grep Active")


@task
def logs(c, service="celery", lines=50):
    """Muestra los logs de un servicio específico."""
    conn = Connection(host=REMOTE_HOST, user=REMOTE_USER)

    valid_services = {
        "gunicorn": "xofi-recaudo",
        "nginx": "nginx",
        "celery": "celery-recaudo",
        "beat": "celerybeat-recaudo",
    }

    if service not in valid_services:
        print(
            f"Servicio inválido. Opciones disponibles: {', '.join(valid_services.keys())}"
        )
        return

    print(f"Mostrando los últimos {lines} logs de {service}...")
    conn.run(
        f"sudo journalctl -u {valid_services[service]} -n {lines} --no-pager"
    )
