'''
Roles defined for the system. We explicitly do not want the complexity
of ACLs, roles, groups, etc. We plan four levels, including later a
school/district-level one.

We create the enum for roles like this to make everything
a string and thus, it is all json serializable. Starting in
Python 3.11, there is an easier way to do this.
`ROLES = enum.StrEnum("ROLES", names=('STUDENT', 'TEACHER', 'ADMIN'))`
'''
class ROLES:
    pass
possible_roles = ['STUDENT', 'TEACHER', 'ADMIN']
[setattr(ROLES, role, role) for role in possible_roles]
