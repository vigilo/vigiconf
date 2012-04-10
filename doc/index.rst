########
VigiConf
########

VigiConf est le centre de configuration de Vigilo.

Documentation disponible :

.. : L'ajout de "suptests" dans toctree permet juste d'éviter un
.. : avertissement sur le fait que le fichier n'est utilisé dans aucun
.. : index, sans désactiver complètement l'analyse du document (pour qu'il
.. : soit quand même analysé par la directive "include").

.. toctree::
   :maxdepth: 2

   util

.. : "suptests" est inclus et ne doit pas être référencé dans une TOC visible.
.. : On l'inclus dans une table cachée pour éviter un avertissement de Sphinx.

.. toctree::
   :hidden:

   suptests


.. *****************
.. Indexes et tables
.. *****************
..
.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`


.. vim: set tw=79 :
