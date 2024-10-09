from django import template

register = template.Library()


class BlockNotOverriddenError(NotImplementedError):
    pass


@register.simple_tag
def ensure_overridden():
    raise BlockNotOverriddenError
