from django import template

register = template.Library()

# register.filter('modify_field_class', modify_field_class)


@register.filter
def field_type(bound_field):
    """
    field -> <input type="text" name="title">, widget(PasswordInput[__class__]) and others
    """
    print(bound_field.field.widget.__class__.__name__)
    return bound_field.field.widget.__class__.__name__


@register.filter
def field_type(bound_field):
    """
    field -> <input type="text" name="title">, widget(PasswordInput[__class__]) and others
    """
    return bound_field.field.widget.__class__.__name__


@register.filter
def modify_field_class(bound_field):
    css_class = ''
    if field_type(bound_field) == 'ClearableFileInput':
        return css_class
    if bound_field.form.is_bound:
        """
        bound_field -> field(<input type="text" name="title">) plus help_text, form object, errors and others
        """
        if bound_field.errors:
            css_class = 'has-error'
        elif field_type(bound_field) != 'PasswordInput':
            """
            If field type is not a passwordinput
            """
            css_class = 'has-success'
    return 'form-control {}'.format(css_class)


@register.filter
def modify_field_div_class(bound_field):
    css_class = ''
    if bound_field.form.is_bound:
        if bound_field.errors:
            css_class += ' has-error'
        else:
            css_class += ' has-success'
    if field_type(bound_field) == 'ClearableFileInput':
        css_class = ''
    if field_type(bound_field) == 'CheckboxInput':
        css_class = ''
    else:
        css_class += ' form-group'
    return css_class


@register.filter
def modify_label_tag_name(bound_field):
    label = bound_field.label
    label_str = bound_field.label
    label = label.split('/')
    return '<label for="id_' + label_str + '">' + label[4] + '</label>'
