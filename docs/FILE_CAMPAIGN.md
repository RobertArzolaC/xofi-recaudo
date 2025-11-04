# Implementación de Campañas Basadas en CSV/Excel

## Contexto del Proyecto

Soy un desarrollador trabajando en un sistema Django de gestión de campañas de cobranza. Actualmente tenemos un sistema de campañas que funciona con grupos de partners existentes en la base de datos. Necesito implementar un nuevo tipo de campaña que permita cargar contactos desde archivos CSV o Excel con montos personalizados y recuerda que el codigo debe ser limpio, mantenible,bien documentado e ingles.

## Arquitectura Actual

El proyecto usa:
- **Framework**: Django 4.x con Python 3.x
- **Base de datos**: PostgreSQL
- **Tareas asíncronas**: Celery
- **Procesamiento de archivos**: Está disponible pandas, openpyxl, xlrd
- **Estructura**: Apps modulares Django (apps/campaigns/, apps/partners/, etc.)

### Modelos Existentes Relevantes

```python
# apps/campaigns/models.py contiene:
- Campaign: Modelo de campaña basado en grupos
- Group: Grupos de partners
- CampaignNotification: Notificaciones enviadas
- MessageTemplate: Plantillas de mensajes

# apps/partners/models.py contiene:
- Partner: Modelo de socio/cliente con deudas
```

## Requerimiento: Nuevo Sistema de Campañas CSV/Excel

### Objetivos

1. Implementar un sistema de campañas basado en archivos CSV/Excel
2. Permitir cargar contactos con montos personalizados
3. Validar los datos antes de ejecutar la campaña
4. Mantener compatibilidad con el sistema de notificaciones actual

### Arquitectura Propuesta

Usar **herencia de modelo base abstracto** con tres componentes principales:

1. **BaseCampaign** (abstracto): Campos y métodos comunes
2. **GroupBasedCampaign**: Refactorización del Campaign actual
3. **CSVBasedCampaign**: Nuevo tipo para archivos CSV/Excel

## Especificaciones Técnicas Detalladas

### 1. Estructura de Modelos

#### BaseCampaign (Abstracto)
```python
# Campos comunes a implementar:
- name, description (heredados de NameDescription)
- execution_date: DateTimeField
- status: CharField con CampaignStatus choices
- channel: CharField con NotificationChannel choices
- use_payment_link: BooleanField
- is_processing: BooleanField
- last_execution_at: DateTimeField
- execution_count: PositiveIntegerField
- last_execution_result: TextField
- campaign_type: CharField (discriminador, auto-poblado)

# Métodos abstractos a definir:
- can_be_executed() -> bool
- start_execution() -> bool
- finish_execution(success, result_message)
- get_notification_summary() -> dict
```

#### CSVBasedCampaign (Concreto)
```python
# Campos específicos:
- contacts_file: FileField (upload_to="campaigns/csv/%Y/%m/%d/")
- validation_status: CharField con ValidationStatus choices
- validation_result: JSONField
- validated_at: DateTimeField
- total_contacts: PositiveIntegerField
- valid_contacts: PositiveIntegerField
- invalid_contacts: PositiveIntegerField
- total_target_amount: DecimalField

# Métodos específicos:
- validate_csv_file() -> dict
- create_notifications_from_csv() -> list
- is_validated property
- validation_progress_percentage property
```

#### CSVContact (Nuevo Modelo)
```python
# Almacena cada contacto del archivo
- campaign: ForeignKey a CSVBasedCampaign
- full_name: CharField(max_length=200)
- email: EmailField (opcional)
- phone: CharField(max_length=20, opcional)
- document_number: CharField(max_length=20, opcional)
- custom_amount: DecimalField(max_digits=12, decimal_places=2)
- additional_data: JSONField (para campos extra del CSV)
- is_valid: BooleanField
- validation_errors: JSONField
- row_number: PositiveIntegerField
- linked_partner: ForeignKey a Partner (opcional, SET_NULL)

# Índices:
- campaign + is_valid
- document_number
- phone
```

#### GroupBasedCampaign (Refactorización)
```python
# Mover campos específicos del Campaign actual:
- group: ForeignKey
- target_amount: DecimalField
- average_cost: DecimalField

# Mantener métodos existentes específicos de grupos
```

### 2. Choices a Agregar

```python
# apps/campaigns/choices.py

class ValidationStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    PROCESSING = "PROCESSING", _("Processing")
    VALIDATED = "VALIDATED", _("Validated")
    FAILED = "FAILED", _("Failed")
    PARTIAL = "PARTIAL", _("Partially Valid")
```

### 3. Servicios a Implementar

