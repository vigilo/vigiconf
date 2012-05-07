..  _`manuel_util`:

******************
Manuel utilisateur
******************


Installation
============

Pré-requis logiciels
--------------------
Afin de pouvoir faire fonctionner VigiConf, l'installation préalable des
logiciels suivants est requise :

* python (>= 2.5), sur la machine où VigiConf est installé
* postgresql-server (>= 8.2), éventuellement sur une machine distante

Reportez-vous aux manuels de ces différents logiciels pour savoir comment
procéder à leur installation sur votre machine.

VigiConf requiert également la présence de plusieurs dépendances Python. Ces
dépendances seront automatiquement installées en même temps que le paquet de
VigiConf.

Installation du paquet RPM
--------------------------
L'installation de VigiConf se fait en installant simplement le paquet RPM
"``vigilo-vigiconf``". La procédure exacte d'installation dépend du gestionnaire
de paquets utilisé. Les instructions suivantes décrivent la procédure pour les
gestionnaires de paquets RPM les plus fréquemment rencontrés.

Installation à l'aide de urpmi:

..  sourcecode:: bash

    urpmi vigilo-vigiconf        # sur la machine d'administration
    urpmi vigilo-vigiconf-local  # sur les autres machines de la plate-forme de supervision

Installation à l'aide de yum:

..  sourcecode:: bash

    yum install vigilo-vigiconf        # sur la machine d'administration
    yum install vigilo-vigiconf-local  # sur les autres machines de la plate-forme de supervision


Configuration
=============

La configuration de VigiConf comprend deux parties. D'une part, la
configuration de l'outil en lui-même. D'autre part, la configuration du parc
informatique supervisé par Vigilo (et dont la configuration est gérée par
VigiConf). Ce chapitre ne porte que sur la configuration de VigiConf. Pour la
documentation sur la configuration du parc informatique supervisé, reportez-vous
au chapitre :ref:`confparc`.

Par défaut, la configuration de VigiConf se trouve dans
:file:`/etc/vigilo/vigiconf/settings.ini`. Vous devrez **impérativement**
modifier ce fichier de configuration avant d'utiliser VigiConf.

Si vous le souhaitez, vous pouvez également placer les options de configuration
communes à tous les modules de Vigilo installés sur la machine dans le fichier
:file:`/etc/vigilo/settings.ini`. Ce fichier générique sera chargé en premier
au lancement de VigiConf.

Ces fichiers sont composés de différentes sections permettant de paramétrer des
aspects divers de VigiConf, chacune de ces sections peut contenir un ensemble
de valeurs sous la forme ``cle=valeur``. Les lignes commençant par ";" ou "#"
sont des commentaires et sont par conséquent ignorées.

Le format de ces fichiers peut donc être résumé dans l'extrait suivant:

..  sourcecode:: ini

    # Ceci est un commentaire
    ; Ceci est également un commentaire

    [section1]
    option1=valeur1
    ; ...
    optionN=valeurN

    ; ...

    [sectionN]
    option1=valeur1
    ; ...
    optionN=valeurN


Configuration de la base de données
-----------------------------------

Connexion
^^^^^^^^^
VigiConf enregistre une partie des informations de la configuration du parc
supervisé en base de données. La configuration de la connexion à cette base de
données se fait en modifiant la valeur de la clé ``sqlalchemy_url`` sous la
section ``[database]``.

Cette clé consiste en une :term:`URL` définissant tous les paramètres
nécessaires pour pouvoir se connecter à la base de données. Le format de cette
URL est le suivant::

    sgbd://utilisateur:mot_de_passe@serveur:port/base_de_donnees

Le champ ``:port`` est optionnel et peut être omis si vous utilisez le port par
défaut d'installation du SGBD choisi.

Par exemple, voici la valeur correspondant à une installation mono-poste par
défaut de Vigilo::

    postgres://vigilo:vigilo@localhost/vigilo

..  warning::
    À l'heure actuelle, seul PostgreSQL a fait l'objet de tests intensifs.
    D'autres SGBD peuvent également fonctionner, mais aucun support ne
    sera fourni pour ceux-ci.

Préfixe pour les tables
^^^^^^^^^^^^^^^^^^^^^^^
Il est recommandé de ne pas utiliser de préfixe pour les noms des tables mais
de privilégier l'installation de Vigilo dans une base de données séparée.
Néanmoins, vous pouvez choisir un préfixe qui sera appliqué aux noms des tables
de la base de données en indiquant ce préfixe dans la clé ``db_basename`` sous
la section ``[database]``.

Utilisez de préférence un préfixe ne contenant que des caractères
alpha-numériques ou le caractère "_". Exemple de préfixe valide :
"``vigilo_``".


Configuration du dépôt pour le suivi des évolutions
---------------------------------------------------

Les modifications apportées à la configuration du parc sont enregistrées dans
un dépôt :term:`SVN`, permettant ainsi d'assurer un suivi des modifications et
un éventuel retour arrière.

La configuration de ce dépôt se fait en utilisant les clés suivantes de la
section ``vigiconf``:

confdir
    Dossier contenant un « checkout » (version de travail) du dépôt SVN et dont
    les modifications seront enregistrées dans le dépôt à chaque utilisation de
    la commande "``vigiconf deploy``".

    Cette option doit pointer vers le dossier où la configuration du parc
    supervisé est sauvegardée.

svnusername
    Nom d'utilisateur pour accéder au dépôt SVN.

svnpassword
    Mot de passe pour accéder au dépôt SVN.

svnrepository
    URL indiquant l'emplacement du dépôt SVN. Il peut s'agir d'une URL pointant
    vers un dépôt local (``file://``) ou distant (``ssh+svn://``, ``http://``,
    etc.). Référez-vous à la documentation de Subversion pour les différents
    protocoles supportés.

Autres options de configuration
-------------------------------
Les paragraphes qui suivent décrivent les autres options de configuration
disponibles dans VigiConf et situées sous la section ``[vigiconf]`` du fichier
``settings.ini``.

En règle générale, les valeurs correspondant à une nouvelle installation de
VigiConf sont suffisantes et il n'est pas nécessaire de les modifier.

Répertoire de travail pour la génération
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
L'option "``libdir``" permet de spécifier l'emplacement du répertoire de
travail servant à générer les fichiers de configuration des applications.

La valeur définie dans la configuration initiale est
:file:`/var/lib/vigilo/vigiconf`.

Emplacement final de la configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
La directive "``targetconfdir``" permet d'indiquer le dossier vers lequel les
fichiers de configuration finaux seront télé-déployés sur les serveurs de
supervision.

La valeur définie dans la configuration initiale est
:file:`/etc/vigilo/vigiconf`.
Les applications dont dépend Vigilo (ex : Nagios) doivent être configurées pour
aller chercher leur fichier de configuration dans le sous-dossier "``prod``" de
ce dossier.

Répertoire des plugins de VigiConf
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
L'option "``pluginsdir``" permet de faciliter l'extension de VigiConf à l'aide
de plugins (modules complémentaires). Il s'agit de l'emplacement d'un
répertoire qui contiendra des modules Python (eggs) qui seront chargés
automatiquement au lancement de VigiConf. Ces modules ont la possibilité
d'enregistrer des points d'entrée Python afin d'ajouter de nouvelles
fonctionnalités.

La valeur de cette option dans la configuration initiale fournie avec VigiConf
est :file:`/etc/vigilo/vigiconf/plugins`.

Emplacement du socket du connecteur-nagios
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
L'option "``socket_nagios_to_vigilo``" contient le chemin d'accès jusqu'au
connecteur-nagios sur les machines où une configuration pour Nagios est
télé-déployée.
La valeur lors d'une nouvelle installation est
:file:`/var/lib/vigilo/connector-nagios/send.sock`, ce qui correspond à la
valeur par défaut dans la configuration du connector-nagios.

Emplacement du verrou
^^^^^^^^^^^^^^^^^^^^^
Afin d'éviter un conflit lorsque plusieurs administrateurs du même parc
effectuent un nouveau déploiement de la configuration simultanément, VigiConf
acquiert un verrou au démarrage. Ce verrou est automatiquement libéré lors de
l'arrêt de VigiConf.

