# Sistema de Pagos Genérico

Este documento describe el nuevo sistema de pagos genérico que permite manejar diferentes tipos de conceptos de pago de manera escalable y flexible.

## Arquitectura

El nuevo sistema está compuesto por:

1. **Payment**: Modelo genérico que representa cualquier tipo de pago
2. **PaymentConcept**: Enum que define los diferentes tipos de conceptos de pago
3. **PaymentConceptAllocation**: Modelo que relaciona pagos con conceptos específicos
4. **QuerySets** (`querysets.py`): Consultas reutilizables y optimizadas
5. **Managers** (`managers.py`): Interfaz de alto nivel para operaciones comunes
6. **Utils** (`utils.py`): Funciones auxiliares para operaciones complejas

## Estructura de Archivos

### `models.py`
Contiene los modelos principales:
- `Payment`: Modelo genérico de pagos
- `PaymentConcept`: Choices para tipos de pago
- `PaymentConceptAllocation`: Relaciones pago-concepto

### `querysets.py`
Define QuerySets reutilizables:
- `PaymentQuerySet`: Filtros y consultas para pagos
- `PaymentConceptAllocationQuerySet`: Filtros para asignaciones

### `managers.py`
Managers que utilizan los QuerySets:
- `PaymentManager`: Operaciones de alto nivel para pagos
- `PaymentConceptAllocationManager`: Operaciones para asignaciones

### `utils.py`
Funciones auxiliares para operaciones complejas:
- Procesamiento de pagos múltiples
- División automática de pagos
- Asignación inteligente de conceptos

### `choices.py`
Definiciones de choices:
- `PaymentStatus`: Estados de pago
- `PaymentMethod`: Métodos de pago
- `AllocationStatus`: Estados de asignación

## Conceptos de Pago Soportados

- **INSTALLMENT**: Cuotas de préstamos
- **CONTRIBUTION**: Aportes
- **SOCIAL_SECURITY**: Previsión social
- **PENALTY**: Multas
- **LATE_FEE**: Cargos por mora
- **INTEREST**: Intereses
- **OTHER**: Otros conceptos

## Ejemplos de Uso

### 1. Crear un Pago para una Cuota

```python
from apps.payments.models import Payment
from apps.credits.models import Installment

# Obtener la cuota
installment = Installment.objects.get(id=1)

# Crear el pago
payment = Payment.create_for_installment(
    installment=installment,
    payment_number="INST-2024-001"
)

# Registrar el pago
payment.make_payment(
    amount=installment.installment_amount,
    payment_method="BANK_TRANSFER",
    reference_number="TXN-123456",
    notes="Pago completo de la cuota"
)

# Asignar el pago a la cuota
allocation = payment.allocate_to_concept(installment)
```

### 2. Pago Parcial de una Cuota

```python
# Crear pago parcial
payment = Payment.create_for_installment(installment)

# Registrar pago parcial (50% del monto)
partial_amount = installment.installment_amount / 2
payment.make_payment(
    amount=partial_amount,
    payment_method="CASH"
)

# Asignar el pago parcial
payment.allocate_to_concept(
    concept_object=installment,
    amount=partial_amount,
    notes="Pago parcial del 50%"
)
```

### 3. Pago que Cubre Múltiples Cuotas

```python
from apps.payments.utils import process_payment_for_multiple_concepts, split_payment_across_installments

# Obtener cuotas pendientes
pending_installments = Installment.objects.filter(
    credit__partner=partner,
    status="PENDING"
).order_by('due_date')[:3]

# Dividir el pago entre las cuotas
payment_amount = Decimal('1500.00')
concepts_data = split_payment_across_installments(
    installments=pending_installments,
    payment_amount=payment_amount,
    strategy="chronological"  # Pagar cuotas más antiguas primero
)

# Procesar el pago
payment, allocations = process_payment_for_multiple_concepts(
    partner=partner,
    payment_amount=payment_amount,
    concepts_data=concepts_data,
    payment_method="BANK_TRANSFER",
    reference_number="TXN-789012",
    notes="Pago múltiples cuotas"
)
```

### 4. Crear Pago para Obligación de Cumplimiento

```python
from apps.compliance.models import Contribution
from apps.payments.models import PaymentConcept

# Obtener la contribución
contribution = Contribution.objects.get(id=1)

# Crear el pago
payment = Payment.create_for_compliance_obligation(
    obligation=contribution,
    concept=PaymentConcept.CONTRIBUTION
)

# Registrar y asignar el pago
payment.make_payment(amount=contribution.amount)
payment.allocate_to_concept(contribution)
```

### 5. Pago Automático con Mejor Coincidencia