#### CSVValidationService
```python
# apps/campaigns/services.py

class CSVValidationService:
    @classmethod
    def validate_campaign_csv(cls, campaign: CSVBasedCampaign) -> dict:
        """
        Valida el archivo CSV/Excel cargado.

        Pasos:
        1. Detectar tipo de archivo (CSV o Excel)
        2. Leer archivo con pandas/openpyxl
        3. Validar estructura (columnas requeridas)
        4. Validar cada fila:
           - Nombre completo (requerido)
           - Al menos email o teléfono (requerido)
           - Monto personalizado > 0 (requerido)
           - Formato de email válido
           - Formato de teléfono válido
        5. Intentar vincular con Partners existentes (por documento/email/teléfono)
        6. Crear registros CSVContact
        7. Actualizar estadísticas en campaign

        Returns:
            dict con:
            - success: bool
            - total_rows: int
            - valid_contacts: int
            - invalid_contacts: int
            - errors: list[dict]
            - warnings: list[dict]
        """
        pass

    @classmethod
    def parse_file(cls, file_path: str) -> pd.DataFrame:
        """
        Parsea CSV o Excel a DataFrame.
        Detecta automáticamente el formato.
        """
        pass

    @classmethod
    def validate_contact_row(cls, row: dict, row_number: int) -> tuple[bool, list]:
        """
        Valida una fila individual.

        Returns:
            (is_valid, error_list)
        """
        pass

    @classmethod
    def try_link_partner(cls, contact_data: dict):
        """
        Intenta encontrar un Partner existente.
        Busca por: document_number, email, phone
        """
        pass
```

#### CSVCampaignNotificationService
```python
class CSVCampaignNotificationService:
    @classmethod
    def create_notifications_from_csv(cls, campaign: CSVBasedCampaign) -> list:
        """
        Crea notificaciones para todos los contactos válidos.

        Similar a create_notifications_for_partners pero:
        - Lee desde CSVContact en lugar de Partners
        - Usa custom_amount en lugar de calcular deuda
        - Genera payment links si use_payment_link=True
        """
        pass
```

### 4. Tasks de Celery

```python
# apps/campaigns/tasks.py

@shared_task(name="campaigns.validate_csv_campaign")
def validate_csv_campaign(campaign_id: int) -> dict:
    """
    Tarea asíncrona para validar archivo CSV.

    Workflow:
    1. Obtener campaña
    2. Actualizar validation_status a PROCESSING
    3. Llamar a CSVValidationService.validate_campaign_csv()
    4. Actualizar validation_status según resultado
    5. Guardar validation_result
    6. Enviar notificación al usuario (opcional)

    Returns:
        dict con resultado de validación
    """
    pass

@shared_task(name="campaigns.process_csv_campaign_notifications")
def process_csv_campaign_notifications(campaign_id: int) -> dict:
    """
    Procesa y crea notificaciones para campaña CSV.

    Similar a process_campaign_notifications pero para CSVBasedCampaign.
    """
    pass
```

### 5. Forms

```python
# apps/campaigns/forms.py

class CSVBasedCampaignForm(forms.ModelForm):
    """
    Formulario para crear/editar campañas CSV.

    Campos:
    - name, description
    - contacts_file (FileField con validación)
    - execution_date
    - channel
    - use_payment_link

    Validaciones:
    - Archivo debe ser .csv, .xlsx, o .xls
    - Tamaño máximo: 10MB
    - No permitir cambiar archivo si ya está validado
    """

    class Meta:
        model = models.CSVBasedCampaign
        fields = [
            'name', 'description', 'contacts_file',
            'execution_date', 'channel', 'use_payment_link'
        ]
        widgets = {
            'contacts_file': forms.FileInput(
                attrs={
                    'class': 'form-control',
                    'accept': '.csv,.xlsx,.xls'
                }
            ),
            # ... otros widgets
        }

    def clean_contacts_file(self):
        """Validar archivo cargado."""
        pass
```

### 6. Views

```python
# apps/campaigns/views.py

class CSVCampaignListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Lista de campañas CSV."""
    model = models.CSVBasedCampaign
    template_name = "campaigns/csv_campaign/list.html"
    permission_required = "campaigns.view_csvbasedcampaign"
    paginate_by = 10

class CSVCampaignCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Crear campaña CSV."""
    model = models.CSVBasedCampaign
    form_class = forms.CSVBasedCampaignForm
    template_name = "campaigns/csv_campaign/form.html"
    permission_required = "campaigns.add_csvbasedcampaign"

class CSVCampaignValidateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Vista AJAX para iniciar validación de CSV."""
    permission_required = "campaigns.change_csvbasedcampaign"

    def post(self, request, pk):
        """
        Inicia validación asíncrona del CSV.

        Response JSON:
        {
            "success": true,
            "message": "Validation started",
            "task_id": "celery-task-id"
        }
        """
        pass

class CSVCampaignValidationStatusView(LoginRequiredMixin, View):
    """Vista AJAX para consultar estado de validación."""

    def get(self, request, pk):
        """
        Retorna estado actual de validación.

        Response JSON:
        {
            "validation_status": "VALIDATED",
            "total_contacts": 100,
            "valid_contacts": 95,
            "invalid_contacts": 5,
            "validation_result": {...},
            "progress_percentage": 95.0
        }
        """
        pass

class CSVContactListView(LoginRequiredMixin, DetailView):
    """Vista para ver contactos del CSV con filtros."""
    pass
```