La directive "``lockfile``" permet de spécifier l'emplacement du fichier qui
correspondra au verrou. Dans la configuration fournie par défaut avec VigiConf,
le verrou est enregistré dans :file:`/var/lock/vigilo-vigiconf/vigiconf.token`.

Mode de simulation des opérations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
L'option "``simulate``" est un booléen qui permet d'activer un mode spécial de
VigiConf dans lequel les opérations sont simulées et ne sont pas validées.
Cette option est destinée uniquement au débogage de l'application lors de la
phase de développement et doit être positionnée à "``False``" en production.



.. _confparc:

Configuration du parc à superviser
==================================
La configuration du parc à superviser se fait au travers de fichiers XML. Ces
fichiers sont stockés dans le répertoire pointé par l'option "``confdir``" de
la section "``vigiconf``" dans le fichier de configuration de VigiConf. Des
fichiers d'exemple sont installés en même temps que VigiConf.

Ce chapitre présente la structure de la configuration et le contenu des
différents fichiers.


Fichiers de configuration XML
-----------------------------

Afin d'éviter les erreurs de saisie dans les fichiers de configuration de
VigiConf, ceux-ci font systématiquement l'objet d'une validation à l'aide de
schémas XML.

Ces schémas sont stockés dans:

    :file:`/usr/lib{arch}/python{version}/site-packages/vigilo/vigiconf/validation/xsd/`

Par exemple, pour une installation standard de Python 2.5 sur une machine
équipée d'une architecture x86:

    :file:`/usr/lib/python2.5/site-packages/vigilo/vigiconf/validation/xsd/`

Dans la suite de ce document, on considère qu'un fichier :samp:`{type}.xml` de
la configuration de VigiConf est valide s'il respecte le schéma défini dans le
fichier :samp:`{type}.xsd` situé dans ce répertoire correspondant au type
d'objet manipulé.

Pour le reste des explications de ce chapitre, tous les emplacements de
fichiers ou dossiers indiqués sont relatifs au dossier de configuration du parc
(par défaut, :file:`/etc/vigilo/vigiconf/conf.d/`)


Configuration des hôtes
-----------------------

Le dossier "``hosts``" contient les fichiers de définition des hôtes supervisés
du parc. Tous les fichiers XML de ce dossier sont analysés et doivent contenir
la définition d'un ou plusieurs hôtes.

La balise à la racine de ce document se nomme "``hosts``" et peut contenir un
ou plusieurs blocs "``host``", correspondant chacun à la définition d'un hôte.

Le fragment de code suivant rappelle la structure générale du fichier:

..  sourcecode:: xml

    <?xml version="1.0"?>
    <hosts>
      <host name="host1" attr1="..." attr2="..." attrN="...">
        ...
      </host>
      <host name="host2" attr1="..." attr2="..." attrN="...">
        ...
      </host>
      ...
    </hosts>

Définition d'un hôte
^^^^^^^^^^^^^^^^^^^^
Un hôte est défini à l'aide d'une balise *host* ayant la forme suivante:

..  sourcecode:: xml

    <host name="localhost" address="127.0.0.1" ventilation="P-F">
      ...
    </host>

Un bloc de données *host* possède les attributs suivants :

name
    [requis] Nom de l'hôte. Il peut s'agir d'un nom entièrement qualifié (FQDN)
    ou simplement d'un nom court permettant d'identifier l'équipement au sein
    du parc.

address
    [optionnel] Adresse permettant de communiquer avec l'hôte. Il peut s'agir
    d'une adresse IP (v4 ou v6) ou d'un nom de domaine entièrement qualifié
    (FQDN). Si cet attribut est omis, la valeur de l'attribut *name* est
    utilisée.

ventilation
    [optionnel] Nom du groupe de supervision dans lequel cet hôte doit être
    placé (ventilé).

    En général, il n'est pas nécessaire de spécifier cet attribut. VigiConf
    tente de le déduire automatiquement à partir des noms des groupes auxquels
    l'hôte est rattaché. Cet attribut permet essentiellement de résoudre les
    conflits entre les groupes. Il peut également être utilisé pour affecter
    l'hôte à un groupe de supervision qui n'a aucune relation avec les groupes
    métier.

La balise *host* peut contenir les balises suivantes :

- ``class`` (0 ou plus)
- ``template`` (0 ou plus)
- ``attribute`` (0 ou plus)
- ``nagios`` (0 ou 1)
- ``test`` (0 ou plus)
- ``tag`` (0 ou plus)
- ``group`` (1 ou plus)
- ``weight`` (0 ou 1)
- ``default_service_weight`` (0 ou 1)
- ``default_service_warning_weight`` (0 ou 1)


Balise "``class``"
^^^^^^^^^^^^^^^^^^
Syntaxe:

..  sourcecode:: xml

    <class>nom de la classe</class>

Indique la ou les classes d'équipements auxquelles l'hôte appartient. En
fonction de ces classes, des tests spécifiques peuvent être disponibles afin
d'obtenir des informations plus précises sur l'état de l'équipement.

Balise "``template``"
^^^^^^^^^^^^^^^^^^^^^
Syntaxe:

..  sourcecode:: xml

    <template>nom du modèle</template>

Précise le nom du modèle d'hôtes duquel cet hôte hérite une partie de ses
propriétés. L'utilisation de l'héritage est pratique lorsque votre parc est
composé d'éléments (serveurs, routeurs, etc.) homogènes. Vous pouvez alors
définir un modèle (template) pour chaque type d'équipement avec tous les tests
associés et créer ensuite simplement une définition d'hôte pour chaque
équipement.

Cette balise peut être utilisée à plusieurs reprises. Les paramètres du dernier
modèle chargé écrasent ceux des modèles précédents. Les valeurs définies au
niveau d'un hôte écrase toujours les valeurs définies au niveau d'un modèle
hérité (en particulier, les paramètres des tests).

..  note::
    Pour être utilisable via cette balise, le modèle doit avoir été défini
    à l'aide de la balise *hosttemplate* (voir :ref:`hosttemplate`).

..  warning::
    En cas de conflits liés aux dépendances des modèles, il se peut que les
    modèles soient réordonnés (un message d'avertissement est alors émis par
    VigiConf lors du déploiement). Dans ce cas, l'ordre d'application des
    paramètres peut être légèrement différent de l'ordre d'affectation des
    modèles dans le fichier de configuration.

Balise "``attribute``"
^^^^^^^^^^^^^^^^^^^^^^
Syntaxes:

..  sourcecode:: xml

    <attribute name="nom de l'attribut">valeur de l'attribut</attribute>

    <attribute name="nom de l'attribut">
      <item>valeur 1</item>
      <item>valeur 2</item>
    </attribute>

Cette balise permet de fixer certains des attributs de l'hôte, comme par
exemple le nombre de processeurs présents sur la machine. En général, ces
informations sont extraites automatiquement des équipements par une
interrogation SNMP (voir à ce sujet le chapitre « :ref:`discover` »).

Les noms d'attributs utilisables dépendent des tests de supervision installés
avec VigiConf. Par défaut, les attributs suivants sont disponibles :

- "``fans``" : la liste des identifiants des ventilateurs sur l'équipement ;
- "``tempsensors``" : la liste des noms des sondes de température présentes
  sur l'équipement ;
- "``cpulist``" : la liste des identifiants des processeurs sur
  l'équipement ;
- "``snmpCommunity``" : la communauté pour l'accès SNMP à l'équipement ;
- "``snmpVersion``" : la version SNMP à utiliser (par défaut, la version 2 est
  utilisée) ;
- "``snmpPort``" : le port SNMP à utiliser (par défaut, le port 161 est
  utilisé) ;
- "``oxe_login``": le nom d'utilisateur permettant de se connecter en Telnet à
  l'hôte ;
- "``oxe_password``": le mot de passe allant de pair avec le nom d'utilisateur
  permettant de se connecter en Telnet à l'hôte ;
- "``timeout``": délai d'attente utilisé lors de la connexion Telnet à l'hôte.


.. _`configuration des tests d'un hôte`:

Balise "``test``"
^^^^^^^^^^^^^^^^^
Syntaxe:

..  sourcecode:: xml

    <test name="nom du test">
      <arg name="nom_argument_1">valeur argument 1</arg>
      <arg name="nom_argument_2">valeur argument 2</arg>
      ...
      <arg name="nom_argument_n">valeur argument n</arg>
      <nagios>
        <directive name="nom_directive_1">valeur directive 1</directive>
        ...
        <directive name="nom_directive_n">valeur directive n</directive>
      </nagios>
    </test>

La balise ``test`` permet d'ajouter un test de supervision à l'hôte. Elle
possède un attribut ``name`` obligatoire qui désigne le test de supervision
à appliquer (par exemple : "``CPU``" pour superviser l'état du processeur d'un
équipement).

Elle accepte un attribut optionnel ``weight``, contenant un entier positif et permettant
de configurer le poids apporté par les services techniques associés à ce test
lorsqu'ils se trouvent dans un état supposé nominal (OK ou UNKNOWN).
Ce poids est utilisé pour le calcul de l'état des
:ref:`services de haut niveau <hlservices>`.
Si cet attribut n'est pas configuré, le poids associé aux services techniques
dans l'état OK ou UNKNOWN sera le même que celui configuré par l'attribut
``default_service_weight`` (qui vaut 1 par défaut).

De même, elle accepte un attribut optionnel ``warning_weight``, contenant
un entier positif et permettant de configurer le poids apporté par
les services techniques associés à ce test lorsqu'ils se trouvent
dans un état dégradé (WARNING).
Ce poids est utilisé pour le calcul de l'état des
:ref:`services de haut niveau <hlservices>`.
Si cet attribut n'est pas configuré, le poids associé aux services techniques
dans l'état WARNING sera le même que celui configuré par l'attibut
``default_service_warning_weight`` (qui vaut 1 par défaut).
La valeur configurée dans cet attribut doit toujours être inférieure ou égale
à celle configurée dans l'attribut ``weight``.

Un test accepte généralement zéro, un ou plusieurs arguments, qui doivent être
passés dans l'ordre lors de la déclaration du test, à l'aide de la balise
``arg``. Chaque argument dispose d'un nom (attribut ``name``) et d'une valeur.

Vous pouvez également, de façon optionnelle, définir des paramètres spécifiques
pour la supervision à l'aide de la balise ``nagios``, qui contiendra une ou
plusieurs directives adressées au moteur de supervision Nagios. Voir la section
ci-dessous pour plus d'informations.

..  note::
    Si le même argument est défini deux fois, seule la dernière valeur sera
    utilisée.

..  note::
    Vigilo est optimiste quant à l'état des éléments du parc. De fait, la
    valeur de l'attribut "``weight``" est utilisée aussi bien lorsque
    le service se trouve dans l'état OK (état nominal) que lorsqu'il se trouve
    dans l'état UNKNOWN (état inconnu, supposé nominal).


.. _nagiostag:

Balise "``nagios``"
^^^^^^^^^^^^^^^^^^^
Un bloc de données ``nagios`` contient des blocs ``directive`` dont l'attribut
``name`` appartient à la liste des directives "``host``" de Nagios. La
documentation sur ces directives est disponible dans `la documentation Nagios
<http://nagios.sourceforge.net/docs/3_0/objectdefinitions.html#host>`_.

Syntaxe:

..  sourcecode:: xml

    <nagios>
      <directive name="max_check_attempts">5</directive>
      <directive name="check_interval">10</directive>
      <directive name="retry_interval">1</directive>
    </nagios>

Toutes les directives proposées par Nagios sont utilisables ici.  Néanmoins, un
mauvais réglage des directives peut dégrader sérieusement les performances de
la supervision, voire entrainer un dysfonctionnement.  L'utilisation des
directives est donc à laisser à des utilisateurs avertis.

Un bloc ``nagios`` peut se trouver au sein d'un bloc ``host``/``hosttemplate``
ou d'un bloc ``test``.

Si la même directive est défini deux fois, la dernière valeur est celle qui
sera utilisée.


Balise "``tag``"
^^^^^^^^^^^^^^^^
Syntaxe:

..  sourcecode:: xml

        <tag service="service" name="étiquette"/>

        <tag service="service" name="étiquette">valeur</tag>

La balise ``tag`` permet d'affecter une étiquette à un hôte ou un service.
L'attribut ``name`` permet de préciser le nom de l'étiquette à ajouter. Il doit
correspondre au nom d'une image (**privée de son extension**) à afficher dans
VigiMap. Cette image doit se trouver dans
:samp:`{Python}/site-packages/vigilo/themes/public/vigimap/images/tags`,
où *Python* vaut par exemple :file:`/usr/lib/python2.5` pour une installation
standard de Python 2.5.

L'attribut ``service`` permet, quant à lui, d'indiquer le nom du service auquel
cette étiquette sera affectée. Utilisez la valeur "``host``" si l'étiquette
doit porter sur l'hôte en lui-même et non pas sur l'un de ses services.

Enfin, la valeur de l'étiquette est facultative et fait office de méta-donnée.
Exemple, pour associer à un hôte l'étiquette de MCO (l'image ``mco.png`` est
fournie dans toute installation standard de Vigilo):

..  sourcecode:: xml

    <tag service="host" name="mco"/>


Balise "``group``"
^^^^^^^^^^^^^^^^^^
Syntaxe:

..  sourcecode:: xml

    <group>/Chemin complet/vers le/Groupe</group>

    <group>Nom de groupe</group>

