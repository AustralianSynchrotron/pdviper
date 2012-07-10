from traits.api import HasTraits
from traitsui.api import Group


class HasTraitsGroup(HasTraits):
    def traits_group(self, object=None, **kw):
        group_names = self.trait_views(Group)
        groups = [ self.trait_view(name) for name in group_names ]
        group = Group(*groups, object='object.' + object if object is not None else 'object', **kw)
        return group

