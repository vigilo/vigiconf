# -*- coding: utf-8 -*-
# Copyright (C) 2018-2020 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>
"""
Cette classe contient des validateurs chargés de convertir et valider
les arguments des tests.
"""

from __future__ import unicode_literals

import re
import sys
import inspect
import textwrap
import operator

import collections
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from vigilo.vigiconf.lib.exceptions import ParsingError

from vigilo.common.gettext import translate
_ = translate(__name__)

__all__ = (
    'Validator',
    'String',
    'Bool',
    'Integer',
    'Float',
    'List',
    'Struct',
    'Enum',
    'Threshold',
    'Time',
    'Port',
    'arg',
    'str_types',
)


if sys.version_info[0] < 3:
    str_types = (str, unicode)
else:
    str_types = (str, bytes)


class Validator(object):
    """Base class for argument validators."""

    epytype = None
    errmsg = _("Invalid value for '%(arg)s': %(value)r")

    def convert(self, arg, value):
        """
        This method is called to convert the given value
        to the appropriate Python type.
        """
        raise NotImplementedError('Override this method in subclasses')

    def export(self):
        """
        This method is called to export the validator's metadata.
        """
        raise NotImplementedError('Override this method in subclasses')

    def raise_error(self, arg, value):
        raise ParsingError(self.errmsg % {'arg': arg, 'value': value})


class String(Validator):
    """
    A validator that expects a string as its input.

    >>> String().convert('arg1', 'foobar')
    u'foobar'
    >>> String().convert('arg1', ['foobar'])
    Traceback (most recent call last):
        ...
    ParsingError: Invalid value for 'arg1': [u'foobar']
    """

    epytype = 'C{str}'

    def __init__(self, placeholder=None, pattern=None):
        self.placeholder = placeholder
        self.pattern = pattern
        # Make sure the pattern is valid.
        if pattern:
            self.pattern_re = re.compile(pattern)
        else:
            self.pattern_re = None

    def convert(self, arg, value):
        if not isinstance(value, str_types):
            self.raise_error(arg, value)
        if self.pattern_re and not self.pattern_re.match(value):
            self.raise_error(arg, value)
        return value

    def export(self):
        res = {"type": "string"}
        if self.placeholder:
            res['placeholder'] = self.placeholder
        if self.pattern:
            res['pattern'] = self.pattern
        return res


class Bool(Validator):
    """
    A validator that expects a boolean as its input.

    >>> Bool().convert('arg1', 'true')
    True
    >>> Bool().convert('arg1', 'false')
    False
    >>> Bool().convert('arg1', ['false'])
    Traceback (most recent call last):
        ...
    ParsingError: Invalid value for 'arg1': [u'false']
    >>> Bool().convert('arg1', 'foobar')
    Traceback (most recent call last):
        ...
    ParsingError: Invalid value for 'arg1': u'foobar'
    """

    epytype = 'C{bool}'

    def convert(self, arg, value):
        if not isinstance(value, str_types):
            self.raise_error(arg, value)
        value = value.lower()
        if value in ('0', 'off', 'no', 'false'):
            return False
        if value in ('1', 'on', 'yes', 'true'):
            return True
        self.raise_error(arg, value)

    def export(self):
        return {"type": "bool"}


class Integer(Validator):
    """
    A validator that expects an integer as its input.
    A range of valid values can also be specified.

    >>> Integer().convert('arg1', '42')
    42
    >>> Integer().convert('arg1', 'foobar')
    Traceback (most recent call last):
        ...
    ParsingError: Invalid value for 'arg1': u'foobar'
    >>> Integer(min=0, max=100).convert('arg1', '100')
    100
    >>> Integer(min=0, max=100).convert('arg1', '101')
    Traceback (most recent call last):
        ...
    ParsingError: Invalid value for 'arg1': 101
    >>> Integer(min=0, max=100, max_incl=False).convert('arg1', '100')
    Traceback (most recent call last):
        ...
    ParsingError: Invalid value for 'arg1': 100
    """

    numeric_type = 'int'

    @property
    def epytype(self):
        return 'C{%s}' % self.numeric_type

    def __init__(self, min=None, min_incl=True, max=None, max_incl=True, step=None):
        if step is not None and \
            (not isinstance(step, (float, int)) or step <= 0):
            raise ValueError(_('Invalid step parameter: %r') % (step, ))

        self.min = min
        self.max = max
        self.min_incl = min_incl
        self.max_incl = max_incl
        self.min_cmp = operator.__ge__ if min_incl else operator.__gt__
        self.max_cmp = operator.__le__ if max_incl else operator.__lt__
        self.step = step

    def _convert(self, arg, value):
        try:
            return int(value)
        except ValueError:
            self.raise_error(arg, value)

    def convert(self, arg, value):
        try:
            value = self._convert(arg, value)
        except ValueError:
            self.raise_error(arg, value)

        if self.min is not None and not self.min_cmp(value, self.min):
            self.raise_error(arg, value)

        if self.max is not None and not self.max_cmp(value, self.max):
            self.raise_error(arg, value)

        if self.step is not None and value % self.step:
            self.raise_error(arg, value)

        return value

    def export(self):
        res = {"type": self.numeric_type}
        if self.min is not None:
            res.update({"min": self.min, "min_incl": self.min_incl})
        if self.max is not None:
            res.update({"max": self.max, "max_incl": self.max_incl})
        if self.step is not None:
            res["step"] = self.step
        return res


