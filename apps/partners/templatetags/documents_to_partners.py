from django import template

register = template.Library()


@register.simple_tag
def get_document_type_choices_to_partners():
    """Return active document types categorized under 'Partner'."""
    return ""
