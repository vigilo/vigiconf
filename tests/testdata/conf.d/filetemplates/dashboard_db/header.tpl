-- confid:%(confid)s

USE dashboard

DROP TABLE IF EXISTS `tags`;
CREATE TABLE IF NOT EXISTS `tags` (
  `host` varchar(255) NOT NULL,
  `service` varchar(255) NOT NULL default '',
  `tag` varchar(255) NOT NULL,
  `value` varchar(255) NOT NULL,
  PRIMARY KEY  (`host`,`service`,`tag`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