class Float(Integer):
    """
    A validator that expects a floating-point value as its input.
    A range of valid values can also be specified.


    >>> Float().convert('arg1', '4.0')
    4.0
    >>> Float().convert('arg1', 'foobar')
    Traceback (most recent call last):
        ...
    ParsingError: Invalid value for 'arg1': u'foobar'
    >>> Float(min=0, max=100).convert('arg1', '100')
    100.0
    >>> Float(min=0, max=100).convert('arg1', '101')
    Traceback (most recent call last):
        ...
    ParsingError: Invalid value for 'arg1': 101.0
    >>> Float(min=0, max=100, max_incl=False).convert('arg1', '100')
    Traceback (most recent call last):
        ...
    ParsingError: Invalid value for 'arg1': 100.0
    """

    numeric_type = 'float'

    def _convert(self, arg, value):
        try:
            return float(value)
        except ValueError:
            self.raise_error(arg, value)


class Port(Integer):
    """
    A specific integer type representing network ports (eg. TCP/UDP ports).
    """
    def __init__(self):
        super(Port, self).__init__(min=0, max=65535)


class List(Validator):
    """
    A validator that expects a list of values as its input.
    The number of elements in the list as well as their type
    can be further restricted. However, it is not possible
    to constrain the items' type based on their position
    inside the list. See L{Struct} for that use case.

    >>> List(types=String).convert('arg1',  () )
    ()
    >>> List().convert('arg1', 'foobar')
    Traceback (most recent call last):
        ...
    ValueError: At least one type must be given
    >>> List(min=2, types=String).convert('arg1',  ('foo', ) )
    Traceback (most recent call last):
        ...
    ParsingError: Invalid value for 'arg1': (u'foo',)
    >>> List(max=1, types=String).convert('arg1',  ('foo', 'bar') )
    Traceback (most recent call last):
        ...
    ParsingError: Invalid value for 'arg1': (u'foo', u'bar')
    >>> List(types=Integer).convert('arg1',  ('23', '42') )
    (23, 42)
    >>> List(types=Integer).convert('arg1',  ('foo', ) )
    Traceback (most recent call last):
        ...
    ParsingError: Invalid value for 'arg1': u'foo'
    """

    epytype = 'C{tuple}'

    def __init__(self, min=0, max=None, types=None, step=1, size=None):
        if not isinstance(step, int) or step <= 0:
            raise ValueError(_('Invalid step parameter: %r') % (step, ))

        if types is None:
            types = []
        if not isinstance(types, collections.Iterable):
            types = [types]
        types = [typ() if isinstance(typ, type) else typ
                 for typ in types]
        if not types:
            raise ValueError(_('At least one type must be given'))

        if size is not None:
            min = size
            max = size

        self.types = types
        self.min = min
        self.max = max
        self.step = step

    def convert(self, arg, value):
        if not isinstance(value, (tuple, list)):
            self.raise_error(arg, value)

        vlen = len(value)
        if vlen < self.min:
            self.raise_error(arg, value)
        if self.max is not None and vlen > self.max:
            self.raise_error(arg, value)
        if vlen % self.step:
            self.raise_error(arg, value)

        res = []
        for item in value:
            for typ in self.types:
                try:
                    res.append(typ.convert(arg, item))
                    break
                except:
                    pass
            else:
                self.raise_error(arg, value)
        return tuple(res)

    def export(self):
        res = {"type": "list"}
        if self.min is not None:
            res['min'] = self.min
        if self.max is not None:
            res['max'] = self.max
        if self.types is not None:
            res['types'] = [ typ.export() for typ in self.types ]
        if self.step != 1:
            res['step'] = self.step
        return res


