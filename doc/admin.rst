..  _`manuel_admin`:

*********************
Manuel administrateur
*********************


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

    postgresql://vigilo:vigilo@localhost/vigilo

..  warning::
    À l'heure actuelle, seul PostgreSQL a fait l'objet de tests intensifs.
    D'autres SGBD peuvent également fonctionner, mais aucun support ne
    sera fourni pour ceux-ci.


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

Emplacement du verrou
^^^^^^^^^^^^^^^^^^^^^
Afin d'éviter un conflit lorsque plusieurs administrateurs du même parc
effectuent un nouveau déploiement de la configuration simultanément, VigiConf
acquiert un verrou au démarrage. Ce verrou est automatiquement libéré lors de
l'arrêt de VigiConf.

La directive "``lockfile``" permet de spécifier l'emplacement du fichier qui
correspondra au verrou. Dans la configuration fournie par défaut avec VigiConf,
le verrou est enregistré dans :file:`/var/lock/subsys/vigilo-vigiconf/vigiconf.token`.

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
avec VigiConf. Les attributs suivants sont disponibles :

- "``collectorTimeout``" : délai d'attente utilisé lors de la récupération
  des données SNMP de l'hôte ;
- "``snmpCommunity``" : la communauté pour l'accès SNMP à l'équipement ;
- "``snmpPort``" : le port SNMP à utiliser (par défaut, le port 161 est
  utilisé) ;
- "``snmpVersion``" : la version SNMP à utiliser (par défaut, la version 2 est
  utilisée) ;
- "``snmpOIDsPerPDU``" : le nombre d'éléments qui peuvent être regroupés
  dans une seule requête SNMP. Il s'agit d'un paramètre avancé qui ne
  nécessite généralement pas d'être modifié ;
- "``snmpContext``" : le contexte à interroger pour les échanges basés
  sur SNMP v3. Par défaut, le contexte par défaut est interrogé. Il s'agit
  d'un paramètre avancé qui ne nécessite généralement pas d'être modifié ;
- "``snmpSecLevel``" : le niveau de sécurité attendu pour les échanges
  basés sur SNMPv3 (``noAuthNoPriv``, ``authNoPriv`` ou ``authPriv``) ;
- "``snmpAuthProto``" : l'algorithme d'authentification (``MD5`` ou ``SHA1``)
  pour les échanges basés sur SNMPv3 ;
- "``snmpPrivProto``" : l'algorithme de chiffrement (``DES`` ou ``AES``)
  pour les échanges basés sur SNMPv3 ;
- "``snmpSecname``" : le nom d'utilisateur pour les échanges basés sur SNMPv3 ;
- "``snmpAuthpass``" : la clé d'authentification pour les échanges
  basés sur SNMPv3 ;
- "``snmpPrivpass``" : la clé de chiffrement pour les échanges basés sur SNMPv3.

..  only:: enterprise

    La version enterprise de Vigilo contient les attributs supplémentaires
    suivants :

    - "``prompt_timeout``" : délai d'attente pour l'obtention d'une invite
      de saisie lors de l'établissement des connexions Telnet ;
    - "``QOS_mainClassName``" : la liste des classes de services utilisées pour
      la qualité de service. Pour chaque classe, il est possible de définir le
      libellé affiché dans les graphes, en utilisant la syntaxe
      "nom_de_la_classe|libellé" ;
    - "``QOS_subClassName``" : la liste des sous-classes de services utilisées
      pour la qualité de service. Pour chaque sous-classe, il est possible de
      définir le libellé affiché dans les graphes, en utilisant la syntaxe
      "nom_de_la_sous_classe|libellé" ;
    - "``telnetLogin``" : le nom d'utilisateur permettant de se connecter à l'hôte
      en utilisant le protocole Telnet ;
    - "``telnetPassword``" : le mot de passe allant de paire avec le nom
      d'utilisateur permettant de se connecter à l'hôte en utilisant le
      protocole Telnet ;
    - "``timeout``" : délai d'attente utilisé lors des connexions Telnet
      à l'hôte.


.. _`configuration des tests d'un hôte`:

Balise "``test``"
^^^^^^^^^^^^^^^^^
Syntaxe:

