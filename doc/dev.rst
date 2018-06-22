******************
Manuel développeur
******************


Chargement des fichiers XML
===========================

Les fichiers XML se situent dans le répertoire
:file:`/etc/vigilo/vigiconf/conf.d/`.

On y trouve notamment les répertoires principaux suivants :

- définition des hôtes :file:`/etc/vigilo/vigiconf/conf.d/hosts`
- definition des groupes d'hôtes :file:`/etc/vigilo/vigiconf/conf.d/groups/`
- définition des modèles d'équipements
  :file:`/etc/vigilo/vigiconf/conf.d/templates/`

La documentation sur la syntaxe des fichiers de configuration XML est disponible
dans le :ref:`manuel utilisateur de VigiConf <manuel_util>`.
Le lecteur s'y référera au besoin.

Les fichiers XML sont parcourus par VigiConf.
La structure d'exécution est la suivante :

- Analyse des fichier XML.
- Prise en compte des tests de supervision Python.
- Exécution des générateurs.


Création d'un nouveau test de supervision
=========================================

Introduction
------------
Les tests de supervision de VigiConf sont écrits en Python.
Ils permettent de générer des fichiers de configuration concernant
une ou plusieurs applications.

Organisation des tests de supervision
-------------------------------------

Principe des classes d'équipements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Les tests fournis par Vigilo sont regroupés dans le répertoire suivant :
:file:`/usr/lib/python{x.y}/site-packages/vigilo/vigiconf/tests/`

On y trouve d'autres répertoires :

- all/
- linux/
- lmsensors/
- ucd/

Ces répertoires correspondent à des classes d'équipements et contiennent
des tests de supervision spécifiques à un type (famille/gamme/modèle)
d'équipement particulier. Par exemple, le dossier ``linux/`` contient
des tests de supervision capables de fonctionner sur toutes les distributions
Linux.

Le dossier ``all/`` est un cas particulier : les tests de supervision qu'il
contient peuvent être appliqués à n'importe quel type d'équipement (système
ou réseau).

..  note::
    Par convention, les noms des classes d'équipements ne peuvent contenir que
    les caractères alphanumériques (a-z0-9) et l'underscore (_).
    De plus, nous recommandons d'inscrire les noms des classes en minuscules.

..  warning::
    Pour des raisons historiques, certaines classes d'équipements actuellement
    fournies avec Vigilo contiennent des traits d'union (-) dans leur nom.
    Cet usage est cependant déconseillé et pourrait ne plus être supporté
    dans les futures versions de Vigilo. Utilisez le caractère underscore (_)
    à la place.

Les fichiers contenus dans ces répertoires portent des noms représentatifs
du test de supervision appliqué (par exemple, ``CPU.py`` pour un test de
supervision portant sur l'état du processeur sur l'équipement).

Le même nom de fichier peut apparaître dans plusieurs classes d'équipements
différentes (par exemple, ``linux/CPU.py`` et ``ucd/CPU.py``).

Ajout ou personnalisation d'un test
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
L'administrateur de la solution a la possibilité de définir ses propres tests
de supervision ou bien de redéfinir les tests fournis par défaut.
Les ajouts/surcharges de tests doivent se faire dans le dossier
:file:`/etc/vigilo/vigiconf/conf.d/tests` en respectant la même arborescence
:file:`{classe}/{test}.py`.

Ainsi, le test portant sur le processeur de la classe d'équipements "maclasse"
se trouvera dans le fichier
:file:`/etc/vigilo/vigiconf/conf.d/tests/maclasse/CPU.py`.

De même, on pourra redéfinir le comportement du test de supervision d'un
processeur sur une distribution Linux en créant un fichier
:file:`/etc/vigilo/vigiconf/conf.d/tests/linux/CPU.py` contenant le code
modifié.

Structure du code d'un test
---------------------------
Tous les tests de supervision héritent de la classe
:py:class:`vigilo.vigiconf.lib.confclasses.test.Test` et contiennent
une méthode :py:func:`add_test` qui intègre la logique du test.

Exemple de test de supervision de la charge du processeur sur un nouveau modèle
d'équipements de la marque "exemple". Le test sera placé dans
:file:`/etc/vigilo/vigiconf/conf.d/tests/exemple/CPU.py`.