class Struct(Validator):
    """
    A validator that expects a fixed-size list of values as its input.
    The types of the elements in the list can then be restricted.

    >>> Struct().convert('arg1',  () )
    ()
    >>> Struct(Integer).convert('arg1',  ('42', ) )
    (42,)
    >>> Struct(Integer, (Integer, String)).convert('arg1',  ('42', '23') )
    (42, 23)
    >>> Struct(Integer, (Integer, String)).convert('arg1',  ('42', 'foo') )
    (42, u'foo')
    >>> Struct().convert('arg1', 'foobar')
    Traceback (most recent call last):
        ...
    ParsingError: Invalid value for 'arg1': u'foobar'
    >>> Struct().convert('arg1',  ('foo', ) )
    Traceback (most recent call last):
        ...
    ParsingError: Invalid value for 'arg1': (u'foo',)
    >>> Struct(String).convert('arg1',  () )
    Traceback (most recent call last):
        ...
    ParsingError: Invalid value for 'arg1': ()
    >>> Struct(Integer).convert('arg1',  ('foo', ) )
    Traceback (most recent call last):
        ...
    ParsingError: Invalid value for 'arg1': (u'foo',)
    """

    epytype = 'C{tuple}'

    def __init__(self, *types):
        validators = []
        for typ in types:
            if not isinstance(typ, collections.Iterable):
                typ = [typ]
            typ = [t() if isinstance(t, type) else t for t in typ]
            validators.append(typ)
        self.types = validators

    def convert(self, arg, value):
        if not isinstance(value, tuple):
            self.raise_error(arg, value)
        if len(value) != len(self.types):
            self.raise_error(arg, value)

        res = []
        for index, item in enumerate(value):
            for typ in self.types[index]:
                try:
                    res.append(typ.convert(arg, item))
                    break
                except:
                    pass
            else:
                self.raise_error(arg, value)
        return tuple(res)

    def export(self):
        res = {"type": "struct"}
        if self.types is not None:
            types = []
            for typ in self.types:
                types.append([ t.export() for t in typ ])
            res['types'] = types
        return res


class Threshold(Validator):
    """
    A validator that expects a Nagios threshold specification
    as its input.

    >>> Threshold().convert('arg1', '10')
    u'10'
    >>> Threshold().convert('arg1', '10:')
    u'10:'
    >>> Threshold().convert('arg1', '~:10')
    u'~:10'
    >>> Threshold().convert('arg1', '10:20')
    u'10:20'
    >>> Threshold().convert('arg1', '@10:20')
    u'@10:20'
    >>> Threshold().convert('arg1', '@')
    Traceback (most recent call last):
        ...
    ParsingError: Invalid value for 'arg1': u'@'
    """

    epytype = 'C{str}'

    def convert(self, arg, value):
        value = "%s" % value
        if value == '':
            return value

        tmp = value
        if tmp.startswith('@'):
            tmp = tmp[1:]
        start, sep_, end = tmp.partition(':')

        if start is not None and start != '~':
            try:
                start = float(start)
            except ValueError:
                self.raise_error(arg, value)

        if end is not None and end != '':
            try:
                end = float(end)
            except ValueError:
                self.raise_error(arg, value)

        return value

    def export(self):
        return {'type': 'threshold'}


class Enum(Validator):
    """
    A validator that restricts valid values
    based on a dictionary of possible choices.

    >>> Enum(blue=1, red=2, yellow=3).convert('arg1', 'yellow')
    u'yellow'
    >>> Enum(blue=1, red=2, yellow=3).convert('arg1', 'green')
    Traceback (most recent call last):
        ...
    ParsingError: Invalid value for 'arg1': u'green'
    >>> Enum(yes="I agree", no="I disagree").convert('arg1', 'yes')
    u'yes'
    >>> Enum(yes="I agree", no="I disagree").convert('arg1', 'maybe')
    Traceback (most recent call last):
        ...
    ParsingError: Invalid value for 'arg1': u'maybe'
    """

    epytype = 'C{str}'

    def __init__(self, choices=None, **kw_args_):
        self.choices = OrderedDict(choices or {})
        self.choices.update(kw_args_)

    def convert(self, arg, value):
        if not value in self.choices:
            self.raise_error(arg, value)
        return value

    def export(self):
        return {'type': 'enum', 'choices': self.choices}


