from django import template

register = template.Library()


@register.filter
def translate_permission(permission_obj) -> str:
    """
    Translate Django permission names from English to Spanish.

    Args:
        permission_obj: Permission object with name and content_type

    Returns:
        The translated permission name
    """
    # If it's a string (fallback), return as is
    if isinstance(permission_obj, str):
        return permission_obj

    # Map of English action prefixes to Spanish translations
    action_map = {
        "Can add": "Puede agregar",
        "Can change": "Puede modificar",
        "Can delete": "Puede eliminar",
        "Can view": "Puede ver",
        "Can approve": "Puede aprobar",
        "Can reject": "Puede rechazar",
        "Can review": "Puede revisar",
        "Can manage": "Puede administrar",
        "Can submit": "Puede enviar",
    }

    # Fallback translations for common model names when verbose_name is not available
    model_name_map = {
        "group": "grupo",
        "permission": "permiso",
        "user": "usuario",
        "agency": "agencia",
        "company": "empresa",
        "applicant": "aspirante",
        "credit": "crédito",
        "credits": "créditos",
        "credit refinance request": "solicitud de refinanciamiento",
        "credit refinance requests": "solicitudes de refinanciamiento",
        "credit reschedule request": "solicitud de reprogramación",
        "credit reschedule requests": "solicitudes de reprogramación",
        "loan reschedule request": "solicitud de reprogramación de préstamo",
        "loan reschedule requests": "solicitudes de reprogramación de préstamo",
        "credit application": "solicitud de crédito",
        "credit applications": "solicitudes de crédito",
        "credit application approval process": "proceso de aprobación de solicitud de crédito",
        "credit disbursement": "desembolso de crédito",
        "credit disbursements": "desembolsos de crédito",
        "credit status": "estado de crédito",
        "credit summary information": "información resumen de crédito",
        "document": "documento",
        "document history": "historial de documento",
        "document template": "plantilla de documento",
        "document type": "tipo de documento",
        "compliance payment": "pago de cumplimiento",
        "payment": "pago",
        "payment concept allocation": "asignación de concepto de pago",
        "payment installment allocation": "asignación de cuota de pago",
        "partner": "socio",
        "partner employment information": "información laboral del socio",
        "prospect": "prospecto",
        "contribution": "aportación",
        "contributions": "aportaciones",
        "social security": "previsión social",
        "penalty": "multa",
        "penalties": "multas",
        "status history": "historial de estado",
        "installment": "cuota",
        "product": "producto",
        "product type": "tipo de producto",
        "position": "posición",
        "area": "área",
        "employee": "empleado",
        "report": "reporte",
        "report filter": "filtro de reporte",
        "report type": "tipo de reporte",
    }

    permission_name = permission_obj.name

    # Get the model class to access verbose_name
    try:
        model_class = permission_obj.content_type.model_class()
        if model_class:
            # Force translation of verbose_name using _()
            verbose_name_raw = model_class._meta.verbose_name
            # If it's a lazy translation object, convert it to string which triggers translation
            model_verbose_name = str(verbose_name_raw)
        else:
            model_verbose_name = permission_obj.content_type.model
    except (AttributeError, Exception):
        model_verbose_name = None

    # Try to translate the action prefix
    for english_action, spanish_action in action_map.items():
        if permission_name.startswith(english_action):
            # Extract the model name from permission
            model_name = permission_name.replace(english_action, "").strip()
            model_name_lower = model_name.lower()
            # First, try to use the fallback dictionary (most reliable)
            translated_model = None
            for key, value in model_name_map.items():
                if key == model_name_lower or key.replace(
                    " ", ""
                ) == model_name_lower.replace(" ", ""):
                    translated_model = value
                    break

            # If found in fallback, use it
            if translated_model:
                return f"{spanish_action} {translated_model}"

            # Otherwise, try to use verbose_name from model
            if model_verbose_name:
                return f"{spanish_action} {model_verbose_name}"

            # Final fallback: keep original name
            return f"{spanish_action} {model_name}"

    # If no match found, return original
    return permission_name


@register.filter
def translate_app_name(app_label: str) -> str:
    """
    Translate Django app names from English to Spanish.

    Args:
        app_label: The app label (e.g., "auth", "compliance")

    Returns:
        The translated app name
    """
    # Map of app labels to Spanish translations
    app_translations = {
        "auth": "Autenticación",
        "compliance": "Cumplimiento",
        "credits": "Créditos",
        "customers": "Clientes",
        "documents": "Documentos",
        "payments": "Pagos",
        "partners": "Socios",
        "reports": "Reportes",
        "team": "Equipo",
        "users": "Usuarios",
        "core": "Principal",
        "home": "Inicio",
        "dashboard": "Panel",
    }

    return app_translations.get(app_label, app_label.title())


@register.filter
def translate_model_name(model_name: str) -> str:
    """
    Translate Django model names from English to Spanish (for titles/headings).

    Args:
        model_name: The model name (e.g., "Applicant", "Document History")

    Returns:
        The translated model name
    """
    # Map of model names to Spanish translations
    model_translations = {
        "applicant": "Aspirante",
        "applicants": "Aspirantes",
        "document history": "Historial De Documento",
        "document histories": "Historiales De Documento",
        "documenthistory": "Historial De Documento",
        "document template": "Plantilla De Documento",
        "document templates": "Plantillas De Documento",
        "documenttemplate": "Plantilla De Documento",
        "compliance payment": "Pago De Cumplimiento",
        "compliance payments": "Pagos De Cumplimiento",
        "compliancepayment": "Pago De Cumplimiento",
        "payment installment": "Cuota De Pago",
        "payment installments": "Cuotas De Pago",
        "paymentinstallment": "Cuota De Pago",
        "payment installment allocation": "Asignación De Cuota De Pago",
        "payment installment allocations": "Asignaciones De Cuota De Pago",
        "paymentinstallmentallocation": "Asignación De Cuota De Pago",
        "credit refinance request": "Solicitud De Refinanciamiento",
        "credit refinance requests": "Solicitudes De Refinanciamiento",
        "credit reschedule request": "Solicitud De Reprogramación",
        "credit reschedule requests": "Solicitudes De Reprogramación",
        "loan reschedule request": "Solicitud De Reprogramación De Préstamo",
        "loan reschedule requests": "Solicitudes De Reprogramación De Préstamo",
    }

    # Normalize the input to lowercase for comparison
    model_name_lower = model_name.lower()

    # Return translation if found, otherwise return original with title case
    return model_translations.get(model_name_lower, model_name)
