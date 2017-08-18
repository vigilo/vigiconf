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

VigiConf a besoin de ``subversion``, de ``sqlite3``, et des modules Python
suivants :

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

Après l'installation, il est nécessaire de mettre en place le dossier de
configuration, qui sera géré sous SVN. Pour cela, suivre les indications du
fichier ``/etc/vigilo/vigiconf/README.post-install``.

Enfin, si cela n'a pas été fait lors de l'install de vigiconf-local, il
faut ajouter des droits sudo à l'utilisateur ``vigiconf`` pour lui permettre
de redémarrer les services qu'il télé-administre. Pour cela, ajouter à la fin
du fichier ``/etc/sudoers`` les lignes suivantes ::

    # VigiConf
    Defaults:vigiconf !requiretty
    Cmnd_Alias INIT = /etc/init.d/*
    Cmnd_Alias VALID = /usr/sbin/nagios
    vigiconf ALL=(ALL) NOPASSWD: INIT, VALID
    vigiconf ALL=(nagios) NOPASSWD: /usr/bin/pkill


Utilisation
-----------
VigiConf s'exécute par la commande ``vigiconf``. Utilisez l'option ``--help``
pour découvrir les fonctionnalités disponibles.


License
-------
VigiConf est sous licence `GPL v2`_.


.. _documentation officielle: Vigilo_
.. _Vigilo: http://www.vigilo-nms.com
.. _GPL v2: http://www.gnu.org/licenses/gpl-2.0.html

.. vim: set syntax=rst fileencoding=utf-8 tw=78 :