### 7. URLs

```python
# apps/campaigns/urls.py

urlpatterns = [
    # ... URLs existentes ...

    # CSV Campaign URLs
    path("csv-campaigns/", views.CSVCampaignListView.as_view(),
         name="csv-campaign-list"),
    path("csv-campaign/create/", views.CSVCampaignCreateView.as_view(),
         name="csv-campaign-create"),
    path("csv-campaign/<int:pk>/", views.CSVCampaignDetailView.as_view(),
         name="csv-campaign-detail"),
    path("csv-campaign/<int:pk>/edit/", views.CSVCampaignUpdateView.as_view(),
         name="csv-campaign-edit"),
    path("csv-campaign/<int:pk>/validate/", views.CSVCampaignValidateView.as_view(),
         name="csv-campaign-validate"),
    path("csv-campaign/<int:pk>/validation-status/",
         views.CSVCampaignValidationStatusView.as_view(),
         name="csv-campaign-validation-status"),
    path("csv-campaign/<int:pk>/contacts/", views.CSVContactListView.as_view(),
         name="csv-campaign-contacts"),
    path("csv-campaign/<int:pk>/execute/", views.CSVCampaignExecuteView.as_view(),
         name="csv-campaign-execute"),
]
```

### 8. Admin

```python
# apps/campaigns/admin.py

@admin.register(models.CSVBasedCampaign)
class CSVBasedCampaignAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'status', 'validation_status',
        'total_contacts', 'valid_contacts', 'execution_date', 'created'
    ]
    list_filter = ['status', 'validation_status', 'channel', 'created']
    search_fields = ['name', 'description']
    readonly_fields = [
        'validation_status', 'validation_result', 'validated_at',
        'total_contacts', 'valid_contacts', 'invalid_contacts',
        'total_target_amount', 'created', 'modified'
    ]

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'contacts_file')
        }),
        ('Validation', {
            'fields': (
                'validation_status', 'validated_at',
                'total_contacts', 'valid_contacts', 'invalid_contacts',
                'validation_result'
            )
        }),
        ('Configuration', {
            'fields': ('execution_date', 'channel', 'use_payment_link')
        }),
        # ... más fieldsets
    )

@admin.register(models.CSVContact)
class CSVContactAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 'campaign', 'custom_amount',
        'is_valid', 'row_number', 'linked_partner'
    ]
    list_filter = ['is_valid', 'campaign']
    search_fields = ['full_name', 'email', 'phone', 'document_number']
    readonly_fields = ['validation_errors', 'row_number']
```

## Formato Esperado del CSV/Excel

### Columnas Requeridas (orden flexible)

```csv
nombre_completo,email,telefono,monto,documento
Juan Pérez,juan@email.com,987654321,150.50,12345678
María García,,965432187,200.00,87654321
Pedro López,pedro@email.com,,100.00,
```

### Columnas Opcionales

- `documento`: DNI, RUC, etc.
- `direccion`: Dirección del contacto
- `notas`: Notas adicionales
- Cualquier otra columna se guarda en `additional_data`

### Reglas de Validación

1. **nombre_completo**: Requerido, máx 200 caracteres
2. **email** o **telefono**: Al menos uno requerido
3. **monto**: Requerido, > 0, formato decimal válido
4. **email**: Formato válido si está presente
5. **telefono**: Solo dígitos y símbolos permitidos (+, -, espacios)

## Migración de Datos Existentes

### Estrategia

Como estamos refactorizando Campaign a GroupBasedCampaign:

```python
# Crear migración de datos

def migrate_existing_campaigns(apps, schema_editor):
    """
    Migra campañas existentes al nuevo modelo GroupBasedCampaign.
    """
    OldCampaign = apps.get_model('campaigns', 'Campaign')
    GroupBasedCampaign = apps.get_model('campaigns', 'GroupBasedCampaign')

    for old_campaign in OldCampaign.objects.all():
        GroupBasedCampaign.objects.create(
            # Copiar todos los campos relevantes
            name=old_campaign.name,
            description=old_campaign.description,
            group=old_campaign.group,
            # ... todos los campos
        )
```

