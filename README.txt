VigiConf
========

VigiConf est le composant de Vigilo_ qui permet de distribuer la configuration
aux autres applications qui composent Vigilo.

Il joue le rôle d'un "chef d'orchestre", offrant un point d'entrée unique pour
la configuration du parc et s'assurant de la cohérence de la configuration des
applications de Vigilo.

Pour les détails du fonctionnement de VigiConf, se reporter à la
`documentation officielle`_.


Dépendances
-----------
Vigilo nécessite une version de Python supérieure ou égale à 2.5. Le chemin de
l'exécutable python peut être passé en paramètre du ``make install`` de la
façon suivante::

    make install PYTHON=/usr/bin/python2.6

VigiConf a besoin des modules Python suivants :

- setuptools (ou distribute)
- vigilo-common
- vigilo-models
- argparse
- lxml

Sur Python < 2.6, il nécessite aussi le module "multiprocessing".

Sur Python < 2.7, il nécessite aussi le module "initgroups".


Installation
------------
L'installation se fait par la commande ``make install`` (à exécuter en
``root``).


License
-------
VigiConf est sous licence `GPL v2`_.


.. _documentation officielle: Vigilo_
.. _Vigilo: http://www.projet-vigilo.org
.. _GPL v2: http://www.gnu.org/licenses/gpl-2.0.html

.. vim: set syntax=rst fileencoding=utf-8 tw=78 :