..  sourcecode:: xml

    <test name="nom_de_classe.nom du test">
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
à appliquer (par exemple : "``all.UpTime``" pour superviser la durée de la
disponibilité d'un équipement). Chaque test dispose d'un nom de classe
représentant le type d'équipement ou de modèle d'équipement et un nom de test
qui décrit l'élément à superviser (mémoire, processeur, etc.).
La liste des classes et de leurs tests peut être obtenue en exécutant
la commande suivante ::

    vigiconf list-tests

Un test accepte généralement zéro, un ou plusieurs arguments, qui doivent être
passés dans l'ordre lors de la déclaration du test, à l'aide de la balise
``arg``. Chaque argument dispose d'un nom (attribut ``name``) et d'une valeur
(ou liste de valeurs). Pour spécifier une liste de valeurs pour un argument,
la sous-balise ``item`` doit être utilisée, comme dans l'extrait suivant :

..  sourcecode:: xml

    <test name="my_firewall.ACL">
        <arg name="policy">whitelist</arg>
        <!--
            L'argument "addresses" est une liste d'adresses IP,
            sous-réseaux ou noms de machines.
        -->
        <arg name="addresses">
            <item>127.0.0.1</item>
            <item>localhost</item>
            <item>192.168.0.0/24</item>
        </arg>
    </test>

Chaque argument possède un type (spécifié dans la documentation du test).
Les types reconnus sont :

-   les chaînes de caractères ;
-   les nombres entiers ;
-   les nombres relatifs (flottants) ;
-   les booléens (utiliser la valeur ``1``, ``true``, ``on`` ou ``yes`` pour
    la valeur ``True`` ou bien ``0``, ``false``, ``off`` ou ``no`` pour la
    valeur ``False``).

..  note::
    Si le même argument est défini deux fois, seule la dernière valeur sera
    utilisée.

Par défaut, les valeurs données aux arguments sont normalisées :
les successions de caractères blancs (espace, tabulation, saut de ligne,
retour charriot) sont remplacées par un seul espace et les blancs en début
et en fin de valeur sont supprimés.

Les 2 fragments de configuration suivants sont donc équivalents :

..  sourcecode:: xml

    <test name="Interface">
        <arg name="ifname">eth0</arg>
    </test>

..  sourcecode:: xml

    <test name="Interface">
        <arg name="ifname">
            eth0     </arg>
    </test>

Pour désactiver la normalisation des espaces, utilisez l'attribut ``xml:space``
avec la valeur ``preserve``.

Sur certains équipements du fabricant Nortel par exemple, les noms
des interfaces réseau contiennent des espaces.
La supervision des interfaces de cet équipement est donc possible en utilisant
la syntaxe suivante :

..  sourcecode:: xml

    <test name="Interface">
        <!-- Ici, l'espace à la fin de la valeur fait partie du nom
             de l'interface réseau et doit être conservé. -->
        <arg name="ifname" xml:space="preserve">eth0 </arg>

        <!-- On change le libellé pour obtenir quelque chose qui soit
             exploitable et compatible avec le moteur de collecte. -->
        <arg name="label">eth0</arg>
    </test>

L'attribut ``xml:space`` peut également être utilisé avec les listes
de valeurs :

..  sourcecode:: xml

    <test name="ma_classe.MonTest">
        <arg name="indexes">
            <item xml:space="preserve">foo </item>
            <item xml:space="preserve"> bar</item>
        </arg>
    </test>

..  note::

    L'attribut ``xml:space`` n'est pas hérité de la balise ``arg`` lorsqu'il
    est utilisé avec une liste de valeurs et doit donc être appliqué sur
    chacune des balises ``item`` pour lesquelles il est pertinent.

Vous pouvez également, de façon optionnelle, définir des paramètres spécifiques
pour la supervision à l'aide de la balise ``nagios``, qui contiendra une ou
plusieurs directives adressées au moteur de collecte Nagios. Voir la section
ci-dessous pour plus d'informations.


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
VigiMap. Cette image doit se trouver dans :samp:`/etc/vigilo/vigimap/public/images/tags`.

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
- ``tag`` (0 ou plus)
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

Balise "``tag``"
^^^^^^^^^^^^^^^^
Syntaxe:

..  sourcecode:: xml

        <tag service="service" name="étiquette"/>

        <tag service="service" name="étiquette">valeur</tag>

La balise ``tag`` permet d'affecter une étiquette à un hôte ou un service.
L'attribut ``name`` permet de préciser le nom de l'étiquette à ajouter. Il doit
correspondre au nom d'une image (**privée de son extension**) à afficher dans
VigiMap. Cette image doit se trouver dans :samp:`/etc/vigilo/vigimap/public/images/tags`.

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
Un bloc de données ``group`` contient une chaîne de caractères.

Exemple:

..  sourcecode:: xml

    <group>AIX servers</group>

Balise "``test``"
^^^^^^^^^^^^^^^^^

Un bloc de données ``test`` possède l'attribut suivant :

- ``name`` (1 exactement)

Un bloc de données ``test`` contient les blocs suivants, dans l'ordre :

- ``arg`` (0 ou plus)
- ``nagios`` (0 ou 1)

Reportez-vous à la documentation sur la `configuration des tests d'un hôte`_
pour plus d'information sur les attributs et blocs acceptés par cette balise.

    Exemple:

..  sourcecode:: xml

    <test name="all.Process">
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


..  only:: enterprise

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

..  only:: not enterprise

    Cette fonctionnalité n'est disponible que dans la version Enterprise
    de Vigilo.

..  only:: enterprise

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
        Le poids courant calculé pour ce service de haut niveau sous forme
        d'entier ou "``None``" s'il est inconnu (ie. si le service est dans
        l'état «``UNKNOWN``»).

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
    ce service de haut niveau. Il possède les attributs suivants :

    - ``host`` : (optionnel) le nom de l'hôte dont dépend ce service de haut
      niveau. Si omis, alors ce service de haut niveau dépend d'un autre service de
      haut niveau dont le nom est donné par l'attribut ``service``.

    - ``service`` : (optionnel) le nom du service dont dépend ce service de haut
      niveau. Si omis, alors ce service de haut niveau dépend directement de l'hôte
      dont le nom est donné par l'attribut ``host``.

    - ``weight`` : (optionnel) poids contribué par cette dépendance dans le calcul
      de l'état du service de haut niveau lorsqu'elle se trouve dans un état nominal
      (``OK`` ou ``UP``). Il s'agit d'un entier positif.
      Si cet attribut n'est pas spécifié, le poids associé est 1.

    - ``warning_weight`` : (optionnel) poids contribué par cette dépendance dans le
      calcul de l'état du service de haut niveau lorsqu'elle se trouve dans un état
      dégradé (``WARNING``). Il s'agit d'un entier positif.
      Si cet attribut n'est pas spécifié, le poids associé est le même que celui
      indiqué par l'attribut ``weight`` ou 1 si ``weight`` n'a pas non plus été
      renseigné.

      .. note::

         La valeur configurée dans cet attribut doit toujours être inférieure ou égale
         à celle configurée dans l'attribut ``weight``.

    Exemple d'une dépendance sur un hôte :

    ..  sourcecode:: xml

        <depends host="foo.example.com"/>

    Exemple d'une dépendance sur un service technique (de bas niveau) utilisant
    un poids différent dans l'état ``OK`` et dans l'état ``WARNING`` :

    ..  sourcecode: xml

        <depends host="router.example.com" service="Interface eth0" weight="42" warning_weight="24"/>

    Exemple d'une dépendance sur un autre service de haut niveau dont seul le poids
    dans l'état ``OK`` est spécifié (cette valeur est automatiquement réutilisée
    comme poids dans l'état ``WARNING``) :

    ..  sourcecode:: xml

        <depends service="hlservice2" weight="13"/>



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


..  only:: enterprise

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

        <test name="all.VigiloDatabase">
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

    usage : vigiconf [-h] [--debug] {info,server-status,list-tests,discover,deploy} ...

    Gestionnaire de configuration Vigilo

    arguments optionnels:
    -h, --help affiche ce message d'aide et quitte
    --debug Mode de débogage

    Sous-commandes: {info,server-status,discover,deploy}

    info           Affiche un résumé de la configuration actuelle.
    list-tests     Liste les tests disponibles pour les classes d'hôtes données.
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
      <test name="all.Users" />
      <test name="all.Partition">
        <arg name="partname">/home</arg>
        <arg name="label">/home</arg>
      </test>
      <test name="all.Partition">
        <arg name="partname">/</arg>
        <arg name="label">/</arg>
      </test>
      <test name="all.TotalProcesses" />
      <test name="all.Swap" />
      <test name="ucd.CPU" />
      <test name="ucd.Load" />
      <test name="ucd.RAM" />
      <test name="all.UpTime" />
      <test name="all.TCPConn" />
      <test name="ucd.InterrCS" />
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

..  only:: enterprise

    Exemples de configurations d'hôtes particulières
    ------------------------------------------------

    Classes de Service (avec un seul niveau de classes)
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    ..  sourcecode:: xml

        <host name="_HOSTNAME_" address="X.X.X.X">
          <test name="all.Interface">
            <arg name="ifname">TenGigabitEthernet4/0/0</arg>
            <arg name="label">Te4/0/0 - QOS</arg>
          </test>

          <test name="cisco_ios.QOS_Interface">
            <arg name="ifname">TenGigabitEthernet4/0/0</arg>
            <arg name="label">Te4/0/0 - QOS</arg>
            <arg name="direction">OUT</arg>
            <arg name="mainClassName">
              <item>mpls-RealTime|RT</item>
              <item>class-default|DE</item>
              <item>mpls-Brocade|BR</item>
              <item>mpls-Bulk|BU</item>
              <item>mpls-BestEffort|BE</item>
            </arg>
          </test>
          <group>/Servers/Linux servers</group>
        </host>

    Classes de Service (avec 2 niveaux de classes)
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    ..  sourcecode:: xml

        <host name="_HOSTNAME_" address="X.X.X.X">
          <attribute name="snmpCommunity">_SNMP_COMMUNITY_</attribute>

          <test name="all.Interface">
            <arg name="ifname">GigabitEthernet0/0</arg>
            <arg name="label">GE0/0</arg>
          </test>

          <test name="cisco_ios.QOS_Interface">
            <arg name="ifname">GigabitEthernet0/0</arg>
            <arg name="label">GE0/0</arg>
            <arg name="direction">OUT</arg>
            <arg name="mainClassName">
              <item>Groupe_1|GR1</item>
              <item>Groupe_2|GR2</item>
              <item>Groupe_3|GR3</item>
            </arg>
            <arg name="subClassName">
              <item>class-default</item>
              <item>telephonie</item>
              <item>Video_Bufferisee</item>
              <item>Video&amp;Donnees_Contraintes</item>
              <item>Services_Reseaux</item>
            </arg>
          </test>
          <group>/Servers/Linux servers</group>
        </host>

    ToIP
    ^^^^

    ..  sourcecode:: xml

        <host name="_HOSTNAME_" address="X.X.X.X">
          <attribute name="telnetLogin">gcharbon</attribute>
          <attribute name="telnetPassword">toor</attribute>
          <attribute name="timeout">10</attribute>
          <attribute name="prompt_timeout">5</attribute>

          <test name="all.Interface">
            <arg name="label">eth0</arg>
            <arg name="ifname">eth0</arg>
          </test>

          <test name="toip.Autocoms">
            <!-- Identifiants des cristaux. -->
            <arg name="crystals">
                <item>42</item>
                <item>47</item>
            </arg>
            <!-- Libellés associés à ces cristaux, dans le même ordre. -->
            <arg name="labels">
                <item>agence_42</item>
                <item>agence_47</item>
            </arg>
          </test>

          <test name="toip.TrunkAverage">
            <!-- Identifiants des cristaux. -->
            <arg name="crystals">
                <item>205</item>
                <item>207</item>
                <item>208</item>
            </arg>
            <!-- Libellés associés à ces cristaux, dans le même ordre. -->
            <arg name="labels">
                <item>agence_205</item>
                <item>agence_207</item>
                <item>agence_208</item>
            </arg>
            <arg name="crit">42</arg>
          </test>

          <test name="toip.TrunkPlatinium">
            <!-- Identifiants des cristaux. -->
            <arg name="crystals">
                <item>27</item>
                <item>28</item>
                <item>29</item>
                <item>31</item>
            </arg>
            <!-- Libellés associés à ces cristaux, dans le même ordre. -->
            <arg name="labels">
                <item>agence_27</item>
                <item>agence_28</item>
                <item>agence_29</item>
                <item>agence_31</item>
            </arg>
            <arg name="crit">42</arg>
          </test>

          <test name="toip.OxeCard">
            <!-- Identifiants des cristaux. -->
            <arg name="crystals">
                <item>42</item>
                <item>47</item>
                <item>49</item>
            </arg>
            <!-- Libellés associés à ces cristaux, dans le même ordre. -->
            <arg name="labels">
                <item>agence_42</item>
                <item>agence_47</item>
                <item>agence_49</item>
            </arg>
          </test>

          <test name="toip.FreePosCard">
            <arg name="hour">15:55:00</arg>
          </test>

          <test name="toip.MevoCapacity">
            <arg name="crit">42</arg>
          </test>

          <test name="toip.TrunkState"/>
          <test name="toip.IpPhones"/>
          <test name="toip.CcdaLicences"/>
          <group>/Servers/Linux servers</group>
        </host>

    Traps SNMP
    ^^^^^^^^^^

    ..  sourcecode:: xml

        <host name="_HOSTNAME_" address="X.X.X.X">
          <!--
            Application d'un test sur l'uptime de l'agent SNMP
            en utilisant l'interrogation SNMP standard (GET).
          -->
          <test name="all.UpTime"/>

          <!--
            Traitement des traps SNMP pour accélérer la détection
            de certains événements impactant l'état de l'agent SNMP.
            Note : le service qui sera mis à jour est celui correspondant
                   au test "UpTime" déclaré ci-dessus.
          -->
          <test name="all.Trap">
            <arg name="trap">warmStart</arg>
            <arg name="state">WARNING</arg>
            <arg name="service">UpTime</arg>
            <arg name="message">La configuration de l'agent a été rechargée</arg>
          </test>

          <test name="all.Trap">
            <arg name="trap">coldStart</arg>
            <arg name="state">CRITICAL</arg>
            <arg name="service">UpTime</arg>
            <arg name="message">L'agent SNMP a redémarré</arg>
          </test>

          <!--
            Les exemples qui suivent sont plus complets et montrent comment
            utiliser des conditions et inclure des variables du trap SNMP
            dans le message.
          -->
          <test name="all.Trap">
            <arg name="trap">EXAMPLE-MIB::exampleTrap</arg>
            <arg name="state">OK</arg>
            <arg name="service">exampleTrap</arg>
            <arg name="message">Un trap d'exemple a été reçu avec la priorité {var:EXAMPLE-MIB::priority}</arg>
            <arg name="conditions">
                <item><![CDATA[EXAMPLE-MIB::priority >= 0]]></item>
                <item><![CDATA[EXAMPLE-MIB::priority < 50]]></item>
            </arg>
          </test>

          <test name="all.Trap">
            <arg name="trap">EXAMPLE-MIB::exampleTrap</arg>
            <arg name="state">WARNING</arg>
            <arg name="service">exampleTrap</arg>
            <arg name="message">Un trap d'exemple a été reçu avec la priorité {var:EXAMPLE-MIB::priority}</arg>
            <arg name="conditions">
                <item><![CDATA[EXAMPLE-MIB::priority >= 50]]></item>
                <item><![CDATA[EXAMPLE-MIB::priority < 100]]></item>
            </arg>
          </test>

          <test name="all.Trap">
            <arg name="trap">EXAMPLE-MIB::exampleTrap</arg>
            <arg name="state">CRITICAL</arg>
            <arg name="service">exampleTrap</arg>
            <arg name="message">Un trap d'exemple a été reçu avec la priorité {var:EXAMPLE-MIB::priority}</arg>
            <arg name="conditions">
                <item><![CDATA[EXAMPLE-MIB::priority >= 100]]></item>
            </arg>
          </test>
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
