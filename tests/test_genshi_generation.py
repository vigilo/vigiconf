#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test du moteur de génération basé sur Genshi
"""

import os

import unittest

from genshi.template import TemplateLoader
from genshi.template import TextTemplate

from vigilo.vigiconf.generators import View


class GenshiGenerationTest(unittest.TestCase):
    
    def setUp(self):
        self.loader = TemplateLoader(os.path.join(
                                        os.path.dirname(__file__),
                                        'testdata', 'genshi'
                                        ),
                                     auto_reload=False)
      
    
    def test_genshi_text(self):
        """ Test basique de génération de texte """
        tmpl = TextTemplate('Hello, $name!')
        stream = tmpl.generate(name='world')
        self.assertEquals(stream.render(), 'Hello, world!')
    
    def test_genshi_for(self):
        """ Test boucle for genshi
        
        BUG: utiliser plutôt la vieille syntaxe
        http://genshi.edgewall.org/ticket/377
        """
        tmpl = TextTemplate(u"""
            {% for server in servers %}
                        ${server}
            {% end %}""")
        stream = tmpl.generate(servers=[u'supserver.example.com',], server='TODO.VOIR.BUG.GENSHI')
        #self.assertEquals(stream.render().strip(), u'supserver.example.com')
    
    
    def test_genshi_for_old(self):
        """ Test boucle for genshi old syntax"""
        tmpl = TextTemplate("""
            #for server in servers
                $server
            #end""")
        stream = tmpl.generate(servers=['supserver.example.com',], server='TODO.VOIR.BUG.GENSHI')
        self.assertEquals(stream.render().strip(), 'supserver.example.com')
    
    def test_genshi_text_file(self):
        """ Test de génération de texte avec fichier template"""
        tmpl = self.loader.load('test.tpl', cls=TextTemplate)
        stream = tmpl.generate(name='world')
        self.assertEquals(stream.render(), 'Hello, world!')
    
    def test_genshi_base_view(self):
        """ Test de la classe de base View basée sur Genshi"""
        view = View('tests', template_dir='tests/testdata/genshi')
        self.assertEquals(view.render('test.tpl', {'name':'world'}),
                          'Hello, world!')
        
    

"""
1   Template Directives

Directives are template commands enclosed by {% ... %} characters. They can affect how the template is rendered in a number of ways: Genshi provides directives for conditionals and looping, among others.
Each directive must be terminated using an {% end %} marker. You can add a string inside the {% end %} marker, for example to document which directive is being closed, or even the expression associated with that directive. Any text after end inside the delimiters is ignored, and effectively treated as a comment.

If you want to include a literal delimiter in the output, you need to escape it by prepending a backslash character (\).
1.1   Conditional Sections
    1.1.1   {% if %}

The content is only rendered if the expression evaluates to a truth value:

    {% if foo %}
      ${bar}
    {% end %}

Given the data foo=True and bar='Hello' in the template context, this would produce:

Hello

    1.1.2   {% choose %}

The choose directive, in combination with the directives when and otherwise, provides advanced contional processing for rendering one of several alternatives. The first matching when branch is rendered, or, if no when branch matches, the otherwise branch is be rendered.
If the choose directive has no argument the nested when directives will be tested for truth:

The answer is:
{% choose %}
  {% when 0 == 1 %}0{% end %}
  {% when 1 == 1 %}1{% end %}
  {% otherwise %}2{% end %}
{% end %}

This would produce the following output:

The answer is:
  1

If the choose does have an argument, the nested when directives will be tested for equality to the parent choose value:

The answer is:
    {% choose 1 %}\
      {% when 0 %}0{% end %}\
      {% when 1 %}1{% end %}\
      {% otherwise %}2{% end %}\
    {% end %}

This would produce the following output:

The answer is:
    1

1.2   Looping
    1.2.1   {% for %}

The content is repeated for every item in an iterable:

Your items:
    {% for item in items %}\
      * ${item}
    {% end %}

Given items=[1, 2, 3] in the context data, this would produce:

Your items
  * 1
  * 2
  * 3

1.3   Snippet Reuse
    1.3.1   {% def %}

The def directive can be used to create macros, i.e. snippets of template text that have a name and optionally some parameters, and that can be inserted in other places:

    {% def greeting(name) %}
      Hello, ${name}!
    {% end %}
    ${greeting('world')}
    ${greeting('everyone else')}

The above would be rendered to:

    Hello, world!
    Hello, everyone else!

If a macro doesn't require parameters, it can be defined without the parenthesis. For example:

    {% def greeting %}
      Hello, world!
    {% end %}
    ${greeting()}

The above would be rendered to:

Hello, world!

    1.3.2   {% include %}

To reuse common parts of template text across template files, you can include other files using the include directive:

    {% include base.txt %}

Any content included this way is inserted into the generated output. The included template sees the context data as it exists at the point of the include. Macros in the included template are also available to the including template after the point it was included.
Include paths are relative to the filename of the template currently being processed. So if the example above was in the file "myapp/mail.txt" (relative to the template search path), the include directive would look for the included file at "myapp/base.txt". You can also use Unix-style relative paths, for example "../base.txt" to look in the parent directory.
Just like other directives, the argument to the include directive accepts any Python expression, so the path to the included template can be determined dynamically:

    {% include ${'%s.txt' % filename} %}

Note that a TemplateNotFound exception is raised if an included file can't be found.

Note

The include directive for text templates was added in Genshi 0.5.

1.4   Variable Binding
    1.4.1   {% with %}

The {% with %} directive lets you assign expressions to variables, which can be used to make expressions inside the directive less verbose and more efficient. For example, if you need use the expression author.posts more than once, and that actually results in a database query, assigning the results to a variable using this directive would probably help.

For example:

    Magic numbers!
    {% with y=7; z=x+10 %}
      $x $y $z
    {% end %}

Given x=42 in the context data, this would produce:

Magic numbers!
  42 7 52

Note that if a variable of the same name already existed outside of the scope of the with directive, it will not be overwritten. Instead, it will have the same value it had prior to the with assignment. Effectively, this means that variables are immutable in Genshi.

2   White-space and Line Breaks

Note that space or line breaks around directives is never automatically removed. Consider the following example:

    {% for item in items %}
      {% if item.visible %}
        ${item}
      {% end %}
    {% end %}

This will result in two empty lines above and beneath every item, plus the spaces used for indentation. If you want to supress a line break, simply end the line with a backslash:

    {% for item in items %}\
      {% if item.visible %}\
        ${item}
      {% end %}\
    {% end %}\

Now there would be no empty lines between the items in the output. But you still get the spaces used for indentation, and because the line breaks are removed, they actually continue and add up between lines. There are numerous ways to control white-space in the output while keeping the template readable, such as moving the indentation into the delimiters, or moving the end delimiter on the next line, and so on.

3   Comments

Parts in templates can be commented out using the delimiters {# ... #}. Any content in comments are removed from the output.

    {# This won't end up in the output #}
    This will.

Just like directive delimiters, these can be escaped by prefixing with a backslash.

    \{# This *will* end up in the output, including delimiters #}
This too.

"""