..  sourcecode:: python

    # -*- coding: utf-8 -*-
    from vigilo.vigiconf.lib.confclasses.test import Test

    class CPU(Test):
        """
        Description de ce que fait le test, par exemple :
        Supervision de la charge du processeur sur un équipement
        de marque exemple.
        """

        def add_test(self, warn=60, crit=80):
            """
            Description des arguments acceptés par ce test de supervision.

            @param warn: Seuil de charge CPU en pourcentage
                au-delà duquel un avertissement sera levé
                par Vigilo dans le bac à événements.
            @type warn: C{float}
            @param crit: Seuil de charge CPU en pourcentage
                au-delà duquel une alerte critique sera levée
                par Vigilo dans le bac à événements.
            @type crit: C{float}
            """
            # Généralement le code commence par convertir les paramètres
            # reçus vers les types attendus, comme ci-dessous.
            warn = self.as_float(warn)
            crit = self.as_float(crit)

            # Code intégrant la logique de test de la charge CPU
            # sur ce type d'équipements.

..  note::
    Si vous souhaitez redistribuer votre test de supervision à l'équipe
    en charge du développement de Vigilo par la suite, nous vous recommandons
    d'adopter la syntaxe de documentation `Epytext`_, comme dans l'exemple
    précédent.
    Il s'agit du format de documentation de l'API adopté par l'équipe
    pour le développement des nouveaux tests de supervision.

..  _`Epytext`: http://epydoc.sourceforge.net/fields.html#fields

..  note::
    Si vous créez un test de supervision similaire à un test déjà existant
    (par exemple, un nouveau test portant sur le CPU), nous vous recommandons
    de garder la même signature pour la fonction :py:func:`add_test`,
    afin de rendre homogène la configuration du test pour l'utilisateur,
    quelle que soit la classe d'équipements sous-jacente.

La classe **doit** avoir exactement le même nom que le fichier dans lequel
elle se trouve. Il s'agit également du nom qui devra être utilisé par
l'administrateur dans les fichiers de configuration XML pour pouvoir appliquer
ce test de supervision à un équipement.

Les arguments passés à la méthode :py:func:`add_test` seront ceux indiqués
dans les fichiers XML de configuration qui utilisent ce test.

