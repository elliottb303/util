__author__ = 'ebmacbp'
from sqlobject import *

class Original(SQLObject):
    name = StringCol()
    conversion_date = StringCol()
    path = StringCol()
    transformed_to = MultipleJoin('Output')

class Output(SQLObject):
    name = StringCol()
    path = StringCol()
    format = StringCol()
    original = ForeignKey('Original')
