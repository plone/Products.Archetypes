class renderer:
    def render(self, field_name, mode, widget, instance=None, field=None, accessor=None, **kwargs):
        if field is None:
            field = instance.Schema()[field_name]

        if accessor is None:
            accessor = getattr(instance, field.accessor)

        context = self.setupContext(field_name, mode, widget,
                                    instance, field, accessor, **kwargs)

        result = widget(mode, instance, context)

        del context
        return result


    def setupContext(self, field_name, mode, widget, instance, field, accessor,
                     **kwargs):
        return {}


