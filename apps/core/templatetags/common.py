from decimal import Decimal

from django import template

register = template.Library()


@register.filter
def map_key(items, key):
    return [item[key] for item in items] if items else []


@register.filter
def subtract(value, arg):
    """Subtract the arg from the value."""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return value


@register.filter
def divide(value, arg):
    """Divide the value by arg."""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return value


@register.filter
def percentage(part, whole):
    """
    Calculate the percentage of `part` out of `whole`.
    """
    try:
        part = float(part)
        whole = float(whole)
        if whole == 0:
            return "0%"  # Prevent division by zero
        return f"{(part / whole) * 100:.2f}%"
    except (ValueError, TypeError):
        return "Invalid input"


@register.filter
def format_number(value):
    """
    Formatea un número eliminando ceros innecesarios al final.
    Ejemplos:
    0.000 -> 0
    0.450 -> 0.45
    0.500 -> 0.5
    18.900 -> 18.9
    """
    if value is None:
        return ""

    # Convertir a Decimal para manejar correctamente la precisión
    if not isinstance(value, Decimal):
        try:
            value = Decimal(str(value))
        except (ValueError, TypeError):
            return value

    # Convertir a string y eliminar ceros innecesarios
    str_value = str(value)
    if "." in str_value:
        str_value = (
            str_value.rstrip("0").rstrip(".") if "." in str_value else str_value
        )

    # Si quedó vacío (caso de 0.000), devolver "0"
    if str_value == "":
        return "0"

    return str_value


@register.filter
def get_status_display_from_value(status_value, choices_class):
    """
    Get display value for a status from its value and choices class.

    Usage in template: {{ status_value|get_status_display_from_value:"apps.credits.choices.CreditApplicationStatus" }}

    Args:
        status_value: The status value (e.g., "DRAFT", "SUBMITTED")
        choices_class: String path to the choices class

    Returns:
        str: The translated display value
    """
    if not status_value:
        return ""

    try:
        # Import the choices class dynamically
        module_path, class_name = choices_class.rsplit(".", 1)
        module = __import__(module_path, fromlist=[class_name])
        choices_cls = getattr(module, class_name)

        # Get the choices dict and return the display value
        choices_dict = dict(choices_cls.choices)
        return choices_dict.get(status_value, status_value)
    except (ImportError, AttributeError, ValueError):
        return status_value


@register.simple_tag
def get_credit_application_status_display(status_value):
    """
    Simple tag to get display value for credit application status.

    Usage in template: {% get_credit_application_status_display status_value %}

    Args:
        status_value: The status value (e.g., "DRAFT", "SUBMITTED")

    Returns:
        str: The translated display value
    """
    try:
        from apps.credits.choices import CreditApplicationStatus

        choices_dict = dict(CreditApplicationStatus.choices)
        return choices_dict.get(status_value, status_value)
    except ImportError:
        return status_value
