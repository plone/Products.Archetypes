class renderer:
    def render(self, field_name, mode, widget, instance, **kwargs):
        context = self.setupContext(field_name, mode, widget,
                                    instance, **kwargs)
            
        result = widget(mode, instance, context)
        context.endScope()
        return result

        
    def setupContext(self, field_name, mode, widget, instance,
                     **kwargs):
        return {}
    
    