## Plan de Implementación Sugerido

### Fase 1: Modelos y Migraciones (Prioridad ALTA)
1. Crear BaseCampaign abstracto
2. Crear CSVBasedCampaign
3. Crear CSVContact
4. Refactorizar Campaign a GroupBasedCampaign
5. Actualizar ValidationStatus en choices.py
6. Crear migraciones de base de datos
7. Migración de datos existentes

### Fase 2: Servicios (Prioridad ALTA)
1. Implementar CSVValidationService
2. Implementar CSVCampaignNotificationService
3. Actualizar servicios existentes para soportar ambos tipos

### Fase 3: Tasks de Celery (Prioridad ALTA)
1. Implementar validate_csv_campaign
2. Implementar process_csv_campaign_notifications
3. Actualizar tasks existentes

### Fase 4: Forms y Views (Prioridad MEDIA)
1. Crear CSVBasedCampaignForm
2. Implementar views CRUD para CSV campaigns
3. Implementar views de validación
4. Actualizar views existentes

### Fase 5: Admin y URLs (Prioridad MEDIA)
1. Configurar admin para nuevos modelos
2. Actualizar URLs
3. Actualizar permisos

### Fase 6: Templates (Prioridad BAJA)
1. Crear templates para campañas CSV
2. Crear template para vista de contactos
3. Actualizar templates existentes si es necesario

### Fase 7: Testing (Prioridad ALTA - CONTINUA)
1. Tests unitarios para servicios
2. Tests de integración para tasks
3. Tests de forms y validaciones
4. Tests end-to-end

## Archivos a Crear/Modificar

### Crear
- `apps/campaigns/services/csv_validation.py`
- `apps/campaigns/services/csv_notification.py`
- `apps/campaigns/tests/test_csv_validation.py`
- `apps/campaigns/tests/test_csv_campaign.py`
- `apps/campaigns/tests/fixtures/sample_contacts.csv`
- `apps/campaigns/tests/fixtures/sample_contacts.xlsx`
- `templates/campaigns/csv_campaign/*.html`

### Modificar
- `apps/campaigns/models.py` (refactorización mayor)
- `apps/campaigns/choices.py` (agregar ValidationStatus)
- `apps/campaigns/services.py` (actualizar servicios existentes)
- `apps/campaigns/tasks.py` (agregar nuevos tasks)
- `apps/campaigns/forms.py` (agregar nuevos forms)
- `apps/campaigns/views.py` (agregar nuevas views)
- `apps/campaigns/urls.py` (agregar nuevas URLs)
- `apps/campaigns/admin.py` (agregar nuevos admins)

## Consideraciones Importantes

1. **Manejo de Archivos Grandes**: Implementar lectura por chunks si el archivo es muy grande
2. **Validación Asíncrona**: Siempre usar Celery para validación, no en request
3. **Seguridad**: Validar extensiones de archivo, tamaño máximo, sanitizar inputs
4. **Performance**: Usar bulk_create para CSVContact, select_related/prefetch_related
5. **Logging**: Agregar logging detallado en servicios y tasks
6. **Transacciones**: Usar atomic() para operaciones críticas
7. **Backwards Compatibility**: Asegurar que el código existente siga funcionando
8. **Notificaciones GenericForeignKey**: Actualizar modelo si es necesario para soportar ambos tipos

## Preguntas a Resolver Durante Implementación

1. ¿Permitir re-validación de archivos ya validados?
2. ¿Qué hacer con CSVContacts cuando se elimina la campaña? (CASCADE confirmado)
3. ¿Permitir edición de contactos individuales post-validación?
4. ¿Implementar vista de previsualización antes de validar?
5. ¿Agregar opción de descarga de reporte de validación?

## Resultado Esperado

Al finalizar, el sistema debe:
- ✅ Soportar ambos tipos de campañas (Groups y CSV)
- ✅ Permitir carga de CSV y Excel
- ✅ Validar datos antes de ejecución
- ✅ Crear notificaciones con montos personalizados
- ✅ Mantener toda funcionalidad existente
- ✅ Tener cobertura de tests >80%
- ✅ Documentación completa en código

---

## Nota Final para el Agente

Este es un feature crítico y complejo. Por favor:
- Seguir el plan de implementación por fases
- Hacer commits atómicos y bien documentados
- Escribir tests antes o junto con el código (TDD recomendado)
- Documentar decisiones importantes en docstrings
- Usar type hints en Python
- Seguir PEP 8 y convenciones del proyecto existente
- Pedir clarificaciones si algo no está claro
- Priorizar calidad sobre velocidad