class Time(Validator):
    """
    A validator that expects a time in 24h format.

    >>> Time().convert('arg1', '13:37')
    u'13:37'
    >>> Time().convert('arg1', '0:00')
    u'00:00'
    >>> Time().convert('arg1', 'abc')
    Traceback (most recent call last):
        ...
    ParsingError: Invalid value for 'arg1': u'abc'
    >>> Time().convert('arg1', '0:0')
    Traceback (most recent call last):
        ...
    ParsingError: Invalid value for 'arg1': u'0:0'
    >>> Time().convert('arg1', '0')
    Traceback (most recent call last):
        ...
    ParsingError: Invalid value for 'arg1': u'0'
    """

    epytype = 'C{str}'

    def convert(self, arg, value):
        hours, sep_, minutes = value.partition(':')
        if len(minutes) != 2:
            self.raise_error(arg, value)

        try:
            hours = int(hours)
            minutes = int(minutes)
        except ValueError:
            self.raise_error(arg, value)

        if not (0 <= hours <= 23):
            self.raise_error(arg, value)
        if not (0 <= minutes <= 59):
            self.raise_error(arg, value)

        return "%02d:%02d" % (hours, minutes)

    def export(self):
        return {'type': 'time'}


class arg(object):
    """
    Decorator for a method's arguments.

    This decorator can be used to describe each argument for a method,
    including detailed information on valid values.
    """

    def __init__(self, arg_name, validator=String, display_name=None, desc=''):
        """
        @param name:        Name of the argument.
        @param validator:   Validator used to validate/convert this argument.
        @param desc:        Description for this argument.
        """
        self.name = arg_name
        self.display_name = display_name or arg_name.capitalize()
        if isinstance(validator, type):
            validator = validator()
        if not isinstance(validator, Validator):
            raise ValueError(validator)
        self.validator = validator
        self.desc = desc

    def __call__(self, func):
        # If the function has not been wrapped yet, prepare it
        wrapped = hasattr(func, 'args')
        if not wrapped:
            func.args = OrderedDict()

        # Retrieve known arguments for the test
        known_args = getattr(func, 'known_args', None)
        if known_args is None:
            known_args = set(inspect.getargspec(func).args[1:])

        # Make sure the argument we are describing actually exists
        if self.name not in known_args:
            raise ValueError(_('Unknown argument for '
                               '%(cls)s.%(method)s: "%(arg)s"') % {
                                'cls': func.__class__.__name__,
                                'method': func.__name__,
                                'arg': self.name,
                             })


        if self.name in func.args:
            raise ValueError('Argument defined multiple times for '
                             '%(cls)s.%(method)s: "%(arg)s"' % {
                                'cls': func.__class__.__name__,
                                'method': func.__name__,
                                'arg': self.name,
                             })

        # Store information about this argument,
        # and prepare a patch for the method's documentation.
        func.args[self.name] = (self.validator, self.display_name, self.desc)
        doc = "@param %s: %s\n" % (self.name, self.desc or self.display_name)
        if self.validator.epytype:
            doc += "@type %s: %s\n" % (self.name, self.validator.epytype)

        # The method is already wrapped, patch the documentation
        # and return the wrapper.
        if wrapped:
            func.__doc__ += doc
            return func

        # Create a new wrapper for the method, that will be called
        # before the original method to validate the arguments.
        def wrapper(instance, **kw):
            new_args = {}

            if set(func.args.keys()) != known_args:
                raise RuntimeError(_("Not all arguments documented "
                                     "in %(cls)s.%(method)s") % {
                                        'cls': func.__class__.__name__,
                                        'method': func.__name__,
                                    })

            for name in kw:
                if name not in func.args:
                    new_args[name] = kw[name]
                    continue

                validator = func.args[name][0]
                try:
                    new_args[name] = validator.convert(name, kw[name])
                except ParsingError as e:
                    raise ParsingError(_('Error in test "%(test)s" on host "%(host)s": %(error)s') % {
                                             'test': instance.get_fullname(),
                                             'host': instance.host.name,
                                             'error': unicode(e),
                                         })

            # Make sure the method is bound to the instance.
            bound = func.__get__(instance)
            return bound(**new_args)

        # Retrieve or create documentation about the method and de-indent it.
        wrapper.__doc__ = textwrap.dedent(getattr(func, '__doc__') or '' + '\n')

        # Update the wrapper's documentation and arguments' descriptors,
        # before returning it.
        wrapper.__doc__ += doc
        wrapper.args = func.args
        wrapper.known_args = known_args
        wrapper.wrapped_func = func
        return wrapper