La balise ``group`` permet d'indiquer les groupes métiers auxquels cet
équipement appartient. Les groupes sont organisés de manière hiérarchique (sous
la forme d'un arbre).

La première forme (chemin absolu) permet de se déplacer dans cette hiérarchie
en donnant le chemin complet jusqu'au groupe, de la racine de l'arbre vers les
feuilles. Chaque élément du chemin est précédé du symbole "``/``". Si le nom de
l'élément contient un "``/``" ou un "``\``", vous devez le faire précéder du
caractère d'échappement "``\``". Ainsi, l'élément "``Serveurs Linux/Unix``"
sera écrit dans les chemins comme "``Serveurs Linux\/Unix``".

La seconde forme (chemin relatif) permet d'ajouter l'équipement à tous les
groupes dont le nom vaut celui indiqué, quelque soit leur position dans
l'arbre. Il n'est pas possible de préciser plusieurs éléments (par exemple
"``A/B``") lorsque cette forme est utilisée. Les règles d'échappement de la
première forme s'appliquent également ici.

..  note::
    Les groupes sont utilisés pour décider de la ventilation des équipements
    sur les différents groupes de supervision. Une fois tous les groupes
    exprimés sous la forme d'un chemin absolu, VigiConf suppose que le premier
    élément du chemin correspond au groupe à utiliser pour la ventilation.
    En cas de conflit, ou pour placer l'équipement dans un autre groupe de
    ventilation que celui déterminé automatiquement, vous devez utiliser
    l'attribut *ventilation* de la balise *host* afin de spécifier manuellement
    le groupe de ventilation à utiliser.

Balise "``weight``"
^^^^^^^^^^^^^^^^
Syntaxe:

..  sourcecode:: xml

    <weight>valeur</weight>

La balise ``weight`` permet de paramétrer le poids affecté à un hôte.

Balise "``default_service_weight``"
^^^^^^^^^^^^^^^^
Syntaxe:

..  sourcecode:: xml

    <default_service_weight>valeur</default_service_weight>

La balise ``default_service_weight`` permet d'affecter un poids par défaut aux
services de l'hôte.

Balise "``default_service_warning_weight``"
^^^^^^^^^^^^^^^^
Syntaxe:

..  sourcecode:: xml

    <default_service_warning_weight>valeur</default_service_warning_weight>

La balise ``default_service_warning_weight`` permet d'affecter un poids par
défaut aux services de l'hôte lorsque ceux-ci sont dans l'état WARNING.

Remarques
^^^^^^^^^
De même que pour les tests, l'hôte peut disposer de directives de configuration
spécifiques destinées à Nagios. Celles-ci seront groupées sous une balise
``nagios`` (voir également la documentation concernant la balise ``test``
ci-dessus).

Chaque hôte hérite implicitement d'un modèle appelé "``default``". Toutes les
directives définies dans le modèle "``default``" sont donc appliquées à la
configuration des différents hôtes, et ce même si ces hôtes n'indiquent pas
explicitement qu'ils utilisent ce modèle, via la balise ``<template>``. Voir le
chapitre  pour plus d'information.


.. _hosttemplate:

Configuration des modèles d'hôtes
---------------------------------

Le dossier "``hosttemplates``" contient les fichiers de définition des modèles
d'hôtes. Un modèle d'hôtes permet de regrouper un ensemble d'éléments de
configuration communs à plusieurs hôtes. Les hôtes peuvent ensuite être
déclarés comme héritant de ce modèle. Tous les fichiers XML de ce dossier sont
analysés et doivent contenir la définition d'un ou plusieurs modèles.

La balise à la racine de ce document se nomme "``hosttemplates``" et peut
contenir un ou plusieurs blocs "``hosttemplate``", correspondant chacun à la
définition d'un hôte.

Le fragment de code suivant rappelle la structure générale du fichier:

..  sourcecode:: xml

    <?xml version="1.0"?>
    <hosttemplates>
        <hosttemplate attr1="..." attr2="..." attrN="..."> ... </hosttemplate>
        <hosttemplate attr1="..." attr2="..." attrN="..."> ... </hosttemplate>
    ...
    </hosttemplates>

Un bloc de données ``hosttemplate`` possède les attributs suivants:

- ``name``: Nom du modèle.

Un bloc de données *hosttemplate* contient les blocs suivants, en respectant l'ordre:

- ``parent`` (0 ou un)
- ``attribute`` (0 ou plus)
- ``group`` (0 ou plus)
- ``class`` (0 ou plus)
- ``test`` (0 ou plus)
- ``nagios`` (0 ou un)
- ``item`` (0 ou plus)

Balise "``parent``"
^^^^^^^^^^^^^^^^^^^
Un bloc de données ``parent`` contient une simple chaîne de caractères, le nom
du template dont ce template hérite. Il est possible de créer autant de niveaux
d'héritage de templates que souhaité et chaque template peut hériter d'un ou
plusieurs templates (héritage multiple).

Exemple:

..  sourcecode:: xml

    <parent>generic</parent>

Balise "``attribute``"
^^^^^^^^^^^^^^^^^^^^^^
Un bloc de données ``attribute`` possède un attribut : ``name``.

Un bloc de données ``attribute`` contient une valeur de type chaîne de
caractères.

Exemple:

..  sourcecode:: xml

    <attribute name="snmpOIDsPerPDU">10</attribute>

Balise "``group``"
^^^^^^^^^^^^^^^^^^
Un bloc de données ``group`` contient une chaîne de caractères.

Exemple:

..  sourcecode:: xml

    <group>AIX servers</group>

Balise "``class``"
^^^^^^^^^^^^^^^^^^
Un bloc de données ``class`` contient une simple chaîne de caractère.

Exemple:

..  sourcecode:: xml

    <class>aix</class>

Balise "``test``"
^^^^^^^^^^^^^^^^^
Un bloc de données ``test`` possède les attributs suivants :

- ``name`` (1 exactement)
- ``weight`` (0 ou 1 exactement)
- ``warning_weight`` (0 ou 1 exactement)

Un bloc de données ``test`` contient les blocs suivants, dans l'ordre :

- ``arg`` (0 ou plus)
- ``nagios`` (0 ou 1)

Reportez-vous à la documentation sur la `configuration des tests d'un hôte`_
pour plus d'information sur les attributs et blocs acceptés par cette balise.

Exemple:

..  sourcecode:: xml

    <test name="Errpt" weight="42"/>
    <test name="Proc">
      <arg name="label">aixmibd</arg>
      <arg name="processname">.*aixmibd .*</arg>
      <nagios> ... </nagios>
    </test>

Balise "``nagios``"
^^^^^^^^^^^^^^^^^^^
Voir la définition utilisée pour la balise ``host`` : :ref:`nagiostag`.

Balise "``item``"
^^^^^^^^^^^^^^^^^
Un bloc de données ``item`` contient une simple chaîne de caractère.

Exemple:

..  sourcecode:: xml

    <item>item1</item>


Cas particulier du modèle "``default.xml``"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Le modèle nommé "``default.xml``" est un cas particulier de modèle. Il est
appliqué systématiquement à tous les hôtes configurés.

Par défaut, ce modèle contient des attributs destinés à configurer le
comportement de Nagios et à renseigner certaines informations relatives à la
configuration de SNMP sur le parc. Il contient également le test "``UpTime``"
qui envoie une alerte lorsque la durée de fonctionnement d'une machine est trop
faible (c'est-à-dire lorsqu'elle a été redémarrée récemment).


Dossier "``topologies``"
------------------------

Le dossier "``topologies``" contient les fichiers de définition des dépendances
topologiques. Tous les fichiers XML de ce dossier sont analysés et doivent
contenir la définition d'une ou plusieurs dépendances.

La balise à la racine de ce document se nomme "``topologies``" et peut contenir
un ou plusieurs blocs "``topology``", correspondant chacun à la définition d'un
groupe de dépendances.

Le fragment de code suivant rappelle la structure générale du fichier:

..  sourcecode:: xml

    <?xml version="1.0"?>
    <topologies>
      <topology attr1="..." attr2="..." attrN="..."> ... </topology>
      <topology attr1="..." attr2="..." attrN="..."> ... </topology>
      ...
    </topologies>

Balise "``topology``"
^^^^^^^^^^^^^^^^^^^^^
Un bloc de données ``topology`` possède les attributs suivants :

- ``host`` : le nom de l'hôte auquel ajouter des dépendances.
- ``service`` (optionnel) : le nom du service auquel ajouter des dépendances.
  Si cet attribut est omis, les dépendances portent directement sur l'hôte
  indiqué par l'attribut ``host``.

Cette balise peut contenir 1 ou plusieurs balises "``depends``" indiquant de
quoi cet élément dépend. La balise "``depends``" possède deux attributs :

- ``host`` : le nom de l'hôte duquel cet élément dépend.
- ``service`` (optionnel) : le nom du service duquel dépend cet élément. Si cet
  attribut est omis, l'élément dépend directement de l'hôte indiqué par
  l'attribut ``host`` de cette balise.

Exemple:

..  sourcecode:: xml

    <topology host="host1" service="service1">
      <depends host="router.example.com" />
      <depends host="router2.example.com" service="Interface eth0" />
    </topology>

Dans cet exemple, le service "``service1``" de l'hôte "``host1``" est marqué
comme dépendant de l'hôte "``router.example.com``" (un routeur) et du service
"``Interface eth0``" de l'hôte "``router2.example.com``" (un second routeur).


Dossier "``groups``"
--------------------

Le dossier "``groups``" contient les fichiers de définition des groupes
d'éléments supervisés. Tous les fichiers XML de ce dossier sont analysés et
doivent contenir la définition d'un ou plusieurs groupes.

L'utilisation de groupes facilite la gestion au quotidien des permissions
(application en masse d'une permission sur un groupe d'éléments supervisés à un
groupe d'utilisateurs).

La balise à la racine de ce document se nomme "``groups``" et peut contenir un
ou plusieurs blocs "``group``", correspondant chacun à la définition d'un
groupe d'éléments supervisés.

Le fragment de code suivant rappelle la structure générale du fichier:

..  sourcecode:: xml

    <?xml version="1.0"?>
    <groups>
      <group attr1="..." attr2="..." attrN="..."> ... </group>
      <group attr1="..." attr2="..." attrN="..."> ... </group>
      ...
    </groups>

Balise "``group``"
^^^^^^^^^^^^^^^^^^
Un bloc de données ``group`` possède un attribut: ``name``.

Le bloc de données ``group`` peut possèder un ou plusieurs sous-blocs
``group``. Cette imbrication peut être répétée autant de fois que nécessaire et
permet de construire une hiérarchie de groupes. Cette hiérarchie est ensuite
utilisée dans les différentes interfaces, pour la gestion des permissions, ou
encore, pour organiser les informations.

Exemple:

..  sourcecode:: xml

    <group name="group1" />

    <group name="group2" >
      <group name="group21"/>
      ...
    </group>

Le même nom de groupe ne peut pas être utilisé plusieurs fois au même niveau
dans la hiérarchie des groupes. C'est-à-dire que l'exemple suivant est
interdit:

..  sourcecode:: xml

    <!-- Attention, cet exemple ne fonctionne pas ! -->
    <group name="group1">
        <group name="group2"/>
        <group name="group2"/>
    </group>

En revanche, le même nom de groupe peut être utilisé dans des endroits séparés
de l'arborescence, comme dans l'exemple ci-dessous:

..  sourcecode:: xml

    <group name="group1">
        <group name="group1">
            <group name="group1"/>
        </group>
    </group>

Notez que chacun des "``group1``" correspond à un groupe différent.


..  _`hlservices`:

Dossier "``hlservices``"
------------------------

Le dossier "``hlservices``" contient les fichiers de définition des services de
haut niveau. Tous les fichiers XML de ce dossier sont analysés et doivent
contenir la définition d'un ou plusieurs services de haut niveau.

Un service de haut niveau permet de représenter un élément virtuel du parc,
c'est-à-dire pour lequel il n'y a pas de test direct possible. Les services de
haut niveau sont généralement utilisés pour représenter un mécanisme
d'équilibrage de charge (load-balancing) ou de redondance (failover) entre des
équipements du parc.

La balise à la racine de ce document se nomme "``hlservice``" et peut contenir
un ou plusieurs blocs "``hlservice``", correspondant chacun à la définition
d'un groupe d'éléments supervisés.

Le fragment de code suivant rappelle la structure générale du fichier:

..  sourcecode:: xml

    <?xml version="1.0"?>
    <hlservices>
      <hlservice attr1="..." attr2="..." attrN="..."> ... </hlservice>
      <hlservice attr1="..." attr2="..." attrN="..."> ... </hlservice>
      ...
    </hlservices>

Balise "``hlservice``"
^^^^^^^^^^^^^^^^^^^^^^
Un bloc de données ``hlservice`` possède un attribut: ``name``.

Un bloc de données ``hlservice`` contient les blocs de données suivants, dans l'ordre :

- message (1 exactement)
- warning_threshold (1 exactement)
- critical_threshold (1 exactement)
- unknown_priority (0 ou 1 exactement)
- warning_priority (0 ou 1 exactement)
- critical_priority (0 ou 1 exactement)
- operator (1 exactement)
- weight (0 ou 1 exactement)
- warning_weight (0 ou 1 exactement)
- group (0 ou plus)
- depends (1 ou plus)

.. sourcecode:: xml

    <hlservice name="hlservice1">
      <message>Message à afficher</message>
      <warning_threshold>20</warning_threshold>
      <critical_threshold>10</critical_threshold>
      <unknown_priority>8</unknown_priority>
      <warning_priority>6</warning_priority>
      <critical_priority>10</critical_priority>
      <operator>PLUS</operator>
      <weight>42</weight>
      <warning_weight>21</warning_weight>
      <group>hlsgroup1</group>
      <group>hlsgroup2</group>
      <depends host="routeur1.example.com" service="Interface eth0"/>
    </hlservice>

Balise "``message``"
^^^^^^^^^^^^^^^^^^^^
Le bloc de données ``message`` contient une chaîne de caractère libre. Il
s'agit du message à afficher lorsque le service passe dans un état autre que
OK.

Exemple:

..  sourcecode:: xml

    <message>Le service %(service)s a changé d'état</message>

Vous pouvez également utiliser l'une des variables de substitution suivante :

%(state)s
    L'état du service de haut niveau, sous forme de texte (ex : "``CRITICAL``").

%(service)s
    Le nom du service de haut niveau (ex : "``hlservice1``").

%(weight)r
    Le poids courant associé a ce service de haut niveau sous forme d'entier ou
    "``None``" s'il est inconnu.

%(critical_threshold)d
    Le seuil sous lequel les alertes passent dans l'état "``CRITICAL``".

%(warning_threshold)d
    Le seuil sous lequel les alertes passent dans l'état "``WARNING``".

%(operator)s
    L'opérateur de dépendance du service de haut niveau. Vaut "``+``" pour le
    type ``PLUS``, "``&``" pour le type ``AND`` ou "``|``" pour le type ``OR``.

%(active_deps)r
    Le nombre de dépendances encore fonctionnelles de ce service de haut niveau
    ou "``None``" si inconnu.

%(total_deps)d
    Le nombre de dépendances totales de ce service de haut niveau,
    sous forme d'entier.

%(dep_hostname)s
    Le nom de l'hôte de la dépendance qui a entraîné un changement de l'état
    de ce service de haut niveau. Si la dépendance qui a entraîné le changement
    d'état est un autre service de haut niveau, ce champ vaudra ``None``.

%(dep_servicename)s
    Le nom du service de la dépendance qui a entraîné un changement de l'état
    de ce service de haut niveau. Si la dépendance qui a entraîné le changement
    d'état est un hôte, ce champ vaudra ``None``.

Balise "``warning_threshold``"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Le bloc de données ``warning_threshold`` contient un entier, correspondant au
seuil sous lequel le service de haut niveau passe dans l'état WARNING.

Exemple:

..  sourcecode:: xml

    <warning_threshold>2</warning_threshold>

Balise "``critical_threshold``"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Le bloc de données ``critical_threshold`` contient un entier, correspondant au
seuil sous lequel le service de haut niveau passe dans l'état CRITICAL.

Exemple:

..  sourcecode:: xml

    <critical_threshold>1</critical_threshold>

Balise "``unknown_priority``"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Le bloc de données ``unknown_priority`` contient un entier, correspondant
à la priorité associée à ce serveur de niveau lorsque celui-ci passe dans
l'état ``UNKNOWN``.

Exemple:

..  sourcecode:: xml

    <unknown_priority>4<unknown_priority/>

Cette valeur est utilisée pour déterminer la priorités des alertes et
influencer l'ordre d'apparition des alertes dans le bac à événements
(VigiBoard).

Balise "``warning_priority``"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Le bloc de données ``unknown_priority`` contient un entier, correspondant
à la priorité associée à ce serveur de niveau lorsque celui-ci passe dans
l'état ``WARNING``.

Exemple:

..  sourcecode:: xml

    <warning_priority>4<warning_priority/>

Cette valeur est utilisée pour déterminer la priorités des alertes et
influencer l'ordre d'apparition des alertes dans le bac à événements
(VigiBoard).

Balise "``critical_priority``"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Le bloc de données ``unknown_priority`` contient un entier, correspondant
à la priorité associée à ce serveur de niveau lorsque celui-ci passe dans
l'état ``CRITICAL``.

Exemple:

..  sourcecode:: xml

    <critical_priority>4<critical_priority/>

Cette valeur est utilisée pour déterminer la priorités des alertes et
influencer l'ordre d'apparition des alertes dans le bac à événements
(VigiBoard).

Balise "``operator``"
^^^^^^^^^^^^^^^^^^^^^
Le bloc de données ``operator`` décrit le type d'opération appliquée
aux dépendances de ce service de haut niveau, parmi les valeurs suivantes :

"``PLUS``" ou "``+``"
    Le poids courant du service de haut niveau correspond à la somme des poids
    de ses dépendances actives. Ce type de dépendance permet de représenter
    une situation de répartition de charge.

"``OR``" ou "``|``"
    Le poids courant du service de haut niveau correspond au maximum des poids
    de ses dépendances actives. Ce type de dépendance permet de représenter
    une situation de redondance (haute-disponibilité).

"``AND``" ou "``&amp;``"
    Le poids courant du service de haut niveau correspond au minimum des poids
    de ses dépendances actives. Ce type de dépendance permet de décrire
    des dépendances fonctionnelles et d'être averti rapidement lorsque l'une
    des dépendances du service de haut niveau tombe en panne.

    ..  note::
        Cet opérateur est représenté par le symbole "``&``".
        Néanmoins, ce symbole joue un rôle spécial en XML et doit donc être
        échappé (représenté par une entité XML) avant d'être utilisé, comme
        dans l'exemple suivant :

        ..  sourcecode:: xml

            <operator>&amp;</operator>

Balise "``weight``"
^^^^^^^^^^^^^^^^^^^^^
Le bloc de données ``weight`` contient le poids apporté par ce service de haut
niveau lorsqu'il se trouve dans un état supposé nominal. La valeur indiquée
dans cette balise doit être un entier positif. La valeur par défaut lorsque
la balise est absente est 1.

Exemple:

..  sourcecode:: xml

    <weight>42</weight>

..  note::
    Vigilo est optimiste quant à l'état des éléments du parc. De fait, cette
    valeur est utilisée aussi bien lorsque le service se trouve dans l'état
    OK (état nominal) que lorsqu'il se trouve dans l'état UNKNOWN (état inconnu,
    supposé nominal).

Balise "``warning_weight``"
^^^^^^^^^^^^^^^^^^^^^^^^^^^
Le bloc de données ``warning_weight`` contient le poids apporté par ce service
de haut niveau lorsqu'il se trouve dans un état dégradé (WARNING).
La valeur indiquée dans cette balise doit être un entier positif, inférieur
ou égal à celui donné dans la balise ``weight``. La valeur par défaut lorsque
la balise est absente est la même que pour la balise ``weight``.

Exemple:

..  sourcecode:: xml

    <warning_weight>42</warning_weight>

Balise "``group``"
^^^^^^^^^^^^^^^^^^
Le bloc de données ``group`` contient le nom du groupe auquel ce service de
haut niveau appartient.

Exemple:

..  sourcecode:: xml

    <group>hlsgroup1</group>

Balise "``depends``"
^^^^^^^^^^^^^^^^^^^^
Le bloc de données ``depends`` correspond à la description d'une dépendance de
ce service de haut niveau. Il possède deux attributs :

- ``host`` : (optionnel) le nom de l'hôte dont dépend ce service de haut
  niveau. Si omis, alors ce service de haut niveau dépend d'un autre service de
  haut niveau dont le nom est donné par l'attribut ``service``.
- ``service`` : (optionnel) le nom du service dont dépend ce service de haut
  niveau. Si omis, alors ce service de haut niveau dépend directement de l'hôte
  dont le nom est donné par l'attribut ``host``.

Exemple d'une dépendance sur un hôte:

..  sourcecode:: xml

    <depends host="foo.example.com"/>

Exemple d'une dépendance sur un service technique (de bas niveau):

..  sourcecode: xml

    <depends host="router.example.com" service="Interface eth0"/>

Exemple d'une dépendance sur un autre service de haut niveau:

..  sourcecode:: xml

    <depends service="hlservice2"/>



Configurations particulières
============================

Ce chapitre recense des cas particuliers de configuration. Pour chaque cas, un
exemple de configuration associée est donné.


Utilisation de SNMPv3
---------------------

L'utilisation de SNMP version 3 nécessite un peu plus de configuration que pour
SNMP version 1 ou 2c. En effet, en plus de la définition de la communauté de
l'équipement, il est nécessaire de spécifier les éléments de sécurité
permettant d'authentifier la connexion à l'équipement et/ou d'assurer la
confidentialité des échanges SNMP avec l'équipement.

Aucun test particulier n'est à appliquer pour utiliser SNMPv3 dans Vigilo.
Cependant, des attributs supplémentaires doivent être définis au niveau de la
configuration de l'équipement fonctionnant avec SNMPv3.

Le listing suivant présente un exemple de configuration d'un hôte devant être
interrogé en utilisant SNMPv3:

..  sourcecode:: xml

    <attribute name="snmpVersion">3</attribute>
    <attribute name="snmpSeclevel">authPriv</attribute>
    <attribute name="snmpAuthproto">MD5</attribute>
    <attribute name="snmpPrivproto">DES</attribute>
    <attribute name="snmpSecname">snmpuser1</attribute>
    <attribute name="snmpAuthpass">12345678</attribute>
    <attribute name="snmpPrivpass">12345678</attribute>

Les noms des attributs suivent la terminologie standard de SNMPv3, excepté pour
le préfixe "``snmp``" qui ne sert qu'à empêcher d'éventuels conflits de nommage
avec d'autres attributs similaires.

Le rôle de chacun de ces attributs est précisé ci-dessous :

- L'attribut "``snmpVersion``" indique que c'est la version 3 du protocole SNMP
  qui doit être utilisée pour interroger l'équipement.
- L'attribut "``snmpSeclevel``" indique les contraintes de sécurité à apporter
  sur les communications avec l'équipement. Les valeurs possibles sont :

  - "``noAuthNoPriv``" (no authentication / no privacy) : aucune authentification
    n'a lieu et les échanges ne sont pas chiffrés. Cette valeur correspond à ce
    qui est fourni par SNMPv1 et SNMPv2c et n'offre **aucune sécurité**. Il est
    donc recommandé de **ne pas utiliser cette valeur** (sauf cas exceptionnels).
  - "``authNoPriv``" (authentication / no privacy) : Vigilo s'authentifiera
    auprès de l'équipement avec un nom d'utilisateur et un mot de passe dédiés.
    Les échanges avec l'équipement ne seront pas chiffrés et les communications
    pourront donc être écoutées par n'importe quelle personne disposant d'un
    accès physique au réseau.
  - "``authPriv``" (authentication / privacy) : Vigilo s'authentifiera auprès
    de l'équipement avec un nom d'utilisateur et un mot de passe dédiées. De
    plus, tous les échanges seront chiffrés. Cette valeur est celle offrant le
    plus de sécurité et est donc recommandée.

- L'attribut "``snmpAuthproto``" est obligatoire lorsque "``snmpSeclevel``"
  vaut "``authNoPriv``" ou "``authPriv``" et spécifie l'algorithme utilisé pour
  masquer le mot de passe lors des transmissions avec l'équipement. Les valeurs
  possibles sont "``MD5``" et "``SHA1``".
- L'attribut "``snmpPrivproto``" est obligatoire lorsque "``snmpSeclevel``"
  vaut "``authPriv``" et spécifie l'algorithme de chiffrement utilisé pour les
  échanges avec l'équipement. Les valeurs possibles sont "``DES``" et
  "``AES``".
- L'attribut "``snmpSecname``" est obligatoire lorsque "``snmpSeclevel``" vaut
  "``authNoPriv``" ou "``authPriv``" et indique le nom d'utilisateur avec
  lequel Vigilo s'authentifiera auprès de l'équipement.
- L'attribut "``snmpAuthpass``" est obligatoire lorsque "``snmpSeclevel``" vaut
  "``authNoPriv``" ou "``authPriv``" et indique le mot de passe à utiliser pour
  s'authentifier auprès de l'équipement. Il peut être donné sous forme
  textuelle (comme dans l'exemple ci-dessus) ou sous forme de chaîne de
  caractères hexadécimaux en préfixant la valeur par "``0x``".
- L'attribut "``snmpPrivpass``" est obligatoire lorsque "``snmpSeclevel``" vaut
  "``authPriv``" et spécifie la clé de chiffrement utilisée pour les échanges
  avec l'équipement. Elle peut être donnée sous forme textuelle (comme dans
  l'exemple ci-dessus) ou sous forme de chaîne de caractères hexadécimaux en
  préfixant la valeur par "``0x``".


Détection de la corruption de la base de données de Vigilo
----------------------------------------------------------

Le test "``VigiloDatabase``" permet de tester l'état de la base de données de
Vigilo pour détecter d'éventuels problèmes (par exemple, une corruption des
données).

Il peut être utilisé depuis n'importe quelle machine capable de se connecter à
la base de données. Nous recommandons cependant d'appliquer le test directement
à la machine qui héberge la base de données, et ce afin de minimiser la durée
d'exécution du test (latence du réseau).

Le listing suivant présente un exemple de configuration de ce test:

..  sourcecode:: xml

    <test name="VigiloDatabase">
      <arg name="command">
        psql -Anqt -c "%s" "user=vigilo dbname=vigilo host=localhost"
      </arg>
      <arg name="strict">True</arg>
      <arg name="force">True</arg>
      <arg name="prefix">vigilo_</arg>
    </test>

Les paramètres de ce test sont :

- La commande (paramètre "``command``") à utiliser pour se connecter à la base
  de données depuis la ligne de commande. Cette commande **DOIT** contenir
  toutes les informations nécessaires pour se connecter à la base de données
  (nom d'utilisateur, adresse de la machine, port du serveur de base de données
  si différent du port par défaut, nom de la base de données, mot de passe),
  ainsi que les options permettant d'obtenir un formatage "``brut``" des
  résultats (dans le cas de PostgreSQL, les options "``-Anqt``" ont cet effet).
  Enfin, la commande passée en paramètre **DOIT** contenir la séquence de
  formatage « %s » et les options permettant de passer une requête SQL à la
  commande sur la ligne de commande (pour PostgreSQL, il s'agit de l'option
  "``-c``"). La séquence « %s » sera remplacée dynamiquement par une série de
  requêtes SQL destinées à vérifier l'intégrité de la base de données.
- Un drapeau optionnel (paramètre "``strict``") qui indique le comportement à
  adopter lorsque des éléments inattendus sont trouvés dans le schéma de la
  base de données (par exemple, des tables/vues supplémentaires). Par défaut,
  cette option vaut *False*. Lorsque ce drapeau est actif, la présence d'objets
  supplémentaires lève un avertissement (WARNING) dans Nagios et Vigilo.

  ..    warning::
        N'activez pas ce drapeau lorsque vous utilisez un modèle personnalisé
        pour Vigilo (par exemple, intégrant des tables de liaison vers d'autres
        outils). Dans le cas contraire, un avertissement sera systématiquement
        levé par ce test.

- Un drapeau optionnel (paramètre "``force``") qui permet de vérifier le schéma
  pour des versions non supportées par le test. Lorsque ce drapeau est actif et
  que la version du schéma de la base de données Vigilo n'est pas supportée par
  ce test, la version la plus proche est utilisée pour effectuer les
  vérificatiions.

  ..    warning::
        Ce drapeau doit être utilisé avec parcimonie. Ne l'utilisez que lorsque
        le schéma de la base de données est en cours de migration vers une
        nouvelle version et que la nouvelle version du test VigiloDatabase
        n'a pas encore été déployée sur les serveurs de collecte pour prendre
        en charge cette nouvelle version du schéma.

- Un préfixe optionnel (paramètre "``prefix``") utilisé devant les noms de
  toutes les tables de Vigilo. Il s'agit du même préfixe que celui défini dans
  l'option "``db_basename``" du fichier settings.ini de VigiConf (voir chapitre
  ). Par défaut, la valeur de l'option "``db_basename``" dans le fichier de
  configuration de VigiConf est utilisée automatiquement.

Mise en place des mails d'alertes pour les problèmes de bus
-----------------------------------------------------------

- Choisir le destinataire final (ex: ``foo@bar.com``)

- Mise en place dans le fichier
  :file:`/etc/nagios/vigilo.d/vigilo-enterprise.cfg`
  du contact ``last-chance-contact`` il faut remplacer ``root@localhost`` par
  le mail choisi:

..  sourcecode:: nagios

    define contact{
        contact_name                    last-chance-contact
        alias                           Contact urgence Vigilo
        service_notification_period     24x7
        host_notification_period        24x7
        service_notification_options    w,u,c,r
        host_notification_options       u,d,r
        service_notification_commands   notify-service-by-email
        host_notification_commands      notify-host-by-email
        ; Remplacer "foo@bar.com" par l'adresse email du contact.
        email                           foo@bar.com
    }

- Vérifier qu'un mail peut-être envoyé via la commande suivante remplaçant
  l'adresse email par ce qui a été choisi:

..  sourcecode:: bash

    echo testbody | /bin/mail -s testobject foo@bar.com

- Mise en place du template avec le contact pour le bus via les templates
  suivant ``vigilo_bus`` il faudra importer dans la définition de l'hôte
  utiliser le template comme ceci:

..  sourcecode:: xml

    <template name="vigilo_bus"/>


..  : Inclusion de la documentation concernant
..  : la configuration des journaux.

..  include:: ../../common/doc/admin-logs.rst


Utilisation de l'utilitaire "``vigiconf``"
==========================================

La génération des fichiers de configuration des différentes applications en
charge de la supervision du parc se fait en utilisant l'utilitaire
"``vigiconf``" fourni lors de l'installation du paquet portant le même nom.

Cet utilitaire permet d'effectuer les opérations suivantes :

- Affichage des informations concernant la configuration actuelle ;
- Gestion des applications ;
- Retour arrière de la configuration ;
- Déploiement d'une nouvelle configuration ;
- Découverte des services présents sur le réseau.

La commande "``vigiconf --help``" permet d'obtenir l'aide de l'utilitaire. Elle
affiche la sortie suivante:

..  sourcecode:: bash

    usage : vigiconf [-h] [--debug] {info,server-status,discover,deploy} ...

    Gestionnaire de configuration Vigilo

    arguments optionnels:
    -h, --help affiche ce message d'aide et quitte
    --debug Mode de débogage

    Sous-commandes: {info,server-status,discover,deploy}

    info           Affiche un résumé de la configuration actuelle.
    deploy         Déploie la configuration sur chaque serveur si la
                   configuration a changé.
    discover       Découvrir les services disponibles sur un serveur
                   distant.
    server-status  Active ou désactive un serveur Vigilo.

Ces différentes opérations sont détaillées dans les sections qui suivent.

Vous pouvez obtenir l'aide sur une commande en tapant
"``vigiconf nom_de_la_commande --help``".


Affichage des informations
--------------------------

L'affichage des informations concernant la configuration actuelle se fait en
exécutant la commande "``vigiconf info``".

La commande renvoie plusieurs informations, comme dans l'exemple
d'exécution suivant:

..  sourcecode:: bash

    VigiConf a été lancé depuis le compte 'root'. Utilisation du compte 'vigiconf' à la place.
    Révision actuelle dans le dépôt : 358
    Serveur supserver1.example.com:
        déployé: 358
        installé: 358
        précédent: 358
    Serveur supserver2.example.com:
        déployé: 358
        installé: 358
        précédent: 358
        DÉSACTIVÉ
    VigiConf se termine

La révision actuelle correspond à la dernière version de la configuration
validée sur la machine qui héberge VigiConf.

Les lignes suivantes affichent, pour chaque serveur de supervision : son nom,
éventuellement son état (lorsque le serveur est désactivé), ainsi que les
numéros de la révision de la configuration actuellement déployée (donc en
production), de la dernière révision installée et de la précédente révision
installée.

Vous pouvez préciser les noms des serveurs de supervision dont les informations
doivent être affichés en passant simplement leur nom comme argument de la
commande.

..  note::
    Toutes les valeurs sont à 0 lors d'une nouvelle installation (car aucun
    des serveurs n'a encore été configuré).

Déploiement de la configuration
-------------------------------

Une fois la configuration des différents éléments du parc effectuées, vous
pouvez la déployer sur les divers machines de la supervision à l'aide de la
commande "``vigiconf deploy``".

Vous pouvez passer en argument la liste des noms des serveurs de supervision
pour lesquels une nouvelle version de la configuration doit être déployée.

..  _`discover`:

Découverte des services à superviser sur un hôte
------------------------------------------------

Afin d'assister l'administrateur dans sa configuration des tests de supervision
d'un serveur, VigiConf dispose d'un mode de découverte automatique des services
disponibles sur un hôte.

La commande "``vigiconf discover``" prend en arguments les noms d'hôtes
(entièrement qualifiés) ou les fichiers de scan à analyser afin de découvrir
les services à superviser. Les fichiers de scan doivent avoir été générés à
l'aide de la commande "``snmpwalk``" sur l'OID "``.1``" en lui passant les
options "``-OnQe``".

Exemple de commande pour créer le fichier de scan:

..  sourcecode:: bash

    SNMPCONFPATH=/dev/null snmpwalk -OnQe -v2c -c public hostname .1 \
        > hostname-OnQe.walk

..  note::
    "``SNMPCONFPATH=/dev/null``" permet d'éviter l'import d'options
    de configuration depuis des fichiers du système tels que :

    - :file:`/etc/snmp/snmp.local.conf`
    - :file:`/etc/snmp/snmp.conf`

Par défaut, cette commande affiche sur la sortie standard le fichier de
configuration XML correspondant aux équipements analysés. Le listing suivant
présente le résultat d'une telle analyse:

..  sourcecode:: xml

    <?xml version="1.0"?>
    <host address="127.0.0.1" name="localhost.localdomain">
      <group>Servers</group>
      <class>ucd</class>
      <test name="Users" />
      <test name="Partition">
        <arg name="partname">/home</arg>
        <arg name="label">/home</arg>
      </test>
      <test name="Partition">
        <arg name="partname">/</arg>
        <arg name="label">/</arg>
      </test>
      <test name="TotalProcesses" />
      <test name="Swap" />
      <test name="CPU" />
      <test name="Load" />
      <test name="RAM" />
      <test name="UpTime" />
      <test name="TCPConn" />
      <test name="InterrCS" />
    </host>

Le résultat de cette commande peut être enregistré directement dans un fichier
de configuration XML afin d'être lu ensuite par VigiConf en utilisant l'option
"``-o``" suivie de l'emplacement du fichier dans lequel le résultat doit être
sauvegardé.

La découverte peut-être limitée à un test en particulier via l'option "``-t``".

Activation / désactivation d'un serveur de supervision
------------------------------------------------------

La commande "``vigiconf server-status``" permet d'activer ou de désactiver un
ou plusieurs serveurs de la plate-forme de supervision. Elle doit être appelée
avec au moins 2 arguments.

Le 1er argument indique l'action à effectuer et peut valoir :

- "``enable``" pour activer un ou plusieurs serveurs de supervision
  précédemment désactivés.
- "``disable``" pour désactiver un ou plusieurs serveurs de supervision.


Annexes
=======

Tests de supervision disponibles dans Vigilo
--------------------------------------------

Le tableau suivant recense les tests de supervision disponibles dans Vigilo.

..  include:: suptests.rst

Messages d’erreurs/d’alerte/d’informations
------------------------------------------

Ce chapitre recense les messages d'erreurs les plus courants que vous êtes
susceptibles de rencontrer, ainsi que la méthode de résolution de ces
problèmes.

VigiConf n'a pas été lancé en utilisant le compte 'vigiconf'. Abandon.
    Afin de garantir la sécurité du système, VigiConf doit être exécuté en tant
    qu'utilisateur "``vigiconf``". Ce message d'erreur s'affiche lorsque cette
    condition n'est pas remplie et VigiConf refuse de s'exécuter. Le compte
    "``root``" peut également être utilisé pour exécuter VigiConf (dans ce cas,
    l'application commencera par basculer vers le compte "``vigiconf``" avant
    de lâcher ses privilèges). L'utilisation du compte "``root``" pour démarrer
    VigiConf en production est déconseillée.

VigiConf a été lancé depuis le  compte "``root``" (super-utilisateur). Utilisation du compte 'vigiconf' à la place.
    Ce message d'avertissement est affiché lorsque VigiConf est exécuté depuis
    le compte "``root``".

Exemples de configurations d'hôtes particulières
------------------------------------------------

Classes de Service (avec un seul niveau de classe)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

..  sourcecode:: xml

    <host name="_HOSTNAME_" address="X.X.X.X">
      <class>cisco</class>
      <attribute name="QOS_mainClassName">
        <item>mpls-RealTime|RT</item>
        <item>class-default|DE</item>
        <item>mpls-Brocade|BR</item>
        <item>mpls-Bulk|BU</item>
        <item>mpls-BestEffort|BE</item>
      </attribute>

      <test name="Interface">
        <arg name="ifname">eth0</arg>
        <arg name="label">eth0</arg>
      </test>

      <test name="QOS_Interface">
        <arg name="ifname">TenGigabitEthernet4/0/0</arg>
        <arg name="label">Te4/0/0 - QOS</arg>
        <arg name="direction">OUT</arg>
      </test>
      <group>/Servers/Linux servers</group>
    </host>

Classes de Service (avec 2 niveaux de classe)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

..  sourcecode:: xml

    <host name="_HOSTNAME_" address="X.X.X.X">
      <class>cisco</class>
      <attribute name="snmpCommunity">_SNMP_COMMUNITY_</attribute>

      <attribute name="QOS_mainClassName">
        <item>Groupe_1|GR1</item>
        <item>Groupe_2|GR2</item>
        <item>Groupe_3|GR3</item>
      </attribute>

      <attribute name="QOS_subClassName">
        <item>class-default</item>
        <item>telephonie</item>
        <item>Video_Bufferisee</item>
        <item>Video&amp;Donnees_Contraintes</item>
        <item>Services_Reseaux</item>
      </attribute>

      <test name="Interface">
        <arg name="ifname">eth0</arg>
        <arg name="label">eth0</arg>
      </test>

      <test name="QOS_Interface">
        <arg name="ifname">GigabitEthernet0/0</arg>
        <arg name="label">GE0/1</arg>
        <arg name="direction">OUT</arg>
      </test>
      <group>/Servers/Linux servers</group>
    </host>

ToIP
^^^^

..  sourcecode:: xml

    <host name="_HOSTNAME_" address="X.X.X.X">
      <class>toip</class>
      <attribute name="oxe_login">gcharbon</attribute>
      <attribute name="oxe_password">toor</attribute>
      <attribute name="timeout">10</attribute>
      <attribute name="prompt_timeout">5</attribute>

      <test name="Interface">
        <arg name="label">eth0</arg>
        <arg name="ifname">eth0</arg>
      </test>

      <test name="Autocoms">
        <arg name="crystals">42;47</arg>
        <arg name="labels">agence_42;agence_47</arg>
      </test>

      <test name="TrunkAverage">
        <arg name="crystals">205;207;208;</arg>
        <arg name="labels">agence_205;agence_208;agence_208</arg>
        <arg name="crit">42</arg>
      </test>

      <test name="TrunkPlatinium">
        <arg name="crystals">27;28;29;31</arg>
        <arg name="labels">agence_27;agence_28;agence_29;agence_31</arg>
        <arg name="crit">42</arg>
      </test>

      <test name="OxeCard">
        <arg name="crystals">42;47;49</arg>
        <arg name="labels">agence_42;agence_47;agence_49</arg>
      </test>

      <test name="FreePosCard">
        <arg name="hour">15:55:00</arg>
      </test>

      <test name="MevoCapacity">
        <arg name="crit">42</arg>
      </test>

      <test name="TrunkState"/>
      <test name="IpPhones"/>
      <test name="CcdaLicences"/>
      <group>/Servers/Linux servers</group>
    </host>

Traps SNMP
^^^^^^^^^^

..  sourcecode:: xml

    <host name="_HOSTNAME_" address="X.X.X.X">
      <class>linux</class>
      <template>linux</template>
      <attribute name="cpulist">2</attribute>
      <test name="Interface">
        <arg name="label">eth0</arg>
        <arg name="ifname">eth0</arg>
      </test>
      <test name="Trap">
        <arg name="OID">.1.3.6.1.1.2.1.1.2</arg>
        <arg name="command">/var/lib/vigilo/snmptt/get_trap_upload</arg>
        <arg name="service">Upload</arg>
        <arg name="label">Upload</arg>
      </test>
    </host>

NetFlow
^^^^^^^

..  sourcecode:: xml

    <host name="_HOSTNAME_" address="X.X.X.X">
      <class>linux</class>
      <class>netflow</class>
      <template>linux</template>
      <test name="Interface">
        <arg name="label">eth0</arg>
        <arg name="ifname">eth0</arg>
      </test>
      <test name="Netflow">
        <arg name="ip_1">X.X.X.X/24</arg>
        <arg name="ip_2">Y.Y.Y.Y/24</arg>
        <arg name="ip_3">Y.Y.Y.Y/24</arg>
      </test>
      <group>/Servers/Linux servers</group>
    </host>


Glossaire - Terminologie
------------------------

Ce chapitre recense les différents termes techniques employés dans ce document
et donne une brève définition de chacun de ces termes.

.. glossary::

   XML
       eXtensible Markup Language. Langage de balisage extensible.

   URL
       Uniform Resource Locator. Chaîne de caractères permettant d'identifier
       une ressource sur Internet.

   SGBD
       Système de Gestion de Base de Données. Logiciel permettant d'héberger
       une base de données sur la machine.

   SVN
       Subversion, système de contrôle de versions. URL :
       http://subversion.apache.org

.. vim: set tw=79 :
