
from types import StringType
from Products.Archetypes.Widget import TypesWidget
from Products.generator.widget import macrowidget
from DateTime import DateTime

from Products.Archetypes.Registry import registerWidget
from Products.Archetypes.Renderer import renderer
from Products.Archetypes.OrderedListOfTuples import OrderedListOfTuples
from Products.Archetypes.utils import generateId

_marker=[]

class ContainerWidget(TypesWidget):
    _properties = TypesWidget._properties.copy()
    _properties.update({
        'macro' : "widgets/container_fields",
        'size' : '30',
        'maxlength' : '255',
        })


    def process_form(self, instance, field, form, empty_marker=_marker):
        field_name=field.getName()
        values=field.getObjectItems(instance)
        if hasattr(field, 'getObjects'):
            for obj in field.getObjects(instance):
                obj.processForm(data=1, metadata=0, REQUEST=None, values=form)
        form_add_object=form.get('form_add_object', None)
        form_delete_objects=form.get('form_delete_objects', None)
        form_rename_objects=form.get('form_rename_objects', None)
        form_move_objects_up=form.get('form_move_objects_up', None)
        form_move_objects_down=form.get('form_move_objects_down', None)
        form_move_objects_top=form.get('form_move_objects_top', None)
        form_move_objects_bottom=form.get('form_move_objects_bottom', None)

        form_delete_object=form.get('form_delete_object', None)
        form_move_object_up=form.get('form_move_object_up', None)
        form_move_object_down=form.get('form_move_object_down', None)
        form_move_object_top=form.get('form_move_object_top', None)
        form_move_object_bottom=form.get('form_move_object_bottom', None)


        form_add_object_id=form.get('form_add_object_id', None)
        form_object_ids=form.get('form_object_ids', None)

        if form_add_object and hasattr(form_add_object, field_name):
            if form_add_object_id and form_add_object_id.has_key(field_name):
                id=form_add_object_id.get(field_name)
                id, obj=field.createObject(instance, id)
                return values+((id,obj),), {}

        elif form_rename_objects and hasattr(form_rename_objects, field_name):
            if form_add_object_id and form_add_object_id.has_key(field_name):
                raise "ToDo"

        elif form_delete_objects and hasattr(form_delete_objects, field_name):
            if form_object_ids:
                deleted_object_ids=form_object_ids.get(field_name, ())
                if type(deleted_object_ids) is StringType: deleted_object_ids=(deleted_object_ids,)
                if deleted_object_ids:
                    new_values=[]
                    for id, obj in values:
                        if id not in deleted_object_ids:
                            new_values.append((id, obj))
                    return new_values, {'deleted_object_ids': deleted_object_ids}

        elif form_move_objects_up and hasattr(form_move_objects_up, field_name):
            if form_object_ids:
                object_ids=form_object_ids.get(field_name, ())
                values=OrderedListOfTuples(values)
                values.move_objects_up(object_ids, 1)
                return values.getList(), {}

        elif form_move_objects_down and hasattr(form_move_objects_down, field_name):
            if form_object_ids:
                object_ids=form_object_ids.get(field_name, ())
                values=OrderedListOfTuples(values)
                values.move_objects_down(object_ids, 1)
                return values.getList(), {}

        elif form_move_objects_top and hasattr(form_move_objects_top, field_name):
            if form_object_ids:
                object_ids=form_object_ids.get(field_name, ())
                values=OrderedListOfTuples(values)
                values.move_objects_to_top(object_ids)
                return values.getList(), {}

        elif form_move_objects_bottom and hasattr(form_move_objects_bottom, field_name):
            if form_object_ids:
                object_ids=form_object_ids.get(field_name, ())
                values=OrderedListOfTuples(values)
                values.move_objects_to_bottom(object_ids)
                return values.getList(), {}

        #Single Object Changes
        elif form_delete_object and hasattr(form_delete_object, field_name):
            id=getattr(form_delete_object, field_name, None)
            if id is not None:
                deleted_object_ids=(id,)
                new_values=[]
                for id, obj in values:
                    if id not in deleted_object_ids:
                        new_values.append((id, obj))
                return new_values, {'deleted_object_ids': deleted_object_ids}

        elif form_move_object_up and hasattr(form_move_object_up, field_name):
            id=getattr(form_move_object_up, field_name, None)
            if id is not None:
                object_ids=(id,)
                values=OrderedListOfTuples(values)
                values.move_objects_up(object_ids, 1)
                return values.getList(), {}

        elif form_move_object_down and hasattr(form_move_object_down, field_name):
            id=getattr(form_move_object_down, field_name, None)
            if id is not None:
                object_ids=(id,)
                values=OrderedListOfTuples(values)
                values.move_objects_down(object_ids, 1)
                return values.getList(), {}

        elif form_move_object_top and hasattr(form_move_object_top, field_name):
            id=getattr(form_move_object_top, field_name, None)
            if id is not None:
                object_ids=(id,)
                values=OrderedListOfTuples(values)
                values.move_objects_to_top(object_ids)
                return values.getList(), {}

        elif form_move_object_bottom and hasattr(form_move_object_bottom, field_name):
            id=getattr(form_move_object_bottom, field_name, None)
            if id is not None:
                object_ids=(id,)
                values=OrderedListOfTuples(values)
                values.move_objects_to_bottom(object_ids)
                return values.getList(), {}

        return empty_marker


registerWidget(ContainerWidget,
               title='ContainerWidget',
               description="Renders a list of Container sub objects and let's the user change them.",
               used_for=('Products.Archetypes.ContainerField.ContainerField',)
               )