```python
from apps.payments.utils import auto_allocate_payment_to_best_match

# Crear un pago genérico
payment = Payment.objects.create(
    partner=partner,
    concept=PaymentConcept.INSTALLMENT,
    payment_number="AUTO-001",
    paid_amount=Decimal('500.00'),
    status=choices.PaymentStatus.PAID
)

# Obtener conceptos disponibles para asignar
available_installments = Installment.objects.filter(
    credit__partner=partner,
    status="PENDING"
)

# Asignación automática basada en reglas de negocio
allocation = auto_allocate_payment_to_best_match(
    payment=payment,
    available_concepts=available_installments
)
```

### 6. Consultas con el Manager Personalizado

```python
# Obtener pagos vencidos
overdue_payments = Payment.objects.overdue()

# Pagos por concepto
installment_payments = Payment.objects.for_installments()
compliance_payments = Payment.objects.for_compliance()

# Resumen por concepto
summary = Payment.objects.summary_by_concept()

# Resumen por socio
partner_summary = Payment.objects.summary_by_partner(partner)

# Pagos en un período específico
from datetime import date, timedelta
start_date = date.today() - timedelta(days=30)
end_date = date.today()

recent_payments = Payment.objects.paid_in_period(start_date, end_date)
```

### 7. Crear Pagos para Todas las Cuotas de un Crédito

```python
from apps.payments.utils import create_payment_schedule_from_installments

# Crear pagos para todas las cuotas de un crédito
credit = Credit.objects.get(id=1)
payments = create_payment_schedule_from_installments(credit)

print(f"Se crearon {len(payments)} pagos para el crédito")
```

### 8. Calcular Resumen de Pagos

```python
from apps.payments.utils import calculate_payment_summary

# Resumen completo del socio
summary = calculate_payment_summary(partner)

print(f"Total programado: ${summary['total_scheduled']}")
print(f"Total pagado: ${summary['total_paid']}")
print(f"Pagos vencidos: {summary['overdue_count']}")

# Por concepto
for concept, data in summary['by_concept'].items():
    print(f"{concept}: {data['count']} pagos, ${data['paid']} pagados")
```

## Implementación desde Cero

Este sistema de pagos genérico fue diseñado e implementado desde cero como una solución escalable y flexible. No requiere migración de datos ya que es la implementación inicial del sistema de pagos en la aplicación.

### Configuración Inicial

Para comenzar a usar el sistema, simplemente ejecuta las migraciones:

```bash
python manage.py makemigrations payments
python manage.py migrate
```

### Primeros Pasos

1. **Crear pagos para cuotas existentes**:
```python
from apps.payments.utils import create_payment_schedule_from_installments

# Para cada crédito existente, crear sus pagos correspondientes
for credit in Credit.objects.filter(status='ACTIVE'):
    payments = create_payment_schedule_from_installments(credit)
    print(f"Creados {len(payments)} pagos para crédito {credit.id}")
```

2. **Configurar pagos para obligaciones de cumplimiento**:
```python
from apps.payments.models import Payment, PaymentConcept

# Para contribuciones existentes
for contribution in Contribution.objects.filter(status='PENDING'):
    payment = Payment.create_for_compliance_obligation(
        obligation=contribution,
        concept=PaymentConcept.CONTRIBUTION
    )
```

## Ventajas del Sistema

1. **Genérico y Escalable**: Un solo modelo maneja todos los tipos de pago
2. **Flexibilidad**: Un pago puede cubrir múltiples conceptos o partes de conceptos
3. **Trazabilidad**: Seguimiento detallado de asignaciones de pagos
4. **Consultas Optimizadas**: Managers personalizados para operaciones comunes
5. **Extensibilidad**: Fácil agregar nuevos conceptos de pago
6. **Diseño Moderno**: Implementación desde cero con mejores prácticas

## API de Manager

### PaymentManager

- `for_partner(partner)`: Pagos de un socio específico
- `by_concept(concept)`: Pagos por tipo de concepto
- `overdue()`: Pagos vencidos
- `pending()`: Pagos pendientes
- `paid()`: Pagos completados
- `summary_by_concept()`: Resumen agrupado por concepto
- `summary_by_partner(partner)`: Resumen de un socio específico

### PaymentConceptAllocationManager

- `for_payment(payment)`: Asignaciones de un pago específico
- `for_concept_type(model_class)`: Asignaciones para un tipo de concepto
- `allocate_payment_to_concept()`: Asignar pago a concepto
- `summary_by_concept_type()`: Resumen por tipo de concepto

## Señales (Signals)

El sistema incluye señales que automáticamente:

1. **Actualizan el estado de cuotas** cuando se asignan pagos
2. **Calculan el balance pendiente de créditos** basado en pagos de cuotas
3. **Marcan créditos como completados** cuando están totalmente pagados
4. **Actualizan estados de obligaciones de cumplimiento** cuando están pagadas

## Consideraciones de Rendimiento

- Usar `select_related` y `prefetch_related` para consultas optimizadas
- Los managers incluyen índices para campos consultados frecuentemente
- Las consultas agregadas están optimizadas para reportes