..  warning::
    Les arguments passés à la fonction :py:func:`add_test` seront
    systématiquement des chaînes de caractères, y compris pour des valeurs
    numériques (par exemple, des seuils d'alerte).

    Le code de la méthode doit donc effectuer les conversions nécessaires
    avant d'utiliser ces valeurs. Le chapitre `Méthodes de l'instance de test`_
    décrit les méthodes de la classe ``Test`` pouvant être utilisées afin
    de réaliser les conversions adéquates.


Méthodes de l'instance de test
------------------------------
Chaque instance de la classe ``Test`` ou d'une classe dérivée possède
plusieurs méthodes outils.

Ces méthodes peuvent être regroupées en 2 catégories :

-   Les méthodes permettant de convertir les paramètres passés à un test
    vers un type donné (entier, flottant, booléen).

-   Les méthodes permettant d'ajouter les éléments de configuration
    nécessaires pour réaliser les tests à proprement parler, récupérer des
    informations sur les performances (métrologie), générer des graphiques
    à partir de ces informations, etc.

La liste suivante décrit les méthodes utilisables pour effectuer la conversion
des paramètres d'un test.

:py:func:`as_bool`
    Convertit la valeur passée en argument en booléen.
    Les valeurs ``1``, ``true``, ``on`` et ``yes`` représentent la valeur
    Python ``True``, tandis que les valeurs ``0``, ``false``, ``off`` et ``no``
    représentent la valeur Python ``False``. Toute autre valeur génèrera une
    erreur d'analyse.

    ..  note::
        L'analyse effectuée est insensible à la casse (ie. ``yes`` == ``Yes``).

    ..  note::
        Si la valeur donnée est déjà un booléen, elle est retournée sans
        qu'aucune conversion ne soit effectuée.

:py:func:`as_float`
    Convertit la valeur passée en argument en nombre flottant.
    Si la valeur ne peut être convertie, une erreur d'analyse est levée.

    ..  note::
        Si la valeur donnée est déjà un flottant, elle est retournée sans
        qu'aucune conversion ne soit effectuée.

:py:func:`as_int`
    Convertit la valeur passée en argument en nombre entier.
    Si la valeur ne peut être convertie, une erreur d'analyse est levée.

    ..  note::
        Si la valeur donnée est déjà un entier, elle est retournée sans
        qu'aucune conversion ne soit effectuée.


La liste suivante décrit les méthodes appartenant à la deuxième catégorie
(manipulation des tests de supervision et de la métrologie).

:py:func:`add_collector_metro`
    Ajoute un service passif de métrologie à Nagios.

:py:func:`add_collector_service`
    Ajoute un service passif à Nagios et ajoute un test supplémentaire
    au collector (SNMP).

:py:func:`add_collector_service_and_metro`
    Cette méthode est un raccourci qui correspond à une succession
    d'appels aux méthodes suivantes :

    * :py:func:`add_collector_service`
    * :py:func:`add_collector_metro`

:py:func:`add_collector_service_and_metro_and_graph`
    Cette méthode est un raccourci qui correspond à une succession
    d'appels aux méthodes suivantes :

    * :py:func:`add_collector_service`
    * :py:func:`add_collector_metro`
    * :py:func:`add_graph`

:py:func:`add_external_sup_service`
    Ajoute un service actif à Nagios.

:py:func:`add_graph`
    Ajoute un graphique à Vigigraph.

:py:func:`add_metro_service`
    Ajoute un test Nagios sur les valeurs contenues dans les fichiers RRD.

.. todo:: (à supprimer car non utilisé en production)
.. : :py:func:`add_netflow`
.. :    Ajoute un service passif dans Nagios, des graphiques dans VigiGraph
.. :    et la configuration de :command:`pmacct` pour la capture de données
.. :    Netflow (information sur les sous-réseaux).
.. :

:py:func:`add_perfdata`
    Déclare une donnée de performance reçu par le connecteur de métrologie,
    permettant ainsi de faire le lien entre les données de performance et les
    base RRDs de métrologie.

:py:func:`add_perfdata_handler`
    Déclare une donnée de performance générée par un module Nagios dans Vigilo,
    permettant ainsi de faire le lien entre les données de performance des
    modules Nagios et les bases RRDs de métrologie.

:py:func:`add_trap`
    Ajoute un service passif dans Nagios, dont l'état changera sur réception
    d'un trap SNMP.

..  note::
    Un service Nagios actif est un service pour lequel l'exécution du test
    de supervision associé est déclenchée par Nagios.
    Un service Nagios passif est un service dont le test de supervision n'est
    pas déclenché par Nagios. À la place, la valeur d'état du service est
    calculée indépendamment de Nagios, puis injectée dans celui-ci.
    Par exemple, les services dont l'état est déterminé grâce à SNMP
    sont déclarés comme des services passifs dans Nagios.
    Le collector SNMP de Vigilo (service actif) est appelé par Nagios,
    se charge de calculer les états de ces services, puis envoie ces états
    à Nagios.

..  note::
    Toutes ces fonctions appellent la méthode add qui va ajouter/modifier
    la hash_map. La structure de la hash_map est disponible au début du fichier
    /lib/confclasses/host.py. La méthode add est également déclarée
    dans ce même fichier, elle va simplement ajouter un élément,
    dans l'une des clefs de la hash_map.
    En cas de non existence de la clef, elle l'ajoute.
    Le développeur peut appeler directement la méthode **add** dans son test
    Python, mais cela nécessite une connaissance de la structure de la hash_map.
    La hash_map est l'équivalent d'un dictionnaire Python, et est parcourue
    par les générateurs pour la génération de configuration.
    Avec un seul test Python, on peut, par exemple, ajouter des services
    passifs/actifs à Nagios, tout en plaçant des informations dans la hash_map,
    qui sera lu par notre générateur qui créera un fichier de configuration
    spécifique.

Générateurs de fichiers de configuration
========================================

Un certain nombre de générateurs de fichiers de configuration sont fournis
par défaut avec VigiConf. Ces générateurs vont créer des fichiers
de configuration pour les applications et composants qui interagissent
avec Vigilo (collecteur, connecteur de métrologie, Nagios, etc.).

Pour créer un nouveau générateur de fichiers de configuration, vous devez créer
un nouveau point d'entrée sous la section ``vigilo.vigiconf.generators``.
Pour l'heure, le nom de la clé associée au point d'entrée n'a pas d'importance.

Les générateurs doivent hériter de la classe
:py:class:`vigilo.vigiconf.lib.generators.Generator` ou d'une sous-classe
(par exemple, :py:class:`vigilo.vigiconf.lib.generators.file.FileGenerator`).

À minima, le générateur doit surcharger la méthode :py:func:`generate`
de la classe :py:class:`Generator` afin d'effectuer les traitements
nécessaires à la création d'une nouvelle configuration.

La méthode :py:func:`generate_host` est également utilisable.
Cette méthode génère la configuration pour un hôte et le serveur de supervision
qui lui est associé.

Les générateurs de fichiers de configuration sont regroupés dans le répertoire
:file:`/usr/lib/python{x.y}/site-packages/vigilo/vigiconf/applications/`,
où *x.y* représente la version de Python utilisée (par exemple, 2.5 ou 2.6).

Architecture d'un générateur
----------------------------
L'ajout d'un générateur se fait par la création d'un nouveau répertoire
dans ``applications/``. Le dossier est organisé selon l'arborescence
suivante ::

    ./applications/premier_generateur/
        |- __init__.py
        |- generator.py
        |- templates/
        |   |- template_un.tpl
        |   `- template_deux.tpl
        `- validate.sh

..  _`dev_app_desc`:

Le fichier :file:`__init__.py`
------------------------------
Ce fichier est quasiment identique entre les différents générateurs et décrit
l'application pour laquelle des fichiers de configuration peuvent être générés.

Le fichier doit contenir une classe Python héritant de la classe
:py:class:`vigilo.vigiconf.lib.application.Application`.
Cette classe ne contient aucune méthode, mais simplement des attributs
permettant de décrire l'application.

Par exemple, pour une application nommée ``Foobar`` effectuant une collecte
d'états, le fichier :file:`__init__.py` pourrait contenir un code semblable
à l'extrait suivant :

..  sourcecode:: python

    # -*- coding: utf-8 -*-

    from __future__ import absolute_import

    from vigilo.vigiconf.lib.application import Application
    from . import generator

    class Foobar(Application):
        name = "foobar"
        priority = -1
        validation = "validate.sh"
        start_command = "start.sh"
        stop_command = "stop.sh"
        generator = generator.FoobarGenerator
        group = "collect"

Le rôle des différents attributs de cette classe est décrit dans le tableau
ci-dessous.

..  table:: Attributs des sous-classes de :py:class:`Application`

    +-------------------+---------------------------------------------------+
    | Attribut          | Rôle                                              |
    +===================+===================================================+
    | ``dbonly``        | Drapeau indiquant si l'application manipule des   |
    |                   | données externes à la base de données Vigilo.     |
    |                   | Ce drapeau permet de paralléliser l'exécution des |
    |                   | applications qui ne travaillent que sur la base   |
    |                   | de données Vigilo et de désactiver leur exécution |
    |                   | lorsqu'une bascule de serveur est nécessaire      |
    |                   | (haute disponibilité).                            |
    +-------------------+---------------------------------------------------+
    | ``defaults``      | Paramêtres de configuration par défaut de         |
    |                   | l'application et indépendants de la configuration |
    |                   | du parc.                                          |
    +-------------------+---------------------------------------------------+
    | ``generator``     | La classe Python correspondant au générateur      |
    |                   | de configuration à proprement parler pour         |
    |                   | cette application.                                |
    +-------------------+---------------------------------------------------+
    | ``group``         | Le groupe fonctionnel auquel l'application        |
    |                   | appartient. Les groupes actuellement définis      |
    |                   | par Vigilo sont :                                 |
    |                   |                                                   |
    |                   | * ``collect``, pour les applications relatives    |
    |                   |   à la collecte d'états ou de données de          |
    |                   |   métrologie (Nagios, Collector, etc.).           |
    |                   | * ``metrology``, pour les applications qui        |
    |                   |   sont responsables du stockage et de la          |
    |                   |   restitution des données de métrologie           |
    |                   |   (connector-metro et VigiRRD).                   |
    |                   | * ``interface``, pour les interfaces graphiques   |
    |                   |   dont le contenu est partiellement généré        |
    |                   |   automatiquement grâce à VigiConf (VigiMap).     |
    +-------------------+---------------------------------------------------+
    | ``name``          | Un nom unique pour faire référence à cette        |
    |                   | application. Le nom ne doit contenir **que**      |
    |                   | des caractères en minuscules.                     |
    +-------------------+---------------------------------------------------+
    | ``priority``      | Priorité pour l'ordonnancement du redémarrage.    |
    |                   | L'application avec la priorité la plus élevée     |
    |                   | sera qualifiée et déployée en premier.            |
    +-------------------+---------------------------------------------------+
    | ``start_command`` | Une commande qui sera exécutée sur les serveurs   |
    |                   | de supervision où l'application est installée     |
    |                   | afin de relancer l'application. Cet attribut peut |
    |                   | valoir ``None`` si l'application n'a pas besoin   |
    |                   | d'être arrêtée puis relancée pour prendre en      |
    |                   | compte une nouvelle configuration.                |
    +-------------------+---------------------------------------------------+
    | ``stop_command``  | Une commande qui sera exécutée sur les serveurs   |
    |                   | de supervision où l'application est installée     |
    |                   | afin d'arrêter l'application. Cet attribut peut   |
    |                   | valoir ``None`` si l'application n'a pas besoin   |
    |                   | d'être arrêtée puis relancée pour prendre en      |
    |                   | compte une nouvelle configuration.                |
    +-------------------+---------------------------------------------------+
    | ``validation``    | Une commande qui sera exécutée sur la machine     |
    |                   | où VigiConf est installé et sur les serveurs      |
    |                   | de supervision où l'application est installée     |
    |                   | afin de vérifier la validité des fichiers de      |
    |                   | configuration générés.                            |
    +-------------------+---------------------------------------------------+

..  warning::
    Le nom de la classe (``Foobar`` dans notre exemple) **doit** commencer
    par une majuscule.

..  note::
    Les groupes fonctionnels sont utilisés pour répartir la supervision
    du parc entre différents serveurs de supervision.
    Cette répartition est effectuée grâce à la configuration située dans
    le fichier :file:`/etc/vigilo/vigiconf/conf.d/general/appgroups-server.py`.

Le dossier :file:`templates/`
-----------------------------
Le dossier :file:`templates/` contient un ensemble de fichiers de « modèles »
portant l'extension ``.tpl`` (pour « template »).

Reportez-vous à la section sur l':ref:`utilisation des modèles de documents`
dans un générateur pour plus d'information sur le mécanisme des modèles.

Le fichier :file:`generator.py`
-------------------------------
Ce fichier contient le générateur à proprement parler. C'est lui qui va générer
le(s) fichier(s) de configuration de l'application.

Imports utiles
^^^^^^^^^^^^^^
Le fichier :file:`generator.py` importe généralement plusieurs objets
et modules de Vigilo, comme indiqué dans l'extrait de code suivant :

..  sourcecode:: python

    # Si l'application utilise des données provenant du fichier
    # de configuration de VigiConf (/etc/vigilo/vigiconf/settings.ini).
    from vigilo.common.conf import settings

    # Cet import donne accès à la hashmap utilisée pour transmettre
    # la configuration des différents hôtes.
    from vigilo.vigiconf import conf

    # Import de la classe permettant de générer des fichiers de configuration.
    from vigilo.vigiconf.lib.generators import FileGenerator

    # Pour des besoins plus spécifiques, on peut également importer
    # directement la classe de base des générateurs
    #from vigilo.vigiconf.lib.generators import Generator

Classe du générateur
^^^^^^^^^^^^^^^^^^^^
Le fichier du générateur doit contenir une classe qui hérite de la classe
:py:class:`vigilo.vigiconf.lib.generators.Generator`
ou de l'une de ses sous-classes (par exemple
:py:class:`vigilo.vigiconf.lib.generators.FileGenerator`).

..  note::
    Par convention, la classe correspondant au générateur pour une application
    nommée ``Foobar`` dans Vigilo s'appelle ``FoobarGen``.

Cette classe doit définir au minimum deux méthodes :

*   :py:func:`generate`
*   :py:func:`generate_host`

La méthode :py:func:`generate` est appelée exactement une fois pour chaque
serveur de supervision vers laquelle une nouvelle configuration doit être
déployée, au début de la génération. La plupart du temps, cette méthode
se contente de réinitialiser la liste des fichiers de configuration à générer
(attribut ``_files``), puis appelle la méthode :py:func:`generate` de
la classe parente.

Par exemple, le générateur de configuration pour Nagios contient :

..  sourcecode:: python

    def generate(self):
        # pylint: disable-msg=W0201
        self._files = {}
        self._graph = None
        super(NagiosGen, self).generate()


La méthode :py:func:`generate_host` est appelée pour chaque hôte pour lequel
une configuration doit être générée. La méthode reçoit en argument le nom
du serveur pour lequel une configuration doit être générée, ainsi que le nom
du serveur de supervision vers lequel cette configuration sera déployée :

..  sourcecode:: python

    def generate_host(self, hostname, vserver):
        # Le code permettant de générer la configuration pour l'hôte
        # "hostname" sur le serveur de supervision "vserver" se trouve ici.
        pass

Les méthodes du générateur seront donc appelées successivement selon
le motif suivant :

..  sourcecode:: python

    # Début de la nouvelle configuration pour un serveur de supervision.
    generator.generate()
    # Génération de la configuration pour les différents équipements
    # supervisés par le serveur "sup1.example.com"
    generator.generate_host("serveur1.example.com", "sup1.example.com")
    generator.generate_host("serveur2.example.com", "sup1.example.com")
    generator.generate_host("serveur3.example.com", "sup1.example.com")

    # Début de la nouvelle configuration pour un serveur de supervision.
    generator.generate()
    # Génération de la configuration pour les différents équipements
    # supervisés par le serveur "sup2.example.com"
    generator.generate_host("serveur4.example.com", "sup2.example.com")
    generator.generate_host("serveur5.example.com", "sup2.example.com")
    generator.generate_host("serveur6.example.com", "sup2.example.com")

    # etc.

..  _`utilisation des modèles de documents`:

Utilisation des modèles
^^^^^^^^^^^^^^^^^^^^^^^
Pour générer le ou les fichiers de configuration dont il est responsable,
un générateur peut utiliser le mécanisme des modèles de documents proposé
par Vigilo. Les modèles de documents sont des fichiers portant l'extension
« .tpl » et placés dans le répertoire :file:`templates/` à côté du générateur.

Un modèle de document peut représenter la totalité d'un fichier de configuration
ou bien simplement un fragment de ce fichier. Dans le second cas, cela signifie
que plusieurs modèles de documents devront être utilisés successivement afin
de générer un fichier de configuration complet.

Un modèle de document est similaire à « un texte à trous », au sens où il
s'agit d'un exemple du contenu d'un fichier de configuration dans lequel
certains champs dont le contenu est variable (par exemple, un nom de machine)
sont remplacés par des champs de formatage Python (``%(foo)s``).
Le contenu des champs de formatage Python sera substitué par les valeurs
adéquates lors de l'utilisation du modèle par le générateur.

Exemple de modèle (ici, le modèle :file:`host.tpl` responsable de la création
de la configuration d'un hôte dans Nagios) :

..  sourcecode:: text

    define host{
        use %(hostTPL)s
        host_name %(name)s
        alias %(name)s
        address %(address)s
        %(hostGroups)s
        %(parents)s
        %(generic_hdirectives)s
    }

Dans cet exemple, on peut voir que le modèle attend plusieurs variables :

*   Le nom du modèle Nagios à utiliser : ``hostTPL``.
*   Le nom de l'équipement en cours de configuration : ``name``.
*   L'adresse de l'équipement : ``address``.
*   D'autres variables : ``hostGroups``, ``parents``, etc.

L'utilisation d'un modèle de documents dans un générateur est plutôt simple.
L'extrait de code (simplifié) suivant donne un exemple d'utilisation
de plusieurs modèles par le générateur Nagios :

..  sourcecode:: python

    def generate_host(self, hostname, vserver):
        # Détermination du chemin jusqu'au fichier de configuration à générer.
        # - self.baseDir correspond à la racine du dossier de génération
        #   des configurations.
        # - vserver contient le nom du serveur de supervision vers lequel
        #   ce fichier de configuration sera déployé.
        # L'affectation du chemin dans un attribut de la classe (self.fileName)
        # est facultative : on aurait pu utiliser une variable locale.
        self.fileName = os.path.join(self.baseDir, vserver, "nagios",
                                     "nagios.cfg")

        if self.fileName not in self._files:
            self._files[self.fileName] = {}

        # Récupération de la configuration relative à l'hôte
        # pour lequel on est en train de générer une configuration.
        h = conf.hostsConf[hostname]

        # Si le fichier de configuration n'existe pas encore
        # (ie. on commence la création de la configuration).
        if not os.path.exists(self.fileName):
            # Alors, on utilise la méthode templateCreate() pour créer
            # le fichier de configuration à partir du modèle contenu
            # dans "templates/header.tpl".
            self.templateCreate(self.fileName, self.templates["header"] {,
                    "confid": conf.confid,
                })

        # Préparation des variables qui seront passées
        # au modèle "templates/host.tpl".
        newhash = self._prepare_template_variables(h.copy())

        # Ajout de la configuration de l'hôte au fichier de configuration,
        # en utilisant le modèle "templates/host.tpl".
        self.templateAppend(self.fileName, self.templates['host'], newhash)

En somme, la signature des méthodes :py:func:`templateCreate` et
:py:func:`templateAppend` est identique, les 2 méthodes acceptant
les arguments suivants (dans cet ordre) :

*   Le nom du fichier de configuration qui sera créé (:py:func:`templateCreate`)
    ou complété (:py:func:`templateAppend`).
*   Le nom du modèle de document à utiliser, **sans extension**.
*   Un dictionnaire dont les clés sont les champs de substitution définis
    dans le modèle de document et les valeurs sont celles que doivent
    prendre les champs de substitution.


Le fichier de validation
------------------------
Ce fichier correspond à la valeur de l'attribut ``validation``
:ref:`dans la classe qui décrit l'application <dev_app_desc>`
et son nom doit donc être adapté en conséquence.
En général, il s'agit d'un simple script shell appelé :file:`validate.sh`.

Le but de ce fichier est d'effectuer des vérifications permettant de s'assurer
que la nouvelle configuration est valide (bon format, bonnes options, etc.).

Ce fichier sera exécuté une première fois sur la machine qui héberge VigiConf
(phase de validation), puis une seconde fois sur la machine de supervision
finale (phase de qualification) afin d'être absolument certain que la
nouvelle configuration pourra être appliquée.

Une rapide lecture du contenu des scripts des autres générateurs
facilite la création d'un nouveau script de validation.

Générateur de cartes automatiques
=================================

VigiConf fournit un mécanisme permettant de générer automatiquement des cartes,
construites à partir des données présentes dans la configuration (groupes,
hôtes, services ou toute autre donnée).

Un générateur de cartes automatiques est une classe contenue dans le paquet
:py:mod:`automaps` et dérivant de la classe de base :py:class:`AutoMap`.

..  only:: enterprise

    Une implémentation d'un tel générateur est fournie, il s'agit de la classe
    :py:class:`BasicAutoMap`. La classe :py:class:`BasicAutoMap` génère
    des cartes et des groupes de cartes selon les spécifications suivantes :

    -   La génération est paramétrable au moyen d'un fichier stocké
        en gestion de configuration SVN ; il s'agit du fichier
        :file:`conf.d/general/automaps.py`.

    -   Un jeu de groupes de cartes est généré de façon paramétrable,
        dont un groupe de cartes par groupe d'éléments supervisés
        de plus haut niveau.

    -   Une carte (entité ``Map``) est générée pour un groupe terminal
        (dans la hiérarchie des groupes) contenant des éléments à superviser
        (hôtes ou services), si cette carte n'existe pas déjà.

    -   Lorsqu'une carte est créée, elle est associée à un ou plusieurs
        groupes de cartes, dont la hiérarchie suit celle des groupes d'éléments
        à superviser correspondants.

    -   Le contenu d'une carte (éléments de la classe ``MapNodeHost``
        ou ``MapNodeHls``) est généré s'il s'agit d'une carte marquée
        comme « générée automatiquement ».

    -   Dans le cas d'une carte générée automatiquement, les éléments affichant
        des entités n'existant plus sont supprimés.

    -   Toutes les modifications apportées à un élément affiché sur une carte
        générée automatiquement ne sont pas prises en compte. En particulier,
        il n'est pas possible de changer l'objet supervisé référencé par
        l'élément.


.. vim: set tw=79 :
